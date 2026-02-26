"""Training keyboards. Callbacks kept within 64 bytes."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.models import Topic


def training_setup_keyboard(topics: list[Topic], selected_ids: list[int]) -> InlineKeyboardMarkup:
    """Topic selection with checkboxes. toggle callback: training_toggle:{id}"""
    rows = []
    for topic in topics:
        is_selected = topic.id in selected_ids
        mark = "✅" if is_selected else "☐"
        rows.append([
            InlineKeyboardButton(
                text=f"{mark} {topic.title}",
                callback_data=f"train_tog:{topic.id}",
            )
        ])

    rows.append([
        InlineKeyboardButton(text="▶️ Начать", callback_data="training_begin"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def training_answer_keyboard(options: dict) -> InlineKeyboardMarkup:
    """
    Answer buttons for training mode.
    Callbacks: train_ans:a / train_ans:b / train_ans:c / train_ans:d (~13 bytes)
    current_question_id is stored in Redis session.
    """
    labels = {"a": "A", "b": "B", "c": "C", "d": "D"}
    buttons = [
        InlineKeyboardButton(
            text=f"{labels[k]}: {v[:30]}",
            callback_data=f"train_ans:{k}",
        )
        for k, v in options.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [buttons[0], buttons[1]],
        [buttons[2], buttons[3]],
        [InlineKeyboardButton(text="🛑 Закончить", callback_data="training_stop")],
    ])


def training_summary_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")],
        [InlineKeyboardButton(text="🏋️ Новая тренировка", callback_data="training_start")],
    ])
