"""
Sprint mode handler — US-002.
Flow: sprint_start → sprint_go → sprint_ans:{option} (loop) → result
question_id is stored in Redis session (current_question_id field).
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from bot.keyboards.sprint import answer_keyboard, sprint_intro_keyboard, sprint_result_keyboard
from repositories.progress_repo import ProgressRepository
from repositories.question_repo import QuestionRepository
from services import session_service, stats_service
from services.mistake_service import add_mistake
from services.question_service import get_sprint_questions

router = Router()

SPRINT_INTRO_TEXT = (
    "🚀 <b>Режим Спринт</b>\n\n"
    "15 вопросов разной сложности. После каждого ответа — мгновенный фидбек.\n"
    "За правильные ответы ты получаешь XP, ошибки попадают в раздел «Мои ошибки».\n\n"
    "🎁 <b>Бонус:</b> +50 XP за завершение спринта!\n\n"
    "Готов?"
)


@router.callback_query(F.data == "sprint_start")
async def sprint_start(callback: CallbackQuery):
    logger.info(f"[HANDLER:sprint] User {callback.from_user.id} opened sprint intro")
    await callback.message.edit_text(
        SPRINT_INTRO_TEXT,
        reply_markup=sprint_intro_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "sprint_go")
async def sprint_go(callback: CallbackQuery, db, user):
    uid = callback.from_user.id
    logger.info(f"[HANDLER:sprint] User {uid} started sprint")

    # Get question IDs
    question_ids = await get_sprint_questions(topic_ids=None, db=db)
    if not question_ids:
        await callback.message.edit_text("😔 Не удалось загрузить вопросы. Попробуйте позже.")
        await callback.answer()
        return

    # Create Redis session
    session = await session_service.create_sprint_session(uid, question_ids)

    # Load first question
    await _show_sprint_question(callback, session, db)
    await callback.answer()


@router.callback_query(F.data.startswith("sprint_ans:"))
async def sprint_answer(callback: CallbackQuery, db, user):
    uid = callback.from_user.id
    option = callback.data.split(":")[1]  # a/b/c/d

    # Load session from Redis
    session = await session_service.get_session(uid, "sprint")
    if not session:
        await callback.answer("⚠️ Сессия истекла. Начни спринт заново.", show_alert=True)
        return

    current_idx = session["current_idx"]
    question_ids = session["questions"]
    question_id = question_ids[current_idx]

    # Load question from DB
    question = await QuestionRepository.get_by_id(question_id, db)
    if not question:
        await callback.answer("❗ Ошибка загрузки вопроса.", show_alert=True)
        return

    is_correct = option == question.correct_option
    logger.info(
        f"[HANDLER:sprint] ans={option} q={question_id} correct={is_correct} user={uid}"
    )

    # Save progress
    await ProgressRepository.add(uid, question_id, is_correct, db)

    # Handle result
    if is_correct:
        xp_result = await stats_service.award_xp(uid, stats_service.XP_CORRECT, db)
        feedback = (
            f"✅ <b>Правильно!</b> +{stats_service.XP_CORRECT} XP\n"
            + (f"🎉 <b>Новый уровень: {xp_result['level']}!</b>\n" if xp_result.get("level_up") else "")
        )
    else:
        await add_mistake(uid, question_id, db)
        correct_text = question.get_options()[question.correct_option]
        feedback = (
            f"❌ <b>Неверно.</b>\n\n"
            f"Верный ответ: <b>{question.correct_option.upper()}. {correct_text}</b>\n\n"
            + (f"💡 {question.explanation}" if question.explanation else "")
        )

    # Advance session
    session["current_idx"] += 1
    if is_correct:
        session["correct_count"] += 1

    total = session["total"]
    new_idx = session["current_idx"]

    if new_idx >= total:
        # Sprint finished
        await session_service.delete_session(uid, "sprint")
        bonus_result = await stats_service.award_xp(uid, stats_service.XP_SPRINT_BONUS, db)
        await stats_service.update_accuracy(uid, db)

        result_text = (
            f"{feedback}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏁 <b>Спринт завершён!</b>\n\n"
            f"✅ Правильно: <b>{session['correct_count']}/{total}</b>\n"
            f"🎁 Бонус за спринт: <b>+{stats_service.XP_SPRINT_BONUS} XP</b>\n"
            + (f"🎉 <b>Уровень повышен: {bonus_result['level']}!</b>\n" if bonus_result.get("level_up") else "")
        )
        logger.info(f"[HANDLER:sprint] Done: {session['correct_count']}/{total} user={uid}")
        
        if question.image_url:
            await callback.message.edit_caption(
                caption=result_text, reply_markup=sprint_result_keyboard(), parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                result_text, reply_markup=sprint_result_keyboard(), parse_mode="HTML"
            )
    else:
        # Update session and show next question
        await session_service.update_session(uid, "sprint", session)
        if question.image_url:
            await callback.message.edit_caption(
                caption=feedback,
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                feedback,
                parse_mode="HTML",
            )
        await _show_next_question_delayed(callback, session, db)

    await callback.answer()


@router.callback_query(F.data == "sprint_menu")
async def sprint_menu(callback: CallbackQuery):
    uid = callback.from_user.id
    logger.debug(f"[HANDLER:sprint] User {uid} exited sprint to menu")
    await session_service.delete_session(uid, "sprint")
    from bot.keyboards.main_menu import main_menu_keyboard
    await callback.message.edit_text(
        "📋 <b>Главное меню</b>", reply_markup=main_menu_keyboard(), parse_mode="HTML"
    )
    await callback.answer()


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _show_sprint_question(callback: CallbackQuery, session: dict, db) -> None:
    """Load question from session and display it."""
    idx = session["current_idx"]
    questions = session["questions"]
    total = session["total"]
    question_id = questions[idx]

    question = await QuestionRepository.get_by_id(question_id, db)
    if not question:
        return

    # Store current_question_id in session (for answer handler)
    session["current_question_id"] = question_id
    await session_service.update_session(callback.from_user.id, "sprint", session)

    text = (
        f"❓ <b>Вопрос {idx + 1}/{total}</b>\n\n"
        f"{question.text}"
    )
    
    markup = answer_keyboard(question.get_options())
    if question.image_url:
        # First question of sprint, coming from intro message without image
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


async def _show_next_question_delayed(callback: CallbackQuery, session: dict, db) -> None:
    """After feedback, immediately show next question by sending a new message."""
    idx = session["current_idx"]
    questions = session["questions"]
    total = session["total"]
    question_id = questions[idx]

    question = await QuestionRepository.get_by_id(question_id, db)
    if not question:
        return

    session["current_question_id"] = question_id
    await session_service.update_session(callback.from_user.id, "sprint", session)

    text = (
        f"❓ <b>Вопрос {idx + 1}/{total}</b>\n\n"
        f"{question.text}"
    )
    
    markup = answer_keyboard(question.get_options())
    if question.image_url:
        await callback.message.answer_photo(
            photo=question.image_url,
            caption=text,
            reply_markup=markup,
            parse_mode="HTML",
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=markup,
            parse_mode="HTML",
        )
