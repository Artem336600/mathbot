"""
Admin content management — add/delete topics and questions.
FSM dialogs: AddTopicFSM, AddQuestionFSM.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.config import settings
from bot.fsm.admin import AddQuestionFSM, AddTopicFSM, EditTopicFSM
from bot.keyboards.admin_kb import (
    admin_questions_keyboard,
    admin_topic_actions_keyboard,
    admin_topics_keyboard,
    cancel_keyboard,
)
from repositories.question_repo import QuestionRepository
from repositories.topic_repo import TopicRepository

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


# ─── Topics ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_topics")
async def admin_topics(callback: CallbackQuery, db):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    topics = await TopicRepository.get_all(db)
    await callback.message.edit_text(
        "📚 <b>Управление темами</b>",
        reply_markup=admin_topics_keyboard(topics),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_topic:"))
async def admin_topic_detail(callback: CallbackQuery, db):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    topic_id = int(callback.data.split(":")[1])
    topic = await TopicRepository.get(topic_id, db)
    questions = await QuestionRepository.get_by_topic(topic_id, db)
    text = (
        f"📚 <b>{topic.title}</b>\n\n"
        f"Вопросов: {len(questions)}\n"
        f"Статус: {'✅ Активна' if topic.is_active else '❌ Скрыта'}"
    )
    await callback.message.edit_text(
        text, reply_markup=admin_topic_actions_keyboard(topic_id), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_topic")
async def start_add_topic(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    await state.set_state(AddTopicFSM.waiting_title)
    await callback.message.answer(
        "📝 Введите <b>название</b> новой темы (или «❌ Отмена»):",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AddTopicFSM.waiting_title)
async def add_topic_title(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.")
        return
    if len(message.text.strip()) > 128:
        await message.answer("❌ Название слишком длинное (макс. 128 символов).")
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(AddTopicFSM.waiting_theory)
    await message.answer(
        "📖 Введите <b>теорию</b> к теме (поддерживается HTML, или «-» чтобы пропустить):",
        parse_mode="HTML",
    )


@router.message(AddTopicFSM.waiting_theory)
async def add_topic_theory(message: Message, state: FSMContext, db):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.")
        return
    data = await state.get_data()
    theory = None if message.text.strip() == "-" else message.text.strip()
    topic = await TopicRepository.create(data["title"], theory or "", db)
    await state.clear()
    logger.info(f"[HANDLER:admin] Topic created: id={topic.id} title={topic.title!r}")
    await message.answer(f"✅ Тема <b>{topic.title}</b> добавлена (id={topic.id})", parse_mode="HTML")


@router.callback_query(F.data.startswith("adm_del_topic:"))
async def admin_delete_topic(callback: CallbackQuery, db):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    topic_id = int(callback.data.split(":")[1])
    deleted = await TopicRepository.delete(topic_id, db)
    if deleted:
        logger.info(f"[HANDLER:admin] Topic deleted: id={topic_id}")
        await callback.message.edit_text(f"🗑️ Тема id={topic_id} удалена.")
    else:
        await callback.message.edit_text("❌ Тема не найдена.")
    await callback.answer()


@router.callback_query(F.data.startswith("adm_edit_topic:"))
async def admin_edit_topic_start(callback: CallbackQuery, state: FSMContext, db):
    """Start edit topic FSM: ask for new title."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    topic_id = int(callback.data.split(":")[1])
    topic = await TopicRepository.get(topic_id, db)
    if not topic:
        await callback.answer("Тема не найдена.", show_alert=True)
        return

    await state.set_state(EditTopicFSM.waiting_new_title)
    await state.update_data(edit_topic_id=topic_id)
    logger.info(f"[HANDLER:admin] Editing topic id={topic_id}")

    await callback.message.answer(
        f"✏️ Редактирование темы <b>{topic.title}</b>\n\n"
        f"Введите новое название (или «-» чтобы оставить прежнее, «❌ Отмена»):",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(EditTopicFSM.waiting_new_title)
async def admin_edit_topic_title(message: Message, state: FSMContext, db):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.")
        return

    data = await state.get_data()
    topic_id = data["edit_topic_id"]
    topic = await TopicRepository.get(topic_id, db)

    new_title = topic.title if message.text.strip() == "-" else message.text.strip()
    await state.update_data(new_title=new_title)
    await state.set_state(EditTopicFSM.waiting_new_theory)

    current_theory = topic.theory_text or "(пусто)"
    await message.answer(
        f"📖 Текущая теория:\n<i>{current_theory[:300]}</i>\n\n"
        f"Введите новую теорию (или «-» чтобы оставить прежнее, «❌ Отмена»):",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(EditTopicFSM.waiting_new_theory)
async def admin_edit_topic_theory(message: Message, state: FSMContext, db):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.")
        return

    data = await state.get_data()
    topic_id = data["edit_topic_id"]
    new_title = data["new_title"]
    topic = await TopicRepository.get(topic_id, db)

    new_theory = topic.theory_text if message.text.strip() == "-" else message.text.strip()

    updated = await TopicRepository.update(topic_id, db, title=new_title, theory_text=new_theory)
    await state.clear()

    logger.info(f"[HANDLER:admin] Topic updated: id={topic_id} title={new_title!r}")
    await message.answer(
        f"✅ Тема обновлена!\n\n<b>{updated.title}</b>",
        parse_mode="HTML",
    )


# ─── Questions ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_questions")
async def admin_questions(callback: CallbackQuery, db):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    topics = await TopicRepository.get_all(db)
    await callback.message.edit_text(
        "❓ <b>Управление вопросами</b>\n\nВыберите тему:",
        reply_markup=admin_questions_keyboard(topics),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_add_q:"))
async def start_add_question(callback: CallbackQuery, state: FSMContext, db):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    topic_id = int(callback.data.split(":")[1])
    await state.update_data(topic_id=topic_id if topic_id != 0 else None)
    await state.set_state(AddQuestionFSM.waiting_text)
    await callback.message.answer(
        "❓ Введите текст <b>вопроса</b> (или «❌ Отмена»):",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


async def _ask_option(message: Message, label: str, state, next_state):
    await state.set_state(next_state)
    await message.answer(f"Вариант <b>{label}</b>:", parse_mode="HTML")


@router.message(AddQuestionFSM.waiting_text)
async def aq_text(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.")
        return
    if len(message.text.strip()) > 2000:
        await message.answer("❌ Текст вопроса слишком длинный (макс. 2000 символов).")
        return
    await state.update_data(text=message.text.strip())
    await _ask_option(message, "A", state, AddQuestionFSM.waiting_option_a)


@router.message(AddQuestionFSM.waiting_option_a)
async def aq_opt_a(message: Message, state: FSMContext):
    await state.update_data(option_a=message.text.strip())
    await _ask_option(message, "B", state, AddQuestionFSM.waiting_option_b)


@router.message(AddQuestionFSM.waiting_option_b)
async def aq_opt_b(message: Message, state: FSMContext):
    await state.update_data(option_b=message.text.strip())
    await _ask_option(message, "C", state, AddQuestionFSM.waiting_option_c)


@router.message(AddQuestionFSM.waiting_option_c)
async def aq_opt_c(message: Message, state: FSMContext):
    await state.update_data(option_c=message.text.strip())
    await _ask_option(message, "D", state, AddQuestionFSM.waiting_option_d)


@router.message(AddQuestionFSM.waiting_option_d)
async def aq_opt_d(message: Message, state: FSMContext):
    await state.update_data(option_d=message.text.strip())
    await state.set_state(AddQuestionFSM.waiting_correct)
    await message.answer("Правильный ответ? (введи a, b, c или d):")


@router.message(AddQuestionFSM.waiting_correct)
async def aq_correct(message: Message, state: FSMContext):
    opt = message.text.strip().lower()
    if opt not in ("a", "b", "c", "d"):
        await message.answer("❌ Введи одну букву: a, b, c или d")
        return
    await state.update_data(correct_option=opt)
    await state.set_state(AddQuestionFSM.waiting_explanation)
    await message.answer("Объяснение (или «-» чтобы пропустить):")


@router.message(AddQuestionFSM.waiting_explanation)
async def aq_explanation(message: Message, state: FSMContext):
    expl = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(explanation=expl)
    await state.set_state(AddQuestionFSM.waiting_difficulty)
    await message.answer("Сложность (1=лёгкая, 2=средняя, 3=сложная):")


@router.message(AddQuestionFSM.waiting_difficulty)
async def aq_difficulty(message: Message, state: FSMContext, db):
    text = message.text.strip()
    if text not in ("1", "2", "3"):
        await message.answer("❌ Введи 1, 2 или 3")
        return

    data = await state.get_data()
    topic_id = data.get("topic_id")

    if not topic_id:
        topics = await TopicRepository.get_all(db)
        if topics:
            topic_id = topics[0].id
        else:
            await message.answer("❌ Нет тем. Сначала создайте тему.")
            await state.clear()
            return

    q = await QuestionRepository.create(
        topic_id=topic_id,
        text=data["text"],
        option_a=data["option_a"],
        option_b=data["option_b"],
        option_c=data["option_c"],
        option_d=data["option_d"],
        correct_option=data["correct_option"],
        difficulty=int(text),
        explanation=data.get("explanation"),
        db=db,
    )
    await state.clear()
    logger.info(f"[HANDLER:admin] Question created id={q.id} topic={topic_id}")
    await message.answer(f"✅ Вопрос добавлен (id={q.id})")
