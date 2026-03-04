"""Attachments CRUD API for Admin Dashboard."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from webapp.auth import get_admin_user, get_db_session
from db.models import User
from webapp.schemas import AttachmentResponse
from repositories.attachment_repo import AttachmentRepository
from services.storage_service import StorageService

router = APIRouter(prefix="/api/attachments", tags=["attachments"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_FILES_PER_REQUEST = 10

PHOTO_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
DOC_MIMES = {
    "application/pdf", 
    "application/msword", 
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain"
}

@router.post("/{entity_type}/{entity_id}/upload", response_model=List[AttachmentResponse])
async def upload_attachments(
    entity_type: str,
    entity_id: int,
    files: List[UploadFile] = File(...),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    if entity_type not in ["topic", "question"]:
        raise HTTPException(400, "Invalid entity_type")
    if len(files) > MAX_FILES_PER_REQUEST:
        logger.warning(
            f"[WEBAPP:ATTACHMENTS] upload rejected reason=too_many_files count={len(files)} limit={MAX_FILES_PER_REQUEST}"
        )
        raise HTTPException(status_code=400, detail=f"Too many files. Max {MAX_FILES_PER_REQUEST} per request")
        
    responses = []
    
    for file in files:
        # Check size (requires reading the file, so we do it in memory for up to 20MB)
        data = await file.read()
        size = len(data)
        
        if size > MAX_FILE_SIZE:
            logger.warning("[WEBAPP:ATTACHMENTS] upload rejected reason=file_too_large")
            raise HTTPException(status_code=400, detail=f"File {file.filename} exceeds 20MB limit")

        mime = file.content_type
        
        # Determine attachment_type
        if mime in PHOTO_MIMES:
            attachment_type = "photo"
        elif mime in DOC_MIMES:
            attachment_type = "document"
        else:
            logger.warning("[WEBAPP:ATTACHMENTS] upload rejected reason=unsupported_mime")
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime}")
            
        if entity_type == "question" and attachment_type != "photo":
            logger.warning("[WEBAPP:ATTACHMENTS] upload rejected reason=question_non_photo")
            raise HTTPException(status_code=400, detail="Only photos are allowed for questions")
            
        # Upload to S3
        file_key = StorageService.generate_key(entity_type, entity_id, file.filename)
        try:
            await StorageService.upload_file(file_key, data, mime)
        except Exception:
            raise HTTPException(status_code=500, detail=f"Failed to upload {file.filename} to storage")
            
        # Save to DB
        att = await AttachmentRepository.create(
            entity_type=entity_type,
            entity_id=entity_id,
            attachment_type=attachment_type,
            file_key=file_key,
            file_name=file.filename,
            file_size=size,
            mime_type=mime,
            db=db
        )
        
        # Get presigned URL for response
        url = await StorageService.get_presigned_url(file_key)
        
        responses.append({
            "id": att.id,
            "entity_type": att.entity_type,
            "entity_id": att.entity_id,
            "attachment_type": att.attachment_type,
            "file_name": att.file_name,
            "file_size": att.file_size,
            "mime_type": att.mime_type,
            "url": url,
            "created_at": att.created_at.isoformat() if att.created_at else ""
        })
        
    logger.info(f"[WEBAPP:ATTACHMENTS] uploaded {len(files)} files for {entity_type}:{entity_id} by admin={admin.id}")
    return responses

@router.get("/{entity_type}/{entity_id}", response_model=List[AttachmentResponse])
async def get_attachments(
    entity_type: str,
    entity_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    if entity_type not in ["topic", "question"]:
        raise HTTPException(400, "Invalid entity_type")
        
    attachments = await AttachmentRepository.get_for_entity(entity_type, entity_id, db)
    
    responses = []
    for att in attachments:
        url = await StorageService.get_presigned_url(att.file_key)
        responses.append({
            "id": att.id,
            "entity_type": att.entity_type,
            "entity_id": att.entity_id,
            "attachment_type": att.attachment_type,
            "file_name": att.file_name,
            "file_size": att.file_size,
            "mime_type": att.mime_type,
            "url": url,
            "created_at": att.created_at.isoformat() if att.created_at else ""
        })
        
    return responses

@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    att = await AttachmentRepository.get_by_id(attachment_id, db)
    if not att:
        raise HTTPException(404, "Attachment not found")
        
    # Delete from S3
    deleted_from_storage = await StorageService.delete_file(att.file_key)
    if not deleted_from_storage:
        logger.warning(
            f"[FIX][WEBAPP:ATTACHMENTS] storage_delete_failed attachment_id={attachment_id} file_key={att.file_key}"
        )
    
    # Delete from DB even if S3 delete failed (it might be missing in S3)
    await AttachmentRepository.delete(attachment_id, db)
    
    logger.info(f"[WEBAPP:ATTACHMENTS] deleted attachment {attachment_id} file_key={att.file_key} by admin={admin.id}")
    return {"status": "deleted"}
