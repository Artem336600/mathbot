"""Start handler — /start command and main menu navigation."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.keyboards.main_menu import main_menu_keyboard
from bot.keyboards.reply import main_reply_keyboard
from services import user_service

router = Router()

WELCOME_TEXT = (
    "👋 Добро пожаловать в <b>MathTrainer</b>!\n\n"
    "Тренируй математику каждый день — быстро, удобно, прямо в Telegram.\n\n"
    "Выбери режим:"
)


@router.message(Command("start"))
async def cmd_start(message: Message, db, user=None):
    tg_user = message.from_user
    # Register or get user (handled by middleware, but ensure it exists)
    if user is None:
        user = await user_service.register_user(
            tg_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name or "",
            db=db,
        )
    logger.info(f"[HANDLER:start] User {tg_user.id} registered/found: level={user.level}")

    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_reply_keyboard(),
        parse_mode="HTML",
    )
    await message.answer(
        "📋 <b>Главное меню</b>",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text == "🏠 Меню")
async def cmd_menu_reply(message: Message):
    logger.debug(f"[HANDLER:start] Menu button from user {message.from_user.id}")
    await message.answer("📋 <b>Главное меню</b>", reply_markup=main_menu_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    logger.debug(f"[HANDLER:start] main_menu callback from {callback.from_user.id}")
    await callback.message.edit_text(
        "📋 <b>Главное меню</b>",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()
