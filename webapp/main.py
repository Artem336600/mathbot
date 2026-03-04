"""Main FastAPI application for Admin Mini App."""
import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from loguru import logger

from webapp.routers import stats, topics, questions, users, broadcast, attachments
from bot.config import settings

app = FastAPI(
    title="MathTrainer Admin WebApp API",
    description="Internal API for Telegram Mini App admin panel",
    version="1.0.0",
    docs_url=None, # disable public docs
    redoc_url=None,
)

# Allow CORS only for configured trusted origins.
cors_origins = settings.webapp_allowed_origins
if not cors_origins:
    logger.warning("[WEBAPP] CORS allowlist is empty. Cross-origin browser requests will be denied.")
if "*" in cors_origins:
    logger.warning("[WEBAPP] Wildcard CORS origin is insecure and should not be used in production.")
logger.info(f"[WEBAPP] Auth mode={settings.webapp_auth_mode}")
if settings.webapp_auth_mode != "telegram_strict":
    logger.warning(f"[WEBAPP] Insecure auth mode enabled: {settings.webapp_auth_mode}")
logger.info(f"[WEBAPP] CORS origins configured={len(cors_origins)}")
logger.info("[WEBAPP] Security header profile=strict")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials="*" not in cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InMemoryRateLimiter:
    def __init__(self):
        self._state: dict[str, tuple[int, float]] = {}

    def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        count, window_start = self._state.get(key, (0, now))
        if now - window_start >= window_seconds:
            count = 0
            window_start = now
        count += 1
        self._state[key] = (count, window_start)
        return count <= limit


rate_limiter = InMemoryRateLimiter()


@app.middleware("http")
async def add_security_headers(request, call_next):
    if request.url.path.startswith("/api/") and request.method in {"POST", "PUT", "PATCH"}:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > settings.webapp_max_request_bytes and "/upload" not in request.url.path:
                    logger.warning(
                        f"[WEBAPP] request_blocked reason=payload_too_large path={request.url.path} size={size}"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Payload too large"},
                    )
            except ValueError:
                logger.warning(f"[WEBAPP] invalid content-length header path={request.url.path}")

    if request.url.path.startswith("/api/"):
        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        method = request.method
        is_sensitive = (
            (method == "POST" and path == "/api/broadcast/send")
            or (method == "POST" and path == "/api/questions/import")
            or (method == "POST" and path.startswith("/api/attachments/"))
            or (method == "POST" and (path.endswith("/ban") or path.endswith("/unban")))
        )
        if is_sensitive:
            limit_key = f"{ip}:{method}:{path}"
            allowed = rate_limiter.hit(
                limit_key,
                settings.webapp_rate_limit_sensitive_per_window,
                settings.webapp_rate_limit_window_seconds,
            )
            if not allowed:
                logger.warning(
                    f"[WEBAPP] request_blocked reason=rate_limited path={path} ip={ip} "
                    f"window={settings.webapp_rate_limit_window_seconds}s limit={settings.webapp_rate_limit_sensitive_per_window}"
                )
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"},
                )

    response = await call_next(request)
    response.headers["Content-Security-Policy"] = settings.webapp_csp
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if settings.webapp_enable_hsts:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Custom logging middleware (optional, for debugging)
@app.middleware("http")
async def log_requests(request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/static/"):
        logger.debug(f"[WEBAPP] {request.method} {request.url.path} -> {response.status_code}")
    return response

# Mount static files
# Mount static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    # Only mount if exists to avoid startup crash before we create it in Phase 2
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
app.include_router(stats.router)
app.include_router(topics.router)
app.include_router(questions.router)
app.include_router(users.router)
app.include_router(broadcast.router)
app.include_router(attachments.router)
