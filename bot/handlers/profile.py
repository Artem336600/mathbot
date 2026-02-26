"""
Profile handler — US-007.
Shows XP bar, level, accuracy, streak, total solved.
"""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.keyboards.profile_kb import profile_keyboard
from repositories.progress_repo import ProgressRepository
from services.stats_service import LEVELS, get_xp_bar, get_xp_progress_text

router = Router()


def _build_profile_text(user, total_solved: int) -> str:
    level = user.level
    xp = user.xp
    accuracy = round(user.accuracy_rate * 100, 1)
    streak = user.streak_days
    xp_bar = get_xp_bar(xp)
    xp_progress = get_xp_progress_text(xp)

    return (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"🏅 Уровень: <b>{level}</b>\n"
        f"⭐ {xp_progress}\n"
        f"{xp_bar}\n\n"
        f"✅ Задач выполнено: <b>{total_solved}</b>\n"
        f"🎯 Точность: <b>{accuracy}%</b>\n"
        f"🔥 Серия: <b>{streak} дн.</b>\n"
        f"💎 Статус: <b>FREE</b>"
    )


async def _show_profile(event, user, db) -> None:
    uid = user.id
    total_solved = await ProgressRepository.get_total_count(uid, db)
    logger.info(f"[HANDLER:profile] User {uid} opened profile. xp={user.xp}, level={user.level}")

    text = _build_profile_text(user, total_solved)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=profile_keyboard(), parse_mode="HTML")
        await event.answer()
    elif isinstance(event, Message):
        await event.answer(text, reply_markup=profile_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "profile")
async def callback_profile(callback: CallbackQuery, db, user):
    await _show_profile(callback, user, db)


@router.message(F.text == "👤 Профиль")
async def message_profile(message: Message, db, user):
    await _show_profile(message, user, db)
