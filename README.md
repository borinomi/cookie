# Cookie Extractor API

웹사이트에 접속하여 쿠키를 추출하는 FastAPI 서비스입니다.

## 로컬 개발 환경 설정

1. uv 설치 (아직 설치하지 않은 경우):
   curl -LsSf https://astral.sh/uv/install.sh | sh

2. 가상환경 생성 및 의존성 설치:
   uv sync

3. Playwright 브라우저 설치:
   uv run playwright install chromium

4. 서버 실행:
   uv run python app.py

   또는

   uv run uvicorn app:app --host 0.0.0.0 --port 8002

## Docker로 실행

1. Docker Compose로 실행:
   docker compose up -d

2. 서버는 포트 8002에서 실행됩니다.

## API 엔드포인트

### POST /get-cookies

웹사이트의 쿠키를 추출합니다. CDP를 통해 원격 브라우저에 연결하여 쿠키를 가져옵니다.

요청 예시:
{
  "url": "https://example.com"
}

응답 예시:
{
  "cookie_header": "session_id=abc123; user_token=xyz789"
}

### POST /curl

curl 명령을 실행합니다.

요청 예시:
{
  "command": "curl -X GET https://example.com"
}

응답 예시:
{
  "success": true,
  "return_code": 0,
  "stdout": "응답 내용",
  "stderr": "",
  "timestamp": "2024-10-20T10:30:00"
}

## API 문서

서버 실행 후 다음 URL에서 Swagger UI를 통해 API를 테스트할 수 있습니다:
- 로컬: http://localhost:8002/docs
- Docker: http://localhost:8002/docs

## 환경변수 (선택사항)

CDP_HOST를 변경하려면 .env 파일을 생성하거나 환경변수로 설정할 수 있습니다:

CDP_HOST=localhost

기본값:
- CDP_HOST: host.docker.internal의 IP 주소
- CDP_PORT: 9222

Docker 환경에서는 CDP를 통해 원격 브라우저에 연결합니다.