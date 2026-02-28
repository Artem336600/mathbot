"""Admin menu handler — entry point for admins."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.config import settings
from bot.keyboards.admin_kb import admin_menu_keyboard
from bot.utils import safe_edit_text

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
        reply_markup=admin_menu_keyboard(settings.webapp_url),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    await safe_edit_text(callback.message, 
        "🔧 <b>Админ-панель MathTrainer</b>\n\nВыберите действие:",
        reply_markup=admin_menu_keyboard(settings.webapp_url),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery, db):
    uid = callback.from_user.id
    if not is_admin(uid):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    from repositories.user_repo import UserRepository
    # For MVP we can use get_all_ids, though a proper count() method is better
    active_user_ids = await UserRepository.get_all_ids(db)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])

    await safe_edit_text(callback.message, 
        f"👥 <b>Статистика пользователей</b>\n\n"
        f"🌟 Активных пользователей: <b>{len(active_user_ids)}</b>\n\n"
        f"<i>(Детальная аналитика в разработке)</i>",
        reply_markup=back_kb,
        parse_mode="HTML",
    )
    await callback.answer()
