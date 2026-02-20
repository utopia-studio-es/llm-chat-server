"""Auth: login JWT, proteccion rutas, proxy a vLLM."""
import os
import time
import logging
from pathlib import Path

# Cargar .env
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
import bcrypt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
import json

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
VLLM_URL = os.environ.get("VLLM_URL", "http://127.0.0.1:8000")
API_KEY = os.environ.get("API_KEY", "token-llm-chat-secret-2025")
JWT_SECRET = os.environ.get("JWT_SECRET", API_KEY)
JWT_EXPIRE_SECONDS = int(os.environ.get("JWT_EXPIRE_SECONDS", "86400"))
COOKIE_NAME = "access_token"
SECURE_COOKIE = os.environ.get("SECURE_COOKIE", "true").lower() in ("1", "true", "yes")
LOGIN_USER = os.environ.get("LOGIN_USER", "admin")
LOGIN_PASSWORD_PLAIN = os.environ.get("LOGIN_PASSWORD", "")
_stored_hash = bcrypt.hashpw(LOGIN_PASSWORD_PLAIN.encode("utf-8"), bcrypt.gensalt()).decode("utf-8") if LOGIN_PASSWORD_PLAIN else None

def check_user(user: str, password: str) -> bool:
    if user != LOGIN_USER:
        return False
    if not _stored_hash:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), _stored_hash.encode("utf-8"))

def create_token(username: str) -> str:
    payload = {"sub": username, "exp": time.time() + JWT_EXPIRE_SECONDS}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except JWTError:
        return None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth")

limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.post("/api/login")
@limiter.limit("5/minute")
async def login(request: Request):
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    username = body.get("username", "")
    password = body.get("password", "")
    if not check_user(username, password):
        raise HTTPException(401, "Invalid credentials")
    token = create_token(username)
    resp = Response(content=json.dumps({"message": "Login successful"}), media_type="application/json")
    resp.set_cookie(key=COOKIE_NAME, value=token, httponly=True, secure=SECURE_COOKIE, samesite="lax")
    return resp

@app.get("/api/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp

@app.get("/")
@app.get("/login")
async def login_page():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/chat")
async def chat_redirect(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token or not decode_token(token):
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse(FRONTEND_DIR / "chat.html")

@app.get("/chat.html")
async def chat_page(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token or not decode_token(token):
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse(FRONTEND_DIR / "chat.html")

async def handle_chat_with_smart_tools(body_json: dict, headers: dict, url: str, is_stream: bool):
    """Maneja chat con herramientas inteligentes."""
    from auth.smart_tools import detect_and_execute_smart_tools, augment_message_with_tool_result
    
    messages = body_json.get("messages", [])
    user_message = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        user_message = item.get("text", "")
                        break
            else:
                user_message = content
            break
    
    if user_message:
        tool_result = await detect_and_execute_smart_tools(user_message)
        if tool_result:
            tool_name, result = tool_result
            logger.info(f"🔧 Herramienta ejecutada: {tool_name}")
            messages = augment_message_with_tool_result(messages, tool_name, result)
            body_json["messages"] = messages
    
    if is_stream:
        async def stream_proxy():
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("POST", url, json=body_json, headers=headers) as r:
                    async for chunk in r.aiter_bytes():
                        yield chunk
        return StreamingResponse(stream_proxy(), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(url, json=body_json, headers=headers)
        return Response(content=r.content, status_code=r.status_code, headers=dict(r.headers))

@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_v1(request: Request, path: str):
    token = request.cookies.get(COOKIE_NAME)
    if not token or not decode_token(token):
        raise HTTPException(401, "No autorizado")
    
    url = f"{VLLM_URL}/v1/{path}"
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "connection", "content-length")}
    headers["Authorization"] = f"Bearer {API_KEY}"
    
    try:
        body_json = json.loads(body) if body else {}
        is_stream = body_json.get("stream", False)
        is_chat = path == "chat/completions" and request.method == "POST"
    except:
        body_json = {}
        is_stream = False
        is_chat = False
    
    if is_chat:
        return await handle_chat_with_smart_tools(body_json, headers, url, is_stream)
    
    if is_stream:
        async def stream_proxy():
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(request.method, url, content=body, headers=headers) as r:
                    async for chunk in r.aiter_bytes():
                        yield chunk
        return StreamingResponse(stream_proxy(), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.request(request.method, url, content=body, headers=headers)
        return Response(content=r.content, status_code=r.status_code, headers=dict(r.headers))
