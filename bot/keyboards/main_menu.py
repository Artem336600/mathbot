"""Inline main menu keyboard."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard(is_admin: bool = False, webapp_url: str = "") -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🚀 Спринт", callback_data="sprint_start"),
            InlineKeyboardButton(text="🏋️ Тренировка", callback_data="training_start"),
        ],
        [
            InlineKeyboardButton(text="📚 Темы", callback_data="topics_list"),
            InlineKeyboardButton(text="❌ Мои ошибки", callback_data="mistakes_menu"),
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
        ],
    ]
    if is_admin:
        from aiogram.types import WebAppInfo
        rows.append([
            InlineKeyboardButton(text="📱 Админ-панель", web_app=WebAppInfo(url=webapp_url)),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
