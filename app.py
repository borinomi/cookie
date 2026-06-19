import asyncio
import os
import socket
import subprocess
from datetime import datetime
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
import uvicorn
from playwright.async_api import async_playwright


app = FastAPI()

CDP_PORT = 9222
CDP_HOST = os.getenv("CDP_HOST", socket.gethostbyname("host.docker.internal"))

class CookieRequest(BaseModel):
    url: HttpUrl

class CookieResponse(BaseModel):
    cookie_header: str

class CurlRequest(BaseModel):
    command: str

class HtmlResponse(BaseModel):
    data: str

class SimpleCookieRequest(BaseModel):
    domain: str
    cookies: dict
    goto_url: Optional[str] = None
    clear_first: bool = True

@app.post("/get-html")
async def get_html(request: CookieRequest):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
        context = browser.contexts[0]
        page = await context.new_page()
        
        await page.goto(str(request.url))
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(2)
        
        html = await page.content()
        
        await page.close()
        return HtmlResponse(data=html)

@app.post("/get-shot")
async def get_screenshot(request: CookieRequest):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
        context = browser.contexts[0]
        page = await context.new_page()
        
        await page.goto(str(request.url))
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(5)
        
        screenshot = await page.screenshot(full_page=True)
        
        await page.close()
        
        import base64
        return {"data": base64.b64encode(screenshot).decode('utf-8')}

@app.post("/get-cookies")
async def get_cookies(request: CookieRequest):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
        context = browser.contexts[0]
        page = await context.new_page()
        
        await page.goto(str(request.url))
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(2)
        
        cookies = await context.cookies(str(request.url))
        cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        
        await page.close()
        return CookieResponse(cookie_header=cookie_header)

@app.post("/curl")
async def execute_curl(request: CurlRequest):
    try:
        result = subprocess.run(
            request.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8'
        )
        
        return {
            "success": True,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat()
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timeout (60s)",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/inject-cookies")
async def inject_cookies(request: SimpleCookieRequest):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
        context = browser.contexts[0]

        if request.clear_first:
            await context.clear_cookies(domain=request.domain)

        cookie_list = [
            {
                "name": name,
                "value": value,
                "domain": request.domain,
                "path": "/",
                "secure": True,
                "httpOnly": True,
                "sameSite": "None",
            }
            for name, value in request.cookies.items()
        ]
        await context.add_cookies(cookie_list)

        result = {"success": True, "injected": len(cookie_list)}

        if request.goto_url:
            page = await context.new_page()
            await page.goto(request.goto_url)
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(2)
            result["url"] = page.url
            await page.close()

        result["timestamp"] = datetime.now().isoformat()
        return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
