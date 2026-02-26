"""Admin menu handler — entry point for admins."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.config import settings
from bot.keyboards.admin_kb import admin_menu_keyboard

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("admin"))
async def cmd_admin(message: Message, user):
    uid = message.from_user.id
    if not is_admin(uid):
        logger.warning(f"[HANDLER:admin] Non-admin {uid} tried /admin")
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return

    logger.info(f"[HANDLER:admin] Admin {uid} opened panel")
    await message.answer(
        "🔧 <b>Админ-панель MathTrainer</b>\n\nВыберите действие:",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    await callback.message.edit_text(
        "🔧 <b>Админ-панель MathTrainer</b>\n\nВыберите действие:",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()
