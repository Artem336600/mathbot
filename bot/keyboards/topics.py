"""Topics keyboards. Callbacks within 64 bytes."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.models import Question, Topic


def topics_list_keyboard(topics: list[Topic]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t.title, callback_data=f"topic_card:{t.id}")]
        for t in topics
    ]
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def topic_card_keyboard(topic_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📖 Теория", callback_data=f"topic_theory:{topic_id}"),
            InlineKeyboardButton(text="📝 Задачи", callback_data=f"topic_tasks:{topic_id}"),
        ],
        [InlineKeyboardButton(text="🔙 К темам", callback_data="topics_list")],
    ])


def tasks_list_keyboard(
    questions: list[Question], solved_ids: list[int], topic_id: int
) -> InlineKeyboardMarkup:
    diff_labels = {1: "🟢", 2: "🟡", 3: "🔴"}
    rows = []
    for q in questions:
        mark = "✅" if q.id in solved_ids else "☐"
        diff = diff_labels.get(q.difficulty, "")
        label = f"{mark} {diff} {q.text[:35]}..."
        rows.append([
            InlineKeyboardButton(text=label, callback_data=f"solve_q:{q.id}")
        ])
    rows.append([
        InlineKeyboardButton(text="🔙 К теме", callback_data=f"topic_card:{topic_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def task_solve_keyboard(options: dict) -> InlineKeyboardMarkup:
    """
    Answer buttons. Callbacks: topic_ans:a/b/c/d (~13 bytes)
    current_question_id stored in Redis temp topics_session:{user_id}
    """
    labels = {"a": "A", "b": "B", "c": "C", "d": "D"}
    buttons = [
        InlineKeyboardButton(
            text=f"{labels[k]}: {v[:30]}",
            callback_data=f"topic_ans:{k}",
        )
        for k, v in options.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [buttons[0], buttons[1]],
        [buttons[2], buttons[3]],
    ])


def task_feedback_keyboard(topic_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 К списку", callback_data=f"topic_tasks:{topic_id}"),
            InlineKeyboardButton(text="➡️ Следующая", callback_data=f"topic_next:{topic_id}"),
        ]
    ])
