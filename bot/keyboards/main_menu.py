"""Inline main menu keyboard."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
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
    ])
