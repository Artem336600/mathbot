"""
Stats service — XP, levels, streak, accuracy.
No Aiogram imports. Pure business logic.
"""
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_repo import UserRepository
from repositories.progress_repo import ProgressRepository

XP_CORRECT = 10
XP_FIX_MISTAKE = 5
XP_SPRINT_BONUS = 50

LEVELS = [
    (0, "Новичок"),
    (100, "Ученик"),
    (300, "Практик"),
    (600, "Профессионал"),
]


def _calc_level(xp: int) -> str:
    level = "Новичок"
    for threshold, name in LEVELS:
        if xp >= threshold:
            level = name
    return level


def _xp_to_next_level(xp: int) -> tuple[str, int, int]:
    """Returns (next_level_name, current_xp_in_level, needed_xp_in_level)."""
    thresholds = [(t, n) for t, n in LEVELS]
    for i, (threshold, name) in enumerate(thresholds):
        if i + 1 < len(thresholds):
            next_threshold, next_name = thresholds[i + 1]
            if xp < next_threshold:
                return next_name, xp - threshold, next_threshold - threshold
    return "Профессионал", xp - 600, 1  # max level


async def award_xp(user_id: int, amount: int, db: AsyncSession) -> dict:
    """Award XP, recalculate level. Returns info dict."""
    user = await UserRepository.get(user_id, db)
    if not user:
        return {}

    old_level = user.level
    user.xp += amount
    new_level = _calc_level(user.xp)
    level_up = new_level != old_level
    user.level = new_level

    await UserRepository.update(user, db)
    logger.info(
        f"[SVC:Stats] User {user_id} +{amount}XP → total={user.xp}, level={new_level}"
        + (" 🎉 LEVEL UP!" if level_up else "")
    )
    return {"xp": user.xp, "level": user.level, "level_up": level_up}


async def update_streak(user_id: int, db: AsyncSession) -> int:
    """Update daily streak. Returns current streak."""
    user = await UserRepository.get(user_id, db)
    if not user:
        return 0

    now = datetime.now(timezone.utc)
    if user.last_active:
        delta = (now.date() - user.last_active.date()).days
        if delta == 1:
            user.streak_days += 1
        elif delta > 1:
            user.streak_days = 1
        # delta == 0 → same day, no change
    else:
        user.streak_days = 1

    user.last_active = now
    await UserRepository.update(user, db)
    logger.debug(f"[SVC:Stats] User {user_id} streak={user.streak_days}")
    return user.streak_days


async def update_accuracy(user_id: int, db: AsyncSession) -> float:
    """Recalculate and save accuracy from progress history."""
    accuracy = await ProgressRepository.get_accuracy(user_id, db)
    user = await UserRepository.get(user_id, db)
    if user:
        user.accuracy_rate = accuracy
        await UserRepository.update(user, db)
    logger.debug(f"[SVC:Stats] User {user_id} accuracy={accuracy:.2%}")
    return accuracy


def get_xp_bar(xp: int, bar_length: int = 10) -> str:
    """Returns visual XP progress bar like: ████████░░"""
    if xp >= 600:
        return "█" * bar_length
    _, current, needed = _xp_to_next_level(xp)
    filled = min(int(bar_length * current / max(needed, 1)), bar_length)
    return "█" * filled + "░" * (bar_length - filled)


def get_xp_progress_text(xp: int) -> str:
    """Returns text like: 'XP: 150 / 300 до Практика'"""
    _, current, needed = _xp_to_next_level(xp)
    next_level, _, _ = _xp_to_next_level(xp)
    if next_level == "Профессионал" and xp >= 600:
        return f"XP: {xp} (максимальный уровень)"
    return f"XP: {xp} / {xp - current + needed} до {next_level}"
