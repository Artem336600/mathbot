"""Authentication middleware for Telegram Web App initData."""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from db.models import User
from db.session import async_session_factory
from repositories.user_repo import UserRepository

init_data_header = APIKeyHeader(name="X-Init-Data", auto_error=False)

def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int = 600) -> dict | None:
    """Validate Telegram WebApp initData string."""
    try:
        parsed_data = dict(parse_qsl(init_data))
        if "hash" not in parsed_data:
            return None
            
        received_hash = parsed_data.pop("hash")
        
        # Sort keys alphabetically
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )
        
        # Secret key computation
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        
        # Calculated hash
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(calculated_hash, received_hash):
            logger.warning("[WEBAPP:AUTH] reject reason=bad_signature")
            return None

        auth_date_raw = parsed_data.get("auth_date")
        if not auth_date_raw:
            logger.warning("[WEBAPP:AUTH] reject reason=missing_auth_date")
            return None
        try:
            auth_date = int(auth_date_raw)
        except ValueError:
            logger.warning("[WEBAPP:AUTH] reject reason=invalid_auth_date")
            return None

        now = int(time.time())
        if auth_date > now + 30:
            logger.warning("[WEBAPP:AUTH] reject reason=future_auth_date")
            return None
        if now - auth_date > max_age_seconds:
            logger.warning("[WEBAPP:AUTH] reject reason=expired_auth")
            return None
            
        user_data = json.loads(parsed_data.get("user", "{}"))
        return user_data
    except Exception:
        logger.exception("[WEBAPP:AUTH] exception during initData validation")
        return None

async def get_db_session():
    async with async_session_factory() as session:
        yield session

async def get_admin_user(
    init_data: str = Security(init_data_header),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """FastAPI Dependency to get current admin user from Telegram initData."""
    if not init_data:
        # Check if auth bypass is allowed for tests/local dev (remove in real prod)
        logger.warning("[WEBAPP:AUTH] reject reason=missing_header")
        raise HTTPException(status_code=401, detail="Unauthorized - Missing X-Init-Data header")

    telegram_id = None
    user = None

    if settings.webapp_auth_mode == "test_bypass" and init_data.startswith("test_dev="):
        try:
            telegram_id = int(init_data.split("=")[1])
        except (ValueError, IndexError):
            logger.warning("[WEBAPP:AUTH] reject reason=invalid_test_bypass")
            raise HTTPException(status_code=401, detail="Unauthorized - Invalid test bypass header")
    else:
        user_data = validate_init_data(
            init_data,
            settings.bot_token,
            max_age_seconds=settings.webapp_init_data_ttl_seconds,
        )
        if not user_data or "id" not in user_data:
            raise HTTPException(status_code=401, detail="Unauthorized - Invalid Telegram initData signature")
        telegram_id = int(user_data["id"])
    
    # 1. Verification of admin rights
    if telegram_id not in settings.admin_ids:
        logger.warning(f"[WEBAPP:AUTH] reject reason=not_admin user_id={telegram_id}")
        raise HTTPException(status_code=403, detail="Forbidden - Not an admin")

    # 2. Get from DB
    user = await UserRepository.get(telegram_id, db)
    if not user:
        # Since he's in admin_ids, we might just create him? Or return mock.
        # But a real admin must interact with the bot first (start)
        logger.warning(f"[WEBAPP:AUTH] reject reason=missing_user_in_db user_id={telegram_id}")
        raise HTTPException(status_code=401, detail="User not found in bot DB. Send /start to bot first.")
        
    if user.is_banned:
        logger.warning(f"[WEBAPP:AUTH] reject reason=banned user_id={telegram_id}")
        raise HTTPException(status_code=403, detail="Forbidden - Your account is banned")

    logger.debug(f"[WEBAPP:AUTH] Valid admin request from {telegram_id} (@{user.username})")
    
    return user
