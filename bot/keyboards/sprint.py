"""Sprint keyboards. callback_data sizes kept within 64 bytes."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def sprint_intro_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="▶️ Поехали!", callback_data="sprint_go"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu"),
        ]
    ])


def answer_keyboard(options: dict) -> InlineKeyboardMarkup:
    """
    options = {"a": text, "b": text, "c": text, "d": text}
    Callbacks: sprint_ans:a / sprint_ans:b / sprint_ans:c / sprint_ans:d (~13 bytes each)
    question_id is stored in Redis session — NOT passed in callback.
    """
    labels = {"a": "A", "b": "B", "c": "C", "d": "D"}
    buttons = [
        InlineKeyboardButton(
            text=f"{labels[k]}: {v[:30]}",
            callback_data=f"sprint_ans:{k}",
        )
        for k, v in options.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [buttons[0], buttons[1]],
        [buttons[2], buttons[3]],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="sprint_menu")],
    ])


def sprint_result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu"),
            InlineKeyboardButton(text="🔄 Ещё раз", callback_data="sprint_start"),
        ]
    ])
