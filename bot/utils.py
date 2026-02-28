import contextlib
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

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

async def get_question_media(question, db, StorageService, AttachmentRepository, BufferedInputFile):
    """
    Returns media list (InputMediaPhoto) and has_media_group boolean 
    for a question if it has attached photos. Returns (None, False) if empty.
    Used for Sprint and Training modes to mimic topics logic.
    """
    from aiogram.types import InputMediaPhoto

    attachments = await AttachmentRepository.get_for_entity("question", question.id, db)
    photos = [a for a in attachments if a.attachment_type == "photo"]
    
    if not photos:
        return None, False

    media = []
    has_media_group = len(photos) >= 2
    
    for idx, p in enumerate(photos[:10]):  # max 10 for media group
        url = await StorageService.get_presigned_url(p.file_key)
        
        # If URL is local, we MUST download it and send as BufferedInputFile
        is_local = any(x in url for x in ["localhost", "127.0.0.1", "minio"])
        
        photo_file = url
        if is_local:
            logger.debug(f"[UTILS] local URL detected for file_key={p.file_key}, downloading...")
            data = await StorageService.get_file(p.file_key)
            if data:
                photo_file = BufferedInputFile(data, filename=p.file_name)
            else:
                logger.error(f"[UTILS] FAILED to download local file for file_key={p.file_key}. Telegram will likely reject the URL.")
        
        media.append(InputMediaPhoto(media=photo_file))

    return media, has_media_group
