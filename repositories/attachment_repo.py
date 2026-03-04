"""Attachment repository."""
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Attachment


class AttachmentRepository:
    @staticmethod
    async def get_for_entity(entity_type: str, entity_id: int, db: AsyncSession) -> list[Attachment]:
        logger.debug(f"[REPO:Attachment] get_for_entity type={entity_type} id={entity_id}")
        result = await db.execute(
            select(Attachment)
            .where(Attachment.entity_type == entity_type, Attachment.entity_id == entity_id)
            .order_by(Attachment.id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(attachment_id: int, db: AsyncSession) -> Attachment | None:
        logger.debug(f"[REPO:Attachment] get_by_id id={attachment_id}")
        result = await db.execute(select(Attachment).where(Attachment.id == attachment_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        entity_type: str,
        entity_id: int,
        attachment_type: str,
        file_key: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        db: AsyncSession
    ) -> Attachment:
        logger.debug(f"[REPO:Attachment] create entity={entity_type}:{entity_id} file={file_name}")
        att = Attachment(
            entity_type=entity_type,
            entity_id=entity_id,
            attachment_type=attachment_type,
            file_key=file_key,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type
        )
        db.add(att)
        await db.commit()
        await db.refresh(att)
        logger.info(f"[REPO:Attachment] created id={att.id} entity={entity_type}:{entity_id}")
        return att

    @staticmethod
    async def delete(attachment_id: int, db: AsyncSession) -> Attachment | None:
        logger.debug(f"[REPO:Attachment] delete id={attachment_id}")
        result = await db.execute(select(Attachment).where(Attachment.id == attachment_id))
        att = result.scalar_one_or_none()
        if att:
            await db.delete(att)
            await db.commit()
            logger.info(f"[REPO:Attachment] deleted id={attachment_id}")
            return att
        return None

    @staticmethod
    async def delete_all_for_entity(entity_type: str, entity_id: int, db: AsyncSession) -> list[str]:
        logger.debug(f"[REPO:Attachment] delete_all_for_entity type={entity_type} id={entity_id}")
        result = await db.execute(
            select(Attachment)
            .where(Attachment.entity_type == entity_type, Attachment.entity_id == entity_id)
        )
        attachments = list(result.scalars().all())
        file_keys = [att.file_key for att in attachments]
        
        for att in attachments:
            await db.delete(att)
            
        if attachments:
            await db.commit()
            logger.info(f"[REPO:Attachment] deleted {len(attachments)} attachments for {entity_type}:{entity_id}")
            
        return file_keys
