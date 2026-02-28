import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram import Bot
from aiogram.types import Message, CallbackQuery, User as TgUser, Chat

@pytest.fixture
def mock_bot():
    """Mock for the Aiogram Bot instance."""
    bot = AsyncMock(spec=Bot)
    bot.send_message = AsyncMock()
    return bot

@pytest.fixture
def mock_tg_user():
    """Returns a mock Telegram User."""
    return TgUser(id=1, is_bot=False, first_name="Test", username="testuser")

@pytest.fixture
def mock_chat():
    """Returns a mock typical private chat."""
    return Chat(id=1, type="private")

@pytest.fixture
def mock_message(mock_tg_user, mock_chat, mock_bot):
    """Returns a mock Aiogram Message."""
    msg = MagicMock(spec=Message)
    msg.from_user = mock_tg_user
    msg.chat = mock_chat
    msg.answer = AsyncMock()
    msg.edit_text = AsyncMock()
    msg.delete = AsyncMock()
    msg.edit_caption = AsyncMock()
    msg.answer_photo = AsyncMock()
    msg.answer_media_group = AsyncMock()
    msg.bot = mock_bot
    msg.text = "Old mock text"
    return msg

@pytest.fixture
def mock_callback_query(mock_tg_user, mock_message, mock_bot):
    """Returns a mock Aiogram CallbackQuery."""
    cq = MagicMock(spec=CallbackQuery)
    cq.from_user = mock_tg_user
    cq.message = mock_message
    cq.answer = AsyncMock()
    cq.bot = mock_bot
    return cq
