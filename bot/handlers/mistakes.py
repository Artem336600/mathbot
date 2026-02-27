"""
Mistakes handler — US-006.
mistake_id + question_id stored in Redis mistakes_session:{user_id}, NOT in callback.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from bot.keyboards.mistakes import (
    mistake_answer_keyboard,
    mistakes_empty_keyboard,
    mistakes_menu_keyboard,
)
from repositories.mistake_repo import MistakeRepository
from repositories.question_repo import QuestionRepository
from repositories.topic_repo import TopicRepository
from services import session_service, stats_service
from services.mistake_service import fix_mistake, get_random_mistake

router = Router()


@router.callback_query(F.data == "mistakes_menu")
async def mistakes_menu(callback: CallbackQuery, db):
    uid = callback.from_user.id
    count = await MistakeRepository.count(uid, db)
    logger.info(f"[HANDLER:mistakes] mistakes count={count} user={uid}")

    if count == 0:
        await callback.message.edit_text(
            "🎉 <b>Отлично!</b>\n\nУ тебя нет нерешённых ошибок. Молодец!",
            reply_markup=mistakes_empty_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    # Get topics that have mistakes
    topic_ids = await MistakeRepository.get_topics_with_mistakes(uid, db)
    topics = []
    for tid in topic_ids:
        topic = await TopicRepository.get(tid, db)
        if topic:
            topics.append(topic)

    await callback.message.edit_text(
        f"❌ <b>Работа над ошибками</b>\n\n"
        f"Нерешённых ошибок: <b>{count}</b>\n\n"
        f"Выбери режим:",
        reply_markup=mistakes_menu_keyboard(has_mistakes=True, topics_with_mistakes=topics),
        parse_mode="HTML",
    )
    await callback.answer()


async def _show_mistake(callback: CallbackQuery, topic_id: int | None, db, send_new: bool = False) -> None:
    """Helper: pick random mistake and show it."""
    uid = callback.from_user.id
    mistake = await get_random_mistake(uid, topic_id, db)

    if not mistake:
        text = "🎉 <b>Все ошибки исправлены!</b>" if topic_id is None else "🎉 <b>В этой теме все ошибки исправлены!</b>"
        if send_new:
            await callback.message.answer(text, reply_markup=mistakes_empty_keyboard(), parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=mistakes_empty_keyboard(), parse_mode="HTML")
        return

    question = await QuestionRepository.get_by_id(mistake.question_id, db)
    if not question:
        return

    # Store in Redis
    await session_service.set_temp(
        uid, "mistakes_session",
        {"current_mistake_id": mistake.id, "current_question_id": question.id, "topic_id": topic_id}
    )

    text = f"❌ <b>Ошибка</b>\n\n{question.text}"
    markup = mistake_answer_keyboard(question.get_options())
    if send_new:
        if question.image_url:
            await callback.message.answer_photo(photo=question.image_url, caption=text, reply_markup=markup, parse_mode="HTML")
        else:
            await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
    else:
        if question.image_url:
            # Can't edit text into photo, so we just delete and send new
            await callback.message.delete()
            await callback.message.answer_photo(photo=question.image_url, caption=text, reply_markup=markup, parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")


@router.callback_query(F.data == "mis_all")
async def mistakes_all(callback: CallbackQuery, db):
    logger.debug(f"[HANDLER:mistakes] User {callback.from_user.id} selected all mistakes")
    await _show_mistake(callback, topic_id=None, db=db)
    await callback.answer()


@router.callback_query(F.data.startswith("mis_top:"))
async def mistakes_by_topic(callback: CallbackQuery, db):
    topic_id = int(callback.data.split(":")[1])
    logger.debug(f"[HANDLER:mistakes] User {callback.from_user.id} selected topic {topic_id}")
    await _show_mistake(callback, topic_id=topic_id, db=db)
    await callback.answer()


@router.callback_query(F.data.startswith("mis_ans:"))
async def mistake_answer(callback: CallbackQuery, db, user):
    uid = callback.from_user.id
    option = callback.data.split(":")[1]

    temp = await session_service.get_temp(uid, "mistakes_session")
    if not temp:
        await callback.answer("⚠️ Сессия истекла.", show_alert=True)
        return

    mistake_id = temp["current_mistake_id"]
    question_id = temp["current_question_id"]
    topic_id = temp.get("topic_id")

    question = await QuestionRepository.get_by_id(question_id, db)
    if not question:
        await callback.answer("❗ Ошибка.", show_alert=True)
        return

    is_correct = option == question.correct_option

    if is_correct:
        await fix_mistake(mistake_id, uid, db)
        xp_result = await stats_service.award_xp(uid, stats_service.XP_FIX_MISTAKE, db)
        feedback = (
            f"✅ <b>Правильно! Ошибка исправлена!</b> +{stats_service.XP_FIX_MISTAKE} XP\n"
            + (f"🎉 <b>Уровень: {xp_result['level']}!</b>\n" if xp_result.get("level_up") else "")
        )
        logger.info(f"[HANDLER:mistakes] fixed mistake {mistake_id} q={question_id} user={uid}")
    else:
        correct_text = question.get_options()[question.correct_option]
        feedback = (
            f"❌ <b>Снова неверно.</b>\n\n"
            f"Верный ответ: <b>{question.correct_option.upper()}. {correct_text}</b>\n\n"
            + (f"💡 {question.explanation}" if question.explanation else "")
        )

    if question.image_url:
        await callback.message.edit_caption(caption=feedback, parse_mode="HTML")
    else:
        await callback.message.edit_text(feedback, parse_mode="HTML")

    # Check remaining mistakes logic is handled by _show_mistake
    # We send the next mistake as a NEW message, so the feedback above stays in chat
    await _show_mistake(callback, topic_id=topic_id, db=db, send_new=True)

    await callback.answer()
