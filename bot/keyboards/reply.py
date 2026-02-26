"""Reply Keyboard — always-visible bottom menu."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Меню"), KeyboardButton(text="👤 Профиль")]
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
