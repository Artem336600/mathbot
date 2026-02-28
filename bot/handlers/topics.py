"""
Topics catalog handler — US-004.
question_id stored in Redis temp (topics_session:{user_id}), NOT in callback.
"""
import random

from aiogram import F, Router
from aiogram.types import CallbackQuery, InputMediaPhoto
from loguru import logger

from bot.keyboards.topics import (
    task_feedback_keyboard,
    task_solve_keyboard,
    tasks_list_keyboard,
    topic_card_keyboard,
    topics_list_keyboard,
)
from repositories.attachment_repo import AttachmentRepository
from repositories.progress_repo import ProgressRepository
from repositories.question_repo import QuestionRepository
from repositories.topic_repo import TopicRepository
from services import session_service, stats_service
from services.mistake_service import add_mistake
from services.storage_service import StorageService
from bot.utils import safe_edit_text

router = Router()

TELEGRAM_MEDIA_GROUP_LIMIT = 10


async def _send_question(callback: CallbackQuery, question, db) -> bool:
    """
    Send a question to the user, including any photo attachments.
    Returns True if a media group was sent (affects how feedback is sent later).
    """
    uid = callback.from_user.id
    attachments = await AttachmentRepository.get_for_entity("question", question.id, db)
    photos = [a for a in attachments if a.attachment_type == "photo"]

    logger.debug(f"[HANDLER:topics] question {question.id} has {len(photos)} photo attachments")

    text = f"❓ <b>Вопрос</b>\n\n{question.text}"
    markup = task_solve_keyboard(question.get_options())

    if len(photos) >= 2:
        # Send as media group — first photo gets caption, rest plain
        urls = []
        for p in photos[:TELEGRAM_MEDIA_GROUP_LIMIT]:
            url = await StorageService.get_presigned_url(p.file_key)
            urls.append(url)

        media = []
        for i, url in enumerate(urls):
            if i == 0:
                media.append(InputMediaPhoto(media=url, caption=text, parse_mode="HTML"))
            else:
                media.append(InputMediaPhoto(media=url))

        try:
            await callback.message.delete()
        except Exception:
            pass

        try:
            await callback.message.answer_media_group(media=media)
            # Keyboard must be a separate message since media groups can't have reply_markup
            await callback.message.answer("👆 Выберите ответ:", reply_markup=markup)
            logger.info(f"[HANDLER:topics] sent {len(media)} photos for question {question.id} to user={uid}")
            return True  # has_media_group → feedback must be sent as new message
        except Exception as e:
            logger.error(f"[HANDLER:topics] failed to send media group: {e}")
            # Fallback to plain text
            await safe_edit_text(callback.message, text, reply_markup=markup, parse_mode="HTML")
            return False

    elif len(photos) == 1:
        url = await StorageService.get_presigned_url(photos[0].file_key)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            photo=url,
            caption=text,
            reply_markup=markup,
            parse_mode="HTML"
        )
        logger.info(f"[HANDLER:topics] sent 1 photo for question {question.id} to user={uid}")
        return False  # single photo with caption → can edit caption on answer

    else:
        # Fallback: legacy image_url field
        if question.image_url:
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer_photo(
                photo=question.image_url,
                caption=text,
                reply_markup=markup,
                parse_mode="HTML"
            )
            return False
        else:
            await safe_edit_text(callback.message, text, reply_markup=markup, parse_mode="HTML")
            return False


@router.callback_query(F.data == "topics_list")
async def topics_list(callback: CallbackQuery, db):
    logger.debug(f"[HANDLER:topics] User {callback.from_user.id} opened topics list")
    topics = await TopicRepository.get_all(db)
    await safe_edit_text(callback.message,
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
    await safe_edit_text(callback.message,
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

    # Fetch attachments
    attachments = await AttachmentRepository.get_for_entity("topic", topic_id, db)
    photos = [a for a in attachments if a.attachment_type == "photo"]
    docs = [a for a in attachments if a.attachment_type == "document"]

    logger.debug(f"[HANDLER:topics] sending theory topic={topic_id}: photos={len(photos)} docs={len(docs)}")

    if photos:
        # Build presigned URLs for all photos
        photo_urls = []
        for p in photos:
            url = await StorageService.get_presigned_url(p.file_key)
            photo_urls.append(url)

        try:
            await callback.message.delete()
        except Exception:
            pass

        # Send in batches of 10 (Telegram media group limit)
        for batch_start in range(0, len(photo_urls), TELEGRAM_MEDIA_GROUP_LIMIT):
            batch = photo_urls[batch_start:batch_start + TELEGRAM_MEDIA_GROUP_LIMIT]
            media = []
            for i, url in enumerate(batch):
                # First photo of the very first batch gets theory text as caption
                if batch_start == 0 and i == 0:
                    media.append(InputMediaPhoto(media=url, caption=text, parse_mode="HTML"))
                else:
                    media.append(InputMediaPhoto(media=url))
            try:
                await callback.message.answer_media_group(media=media)
            except Exception as e:
                logger.error(f"[HANDLER:topics] failed to send media group: {e}")

        # Navigation keyboard after photos
        await callback.message.answer("📚 Вернуться:", reply_markup=markup)
        logger.info(f"[HANDLER:topics] theory sent with media group to user={callback.from_user.id}")
    else:
        # No attachment photos — use legacy image_url or plain text
        if topic.image_url:
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer_photo(
                photo=topic.image_url,
                caption=text,
                reply_markup=markup,
                parse_mode="HTML"
            )
        else:
            await safe_edit_text(callback.message, text, reply_markup=markup, parse_mode="HTML")

    # Send documents as separate messages
    for doc_att in docs:
        doc_url = await StorageService.get_presigned_url(doc_att.file_key)
        try:
            await callback.message.answer_document(
                document=doc_url,
                caption=f"📎 {doc_att.file_name}"
            )
        except Exception as e:
            logger.error(f"[HANDLER:topics] failed to send document {doc_att.id}: {e}")

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

    await safe_edit_text(callback.message,
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

    has_media_group = await _send_question(callback, question, db)

    # Store current question + media group flag in Redis
    await session_service.set_temp(
        uid, "topics_session",
        {
            "current_question_id": question_id,
            "topic_id": question.topic_id,
            "has_media_group": has_media_group,
        }
    )

    logger.debug(f"[HANDLER:topics] User {uid} solving q={question_id} has_media_group={has_media_group}")
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
    has_media_group = temp.get("has_media_group", False)

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

    if has_media_group:
        # Media group messages can't have their caption edited — send new message
        await callback.message.answer(feedback, reply_markup=markup, parse_mode="HTML")
    elif question.image_url:
        await callback.message.edit_caption(
            caption=feedback,
            reply_markup=markup,
            parse_mode="HTML",
        )
    else:
        await safe_edit_text(callback.message, feedback, reply_markup=markup, parse_mode="HTML")

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

    question = random.choice(unsolved)
    has_media_group = await _send_question(callback, question, db)

    await session_service.set_temp(
        uid, "topics_session",
        {
            "current_question_id": question.id,
            "topic_id": topic_id,
            "has_media_group": has_media_group,
        }
    )

    await callback.answer()
