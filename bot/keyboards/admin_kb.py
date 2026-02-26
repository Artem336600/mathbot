"""Admin keyboards."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from db.models import Topic


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📚 Управление темами", callback_data="admin_topics"),
            InlineKeyboardButton(text="❓ Управление вопросами", callback_data="admin_questions"),
        ],
        [
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
            InlineKeyboardButton(text="🔙 В меню", callback_data="main_menu"),
        ],
    ])


def admin_topics_keyboard(topics: list[Topic]) -> InlineKeyboardMarkup:
    rows = []
    for t in topics:
        rows.append([
            InlineKeyboardButton(text=t.title, callback_data=f"adm_topic:{t.id}"),
        ])
    rows.append([
        InlineKeyboardButton(text="➕ Добавить тему", callback_data="admin_add_topic"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_topic_actions_keyboard(topic_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"adm_edit_topic:{topic_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"adm_del_topic:{topic_id}"),
        ],
        [
            InlineKeyboardButton(text="➕ Добавить вопрос", callback_data=f"admin_add_q:{topic_id}"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_topics")],
    ])


def admin_questions_keyboard(topics: list[Topic]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"📂 {t.title}", callback_data=f"adm_qs:{t.id}")]
        for t in topics
    ]
    rows.append([
        InlineKeyboardButton(text="➕ Добавить вопрос", callback_data="admin_add_q:0"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_broadcast_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel"),
        ]
    ])


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
