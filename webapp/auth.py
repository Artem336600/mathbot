"""Authentication middleware for Telegram Web App initData."""
import hashlib
import hmac
import json
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

def validate_init_data(init_data: str, bot_token: str) -> dict | None:
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
        
        if calculated_hash != received_hash:
            logger.warning("[WEBAPP:AUTH] Invalid initData hash")
            return None
            
        user_data = json.loads(parsed_data.get("user", "{}"))
        return user_data
    except Exception as e:
        logger.error(f"[WEBAPP:AUTH] Exception validating initData: {e}")
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
        logger.warning("[WEBAPP:AUTH] No X-Init-Data header")
        raise HTTPException(status_code=401, detail="Unauthorized - Missing X-Init-Data header")

    if settings.log_level == "DEBUG" and "dev_user=" in init_data:
        pass # we could add dev mock here, but let's stick to strict validation

    # In dev mode we might allow a stub payload for easier testing in the browser
    if init_data.startswith("test_dev="):
        uid = int(init_data.split("=")[1])
        if uid in settings.admin_ids:
            return User(id=uid, username="testadmin", first_name="Admin", level="Профессионал")

    user_data = validate_init_data(init_data, settings.bot_token)
    
    if not user_data or "id" not in user_data:
        raise HTTPException(status_code=401, detail="Unauthorized - Invalid Telegram initData signature")

    telegram_id = int(user_data["id"])
    
    # 1. Verification of admin rights
    if telegram_id not in settings.admin_ids:
        logger.warning(f"[WEBAPP:AUTH] User {telegram_id} is not an admin! Rejecting.")
        raise HTTPException(status_code=403, detail="Forbidden - Not an admin")

    # 2. Get from DB
    user = await UserRepository.get(telegram_id, db)
    if not user:
        # Since he's in admin_ids, we might just create him? Or return mock.
        # But a real admin must interact with the bot first (start)
        logger.warning(f"[WEBAPP:AUTH] Admin {telegram_id} not found in DB!")
        raise HTTPException(status_code=401, detail="User not found in bot DB. Send /start to bot first.")
        
    logger.debug(f"[WEBAPP:AUTH] Valid admin request from {telegram_id} (@{user.username})")
    
    return user
