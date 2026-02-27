import contextlib
from aiogram.types import Message

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
    return await message.edit_text(text, **kwargs)
