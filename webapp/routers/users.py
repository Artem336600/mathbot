"""Users API for Admin Dashboard (US-010)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot

from webapp.auth import get_admin_user, get_db_session
from db.models import User
from webapp.schemas import UserResponse, UserSendMessage
from repositories.user_repo import UserRepository
from bot.config import settings
from loguru import logger

router = APIRouter(prefix="/api/users", tags=["users"])

# We initialize a bot instance for sending messages. 
# Alternatively, we could share the instance from bot/main.py, but Aiogram allows multiple Bot instances with the same token.
admin_bot = Bot(token=settings.bot_token)

@router.get("/", response_model=List[UserResponse])
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    users = await UserRepository.get_paginated(page, limit, search, db)
    
    # Converting datetime to string for response
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "username": u.username,
            "first_name": u.first_name,
            "xp": u.xp,
            "level": str(u.level),
            "streak_days": u.streak_days,
            "accuracy_rate": u.accuracy_rate,
            "is_banned": u.is_banned,
            "created_at": u.created_at.isoformat() if u.created_at else ""
        })
    return result

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    u = await UserRepository.get(user_id, db)
    if not u:
        raise HTTPException(404, "User not found")
        
    return dict(
        id=u.id,
        username=u.username,
        first_name=u.first_name,
        xp=u.xp,
        level=str(u.level),
        streak_days=u.streak_days,
        accuracy_rate=u.accuracy_rate,
        is_banned=u.is_banned,
        created_at=u.created_at.isoformat() if u.created_at else ""
    )

@router.post("/{user_id}/ban")
async def ban_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    if user_id in settings.admin_ids:
        raise HTTPException(status_code=400, detail="Cannot ban an admin")
        
    success = await UserRepository.set_banned(user_id, True, db)
    if not success:
        raise HTTPException(404, "User not found")
        
    logger.info(f"[WEBAPP:USERS] Admin {admin.id} banned user {user_id}")
    return {"status": "ok", "is_banned": True}

@router.post("/{user_id}/unban")
async def unban_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    success = await UserRepository.set_banned(user_id, False, db)
    if not success:
        raise HTTPException(404, "User not found")
        
    logger.info(f"[WEBAPP:USERS] Admin {admin.id} unbanned user {user_id}")
    return {"status": "ok", "is_banned": False}

@router.post("/{user_id}/message")
async def send_message_to_user(
    user_id: int,
    payload: UserSendMessage,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Send a direct message from the bot to a user."""
    u = await UserRepository.get(user_id, db)
    if not u:
        raise HTTPException(404, "User not found")
        
    try:
        await admin_bot.send_message(
            chat_id=user_id, 
            text=f"✉️ <b>Сообщение от администрации:</b>\n\n{payload.text}",
            parse_mode="HTML"
        )
        logger.info(f"[WEBAPP:USERS] Admin {admin.id} sent message to user {user_id}")
        return {"status": "ok", "message": "Sent"}
    except Exception as e:
        logger.error(f"[WEBAPP:USERS] Failed to send message to user {user_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to send: {e}")
