"""Mistakes keyboards. Callbacks within 64 bytes."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.models import Topic


def mistakes_menu_keyboard(
    has_mistakes: bool, topics_with_mistakes: list[Topic]
) -> InlineKeyboardMarkup:
    rows = []
    if has_mistakes:
        rows.append([
            InlineKeyboardButton(text="🎲 Все подряд", callback_data="mis_all"),
        ])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mistake_answer_keyboard(options: dict) -> InlineKeyboardMarkup:
    """
    Answer buttons. Callbacks: mis_ans:a/b/c/d (~10 bytes)
    mistake_id + question_id stored in Redis mistakes_session:{user_id}
    """
    labels = {"a": "A", "b": "B", "c": "C", "d": "D"}
    buttons = [
        InlineKeyboardButton(
            text=f"{labels[k]}: {v[:30]}",
            callback_data=f"mis_ans:{k}",
        )
        for k, v in options.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [buttons[0], buttons[1]],
        [buttons[2], buttons[3]],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="mistakes_menu")],
    ])


def mistakes_empty_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")]
    ])
