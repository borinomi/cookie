import asyncio
import os
import socket
import subprocess
from datetime import datetime
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

@app.post("/get-cookies")
async def get_cookies(request: CookieRequest):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://{CDP_HOST}:{CDP_PORT}")
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto(str(request.url))
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(2)
        
        cookies = await context.cookies(str(request.url))
        cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)