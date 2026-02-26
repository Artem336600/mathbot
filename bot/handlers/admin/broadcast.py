"""
Admin broadcast handler — US-011.
FSM: BroadcastFSM — get message, confirm, send.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.config import settings
from bot.fsm.admin import BroadcastFSM
from bot.keyboards.admin_kb import cancel_keyboard, confirm_broadcast_keyboard
from services.broadcast_service import send_to_all

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    await state.set_state(BroadcastFSM.waiting_message)
    await callback.message.answer(
        "📢 Введите текст рассылки (или «❌ Отмена»).\n\n"
        "Поддерживается HTML-формат (<b>жирный</b>, <i>курсив</i>).",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(BroadcastFSM.waiting_message)
async def broadcast_text(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Рассылка отменена.")
        return

    await state.update_data(broadcast_text=message.text)
    await state.set_state(BroadcastFSM.confirming)

    await message.answer(
        f"📢 <b>Предпросмотр рассылки:</b>\n\n{message.text}\n\n"
        f"Отправить всем пользователям?",
        reply_markup=confirm_broadcast_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "broadcast_confirm", BroadcastFSM.confirming)
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext, db, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await state.clear()

    logger.info(f"[HANDLER:admin] Broadcast started by {callback.from_user.id}")
    await callback.message.edit_text("📤 Рассылка началась... Подождите.")

    result = await send_to_all(text, bot, db)

    await callback.message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📨 Отправлено: <b>{result['sent']}</b>\n"
        f"❌ Не доставлено: <b>{result['failed']}</b>\n"
        f"👥 Всего: <b>{result['total']}</b>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена.")
    await callback.answer()
