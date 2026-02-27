"""
Training mode handler — US-003.
Adaptive difficulty: correct → difficulty+1, wrong → difficulty-1 (min=1, max=3).
current_question_id stored in Redis, NOT in callback.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from bot.keyboards.training import (
    training_answer_keyboard,
    training_setup_keyboard,
    training_summary_keyboard,
)
from repositories.progress_repo import ProgressRepository
from repositories.question_repo import QuestionRepository
from repositories.topic_repo import TopicRepository
from services import session_service, stats_service
from services.mistake_service import add_mistake
from services.question_service import get_next_training_question

router = Router()


@router.callback_query(F.data == "training_start")
async def training_start(callback: CallbackQuery, db):
    uid = callback.from_user.id
    logger.debug(f"[HANDLER:training] User {uid} opened topic selection")

    topics = await TopicRepository.get_all(db)
    if not topics:
        await callback.message.edit_text("😔 Темы не найдены. Обратитесь к администратору.")
        await callback.answer()
        return

    # Default: all topics selected
    all_ids = [t.id for t in topics]

    # Store selection temp in Redis
    await session_service.set_temp(uid, "train_topics", {"selected": all_ids})

    await callback.message.edit_text(
        "🏋️ <b>Режим Тренировка</b>\n\n"
        "Выберите темы для тренировки. Сложность адаптируется под твои ответы.\n\n"
        "📌 Выбраны все темы. Нажми на тему, чтобы убрать её.",
        reply_markup=training_setup_keyboard(topics, all_ids),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("train_tog:"))
async def training_topic_toggle(callback: CallbackQuery, db):
    uid = callback.from_user.id
    topic_id = int(callback.data.split(":")[1])
    logger.debug(f"[HANDLER:training] User {uid} toggled topic {topic_id}")

    temp = await session_service.get_temp(uid, "train_topics")
    selected = temp.get("selected", []) if temp else []

    if topic_id in selected:
        selected.remove(topic_id)
    else:
        selected.append(topic_id)

    await session_service.set_temp(uid, "train_topics", {"selected": selected})

    topics = await TopicRepository.get_all(db)
    await callback.message.edit_reply_markup(
        reply_markup=training_setup_keyboard(topics, selected)
    )
    await callback.answer()


@router.callback_query(F.data == "training_begin")
async def training_begin(callback: CallbackQuery, db):
    uid = callback.from_user.id

    temp = await session_service.get_temp(uid, "train_topics")
    selected = temp.get("selected", []) if temp else []

    if not selected:
        await callback.answer("⚠️ Выберите хотя бы одну тему!", show_alert=True)
        return

    logger.info(f"[HANDLER:training] Started. User={uid} Topics={selected} difficulty=1")

    # Create training session
    session = await session_service.create_training_session(uid, selected)
    await session_service.delete_temp(uid, "train_topics")

    # Get first question
    question = await get_next_training_question(session, db)
    if not question:
        await callback.message.edit_text("😔 Нет доступных вопросов для выбранных тем.")
        await callback.answer()
        return

    session["current_question_id"] = question.id
    await session_service.update_session(uid, "training", session)

    text = (
        f"🏋️ <b>Тренировка</b> | Сложность: {'⭐' * session['difficulty']}\n\n"
        f"{question.text}"
    )
    markup = training_answer_keyboard(question.get_options())
    if question.image_url:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=question.image_url, caption=text, reply_markup=markup, parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text, reply_markup=markup, parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("train_ans:"))
async def training_answer(callback: CallbackQuery, db, user):
    uid = callback.from_user.id
    option = callback.data.split(":")[1]

    session = await session_service.get_session(uid, "training")
    if not session:
        await callback.answer("⚠️ Сессия истекла. Начни тренировку заново.", show_alert=True)
        return

    question_id = session.get("current_question_id")
    if not question_id:
        await callback.answer("❗ Ошибка сессии.", show_alert=True)
        return

    question = await QuestionRepository.get_by_id(question_id, db)
    if not question:
        await callback.answer("❗ Вопрос не найден.", show_alert=True)
        return

    is_correct = option == question.correct_option
    old_difficulty = session["difficulty"]

    logger.info(
        f"[HANDLER:training] ans={option} correct={is_correct}"
        f" user={uid} q={question_id}"
    )

    await ProgressRepository.add(uid, question_id, is_correct, db)

    if is_correct:
        session["difficulty"] = min(3, session["difficulty"] + 1)
        session["xp_earned"] = session.get("xp_earned", 0) + stats_service.XP_CORRECT
        await stats_service.award_xp(uid, stats_service.XP_CORRECT, db)
        feedback = (
            f"✅ <b>Правильно!</b> +{stats_service.XP_CORRECT} XP\n"
            f"🔼 Сложность: {'⭐' * session['difficulty']}"
        )
    else:
        session["difficulty"] = max(1, session["difficulty"] - 1)
        await add_mistake(uid, question_id, db)
        correct_text = question.get_options()[question.correct_option]
        feedback = (
            f"❌ <b>Неверно.</b>\n\n"
            f"Верный ответ: <b>{question.correct_option.upper()}. {correct_text}</b>\n\n"
            + (f"💡 {question.explanation}\n\n" if question.explanation else "")
            + f"🔽 Сложность: {'⭐' * session['difficulty']}"
        )

    logger.debug(
        f"[HANDLER:training] difficulty: {old_difficulty}→{session['difficulty']} user={uid}"
    )

    session["solved_count"] = session.get("solved_count", 0) + 1

    # Get next question
    question = await get_next_training_question(session, db)
    if not question:
        await session_service.delete_session(uid, "training")
        await callback.message.edit_text(
            f"{feedback}\n\n😔 Вопросы закончились.",
            reply_markup=training_summary_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    session["current_question_id"] = question.id
    await session_service.update_session(uid, "training", session)

    # Show feedback then next question
    await callback.message.edit_text(feedback, parse_mode="HTML")
    next_text = (
        f"🏋️ <b>Тренировка</b> | #{session['solved_count'] + 1} | "
        f"Сложность: {'⭐' * session['difficulty']}\n\n"
        f"{question.text}"
    )
    markup = training_answer_keyboard(question.get_options())
    if question.image_url:
        await callback.message.answer_photo(
            photo=question.image_url, caption=next_text, reply_markup=markup, parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            next_text, reply_markup=markup, parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data == "training_stop")
async def training_stop(callback: CallbackQuery, db, user):
    uid = callback.from_user.id
    session = await session_service.get_session(uid, "training")

    solved = session.get("solved_count", 0) if session else 0
    xp = session.get("xp_earned", 0) if session else 0

    await session_service.delete_session(uid, "training")
    await stats_service.update_accuracy(uid, db)

    logger.info(f"[HANDLER:training] Stopped. User={uid} solved={solved} xp={xp}")

    text = (
        f"🏁 <b>Тренировка завершена!</b>\n\n"
        f"✅ Решено вопросов: <b>{solved}</b>\n"
        f"⭐ XP заработано: <b>{xp}</b>"
    )
    await callback.message.edit_text(
        text, reply_markup=training_summary_keyboard(), parse_mode="HTML"
    )
    await callback.answer()
