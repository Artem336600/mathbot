"""Broadcast API for Admin Dashboard (US-011)."""
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
import redis.asyncio as aioredis

from webapp.auth import get_admin_user, get_db_session
from db.models import User
from db.session import async_session_factory
from webapp.schemas import BroadcastRequest, BroadcastResponse
from services.broadcast_service import send_to_all
from bot.config import settings
from loguru import logger

router = APIRouter(prefix="/api/broadcast", tags=["broadcast"])

# Common bot instance for webapp
admin_bot = Bot(token=settings.bot_token)


async def get_redis():
    r = aioredis.from_url(settings.redis_url)
    try:
        yield r
    finally:
        await r.aclose()


@router.post("/preview")
async def broadcast_preview(
    payload: BroadcastRequest,
    admin: User = Depends(get_admin_user)
):
    """Return preview of the broadcast HTML text."""
    # We could theoretically render it or just validate the HTML format here using Aiogram's parse_mode
    # For now, just echo it back. The frontend will do the visual rendering.
    return {"html": payload.text}


@router.get("/status", response_model=BroadcastResponse)
async def get_broadcast_status(
    admin: User = Depends(get_admin_user),
    redis_client: aioredis.Redis = Depends(get_redis)
):
    """Get status of the current or last broadcast."""
    raw = await redis_client.get("broadcast:status")
    if not raw:
        return {"status": "idle", "sent": 0, "failed": 0, "total": 0}
        
    data = json.loads(raw)
    return {
        "status": data.get("status", "unknown"),
        "sent": data.get("sent", 0),
        "failed": data.get("failed", 0),
        "total": data.get("total", 0)
    }

async def run_broadcast_background(text: str, admin_id: int):
    """Run broadcast in background task, needs its own fresh DB session."""
    logger.info(f"[WEBAPP:BROADCAST] Starting background task for admin {admin_id}")
    async with async_session_factory() as db:
        r = aioredis.from_url(settings.redis_url)
        try:
            await send_to_all(text, admin_bot, db, redis_client=r)
        except Exception as e:
            logger.error(f"[WEBAPP:BROADCAST] Task failed: {e}")
            await r.set("broadcast:status", json.dumps({"status": "error"}))
        finally:
            await r.aclose()


@router.post("/send")
async def send_broadcast(
    payload: BroadcastRequest,
    background_tasks: BackgroundTasks,
    admin: User = Depends(get_admin_user),
    redis_client: aioredis.Redis = Depends(get_redis)
):
    """Start broadcast asynchronously."""
    # Check if one is already running
    raw = await redis_client.get("broadcast:status")
    if raw:
        data = json.loads(raw)
        if data.get("status") == "in_progress":
            raise HTTPException(400, "A broadcast is already running.")
            
    background_tasks.add_task(run_broadcast_background, payload.text, admin.id)
    return {"status": "started"}
