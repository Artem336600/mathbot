"""Main FastAPI application for Admin Mini App."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from webapp.routers import stats, topics, questions, users, broadcast

app = FastAPI(
    title="MathTrainer Admin WebApp API",
    description="Internal API for Telegram Mini App admin panel",
    version="1.0.0",
    docs_url=None, # disable public docs
    redoc_url=None,
)

# Allow CORS since Telegram WebApp runs in an iframe
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to Telegram Web App origins or your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
app.include_router(stats.router)
app.include_router(topics.router)
app.include_router(questions.router)
app.include_router(users.router)
app.include_router(broadcast.router)
