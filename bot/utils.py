import contextlib
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

async def safe_edit_text(message: Message, text: str, **kwargs):
    """
    Элегантно заменяет сообщение с картинкой на текст,
    или просто редактирует текст, если картинки нет.
    Помогает избежать `TelegramBadRequest: there is no text in the message to edit`.
    """
    if not message.text:
        with contextlib.suppress(Exception):
            await message.delete()
        return await message.answer(text, **kwargs)
    
    try:
        return await message.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return message
        raise e
