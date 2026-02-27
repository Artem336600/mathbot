"""
Topics catalog handler — US-004.
question_id stored in Redis temp (topics_session:{user_id}), NOT in callback.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from bot.keyboards.topics import (
    task_feedback_keyboard,
    task_solve_keyboard,
    tasks_list_keyboard,
    topic_card_keyboard,
    topics_list_keyboard,
)
from repositories.progress_repo import ProgressRepository
from repositories.question_repo import QuestionRepository
from repositories.topic_repo import TopicRepository
from services import session_service, stats_service
from services.mistake_service import add_mistake

router = Router()


@router.callback_query(F.data == "topics_list")
async def topics_list(callback: CallbackQuery, db):
    logger.debug(f"[HANDLER:topics] User {callback.from_user.id} opened topics list")
    topics = await TopicRepository.get_all(db)
    await callback.message.edit_text(
        "📚 <b>Каталог тем</b>\n\nВыбери тему для изучения:",
        reply_markup=topics_list_keyboard(topics),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("topic_card:"))
async def topic_card(callback: CallbackQuery, db):
    topic_id = int(callback.data.split(":")[1])
    logger.debug(f"[HANDLER:topics] User {callback.from_user.id} opened topic {topic_id}")

    topic = await TopicRepository.get(topic_id, db)
    if not topic:
        await callback.answer("Тема не найдена.", show_alert=True)
        return

    questions = await QuestionRepository.get_by_topic(topic_id, db)
    easy = sum(1 for q in questions if q.difficulty == 1)
    medium = sum(1 for q in questions if q.difficulty == 2)
    hard = sum(1 for q in questions if q.difficulty == 3)

    text = (
        f"📚 <b>{topic.title}</b>\n\n"
        f"📊 Задач: {len(questions)} "
        f"(🟢{easy} 🟡{medium} 🔴{hard})"
    )
    await callback.message.edit_text(
        text, reply_markup=topic_card_keyboard(topic_id), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("topic_theory:"))
async def topic_theory(callback: CallbackQuery, db):
    topic_id = int(callback.data.split(":")[1])
    topic = await TopicRepository.get(topic_id, db)
    if not topic:
        await callback.answer("Тема не найдена.", show_alert=True)
        return

    theory = topic.theory_text or "Теория не добавлена."
    text = f"📖 <b>{topic.title}</b>\n\n{theory}"
    
    markup = topic_card_keyboard(topic_id)
    if topic.image_url:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=topic.image_url,
            caption=text,
            reply_markup=markup,
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=markup,
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("topic_tasks:"))
async def topic_tasks(callback: CallbackQuery, db):
    uid = callback.from_user.id
    topic_id = int(callback.data.split(":")[1])

    topic = await TopicRepository.get(topic_id, db)
    questions = await QuestionRepository.get_by_topic(topic_id, db)
    solved_ids = await ProgressRepository.get_solved_ids(uid, topic_id, db)

    logger.debug(
        f"[HANDLER:topics] opened topic {topic_id} tasks. "
        f"total={len(questions)} solved={len(solved_ids)} user={uid}"
    )

    await callback.message.edit_text(
        f"📝 <b>{topic.title if topic else 'Тема'}</b> — Задачи\n\n"
        f"Решено: {len(solved_ids)}/{len(questions)}",
        reply_markup=tasks_list_keyboard(questions, solved_ids, topic_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("solve_q:"))
async def solve_question(callback: CallbackQuery, db):
    uid = callback.from_user.id
    question_id = int(callback.data.split(":")[1])

    question = await QuestionRepository.get_by_id(question_id, db)
    if not question:
        await callback.answer("Вопрос не найден.", show_alert=True)
        return

    # Store current question in Redis temp
    await session_service.set_temp(
        uid, "topics_session",
        {"current_question_id": question_id, "topic_id": question.topic_id}
    )

    logger.debug(f"[HANDLER:topics] User {uid} solving q={question_id}")

    text = f"❓ <b>Вопрос</b>\n\n{question.text}"
    markup = task_solve_keyboard(question.get_options())
    
    if question.image_url:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=question.image_url,
            caption=text,
            reply_markup=markup,
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=markup,
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("topic_ans:"))
async def topic_answer(callback: CallbackQuery, db, user):
    uid = callback.from_user.id
    option = callback.data.split(":")[1]

    temp = await session_service.get_temp(uid, "topics_session")
    if not temp:
        await callback.answer("⚠️ Сессия истекла. Вернитесь к списку задач.", show_alert=True)
        return

    question_id = temp["current_question_id"]
    topic_id = temp["topic_id"]

    question = await QuestionRepository.get_by_id(question_id, db)
    if not question:
        await callback.answer("❗ Ошибка.", show_alert=True)
        return

    is_correct = option == question.correct_option
    logger.info(f"[HANDLER:topics] solved q={question_id} correct={is_correct} user={uid}")

    await ProgressRepository.add(uid, question_id, is_correct, db)

    if is_correct:
        await stats_service.award_xp(uid, stats_service.XP_CORRECT, db)
        feedback = f"✅ <b>Правильно!</b> +{stats_service.XP_CORRECT} XP"
    else:
        await add_mistake(uid, question_id, db)
        correct_text = question.get_options()[question.correct_option]
        feedback = (
            f"❌ <b>Неверно.</b>\n\n"
            f"Верный ответ: <b>{question.correct_option.upper()}. {correct_text}</b>\n\n"
            + (f"💡 {question.explanation}" if question.explanation else "")
        )

    markup = task_feedback_keyboard(topic_id)
    if question.image_url:
        await callback.message.edit_caption(
            caption=feedback,
            reply_markup=markup,
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            feedback,
            reply_markup=markup,
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("topic_next:"))
async def topic_next(callback: CallbackQuery, db):
    """Show a random unsolved question from the same topic."""
    uid = callback.from_user.id
    topic_id = int(callback.data.split(":")[1])

    questions = await QuestionRepository.get_by_topic(topic_id, db)
    solved_ids = await ProgressRepository.get_solved_ids(uid, topic_id, db)
    unsolved = [q for q in questions if q.id not in solved_ids]

    if not unsolved:
        await callback.answer("🎉 Все задачи темы решены!", show_alert=True)
        return

    import random
    question = random.choice(unsolved)

    await session_service.set_temp(
        uid, "topics_session",
        {"current_question_id": question.id, "topic_id": topic_id}
    )

    text = f"❓ <b>Вопрос</b>\n\n{question.text}"
    markup = task_solve_keyboard(question.get_options())
    
    if question.image_url:
        # since previous message could be text/photo feedback, easier to delete and resend
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=question.image_url,
            caption=text,
            reply_markup=markup,
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=markup,
            parse_mode="HTML",
        )
    await callback.answer()
