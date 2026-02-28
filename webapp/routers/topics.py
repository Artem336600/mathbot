"""Topics CRUD API for Admin Dashboard."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from webapp.auth import get_admin_user, get_db_session
from db.models import User, Topic, Question
from webapp.schemas import TopicCreate, TopicUpdate, TopicResponse
from repositories.topic_repo import TopicRepository
from loguru import logger

router = APIRouter(prefix="/api/topics", tags=["topics"])

@router.get("/", response_model=List[TopicResponse])
async def get_topics(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get all topics with question counts."""
    topics = await TopicRepository.get_all(db)
    
    # We also need questions count per topic. 
    # For MVP we can do it with an aggregate query, but TopicRepository.get_all is already cached or neat
    # Let's count via group by
    stmt = select(Topic.id, func.count(Question.id)).outerjoin(Question).group_by(Topic.id)
    counts = dict((await db.execute(stmt)).all())
    
    result = []
    for t in topics:
        result.append({
            "id": t.id,
            "title": t.title,
            "theory_text": t.theory_text,
            "image_url": t.image_url,
            "is_active": t.is_active,
            "questions_count": counts.get(t.id, 0)
        })
        
    return result

@router.post("/", response_model=TopicResponse)
async def create_topic(
    payload: TopicCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    logger.info(f"[WEBAPP:TOPICS] Creating topic '{payload.title}' by admin={admin.id}")
    try:
        topic = await TopicRepository.create(
            title=payload.title,
            theory_text=payload.theory_text,
            image_url=payload.image_url,
            db=db
        )
        # also set active
        if not payload.is_active:
            topic.is_active = False
            await db.commit()
            
        return dict(
            id=topic.id,
            title=topic.title,
            theory_text=topic.theory_text,
            image_url=topic.image_url,
            is_active=topic.is_active,
            questions_count=0
        )
    except Exception as e:
        logger.error(f"[WEBAPP:TOPICS] Error: {e}")
        raise HTTPException(status_code=400, detail="Topic already exists or DB Error")

@router.patch("/{topic_id}")
async def update_topic(
    topic_id: int,
    payload: TopicUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    topic = await TopicRepository.get(topic_id, db)
    if not topic:
        raise HTTPException(404, "Topic not found")
        
    update_data = {k: v for k, v in payload.dict(exclude_unset=True).items()}
    if not update_data:
        return {"status": "ok"}
        
    try:
        updated = await TopicRepository.update(topic_id, db, **update_data)
        logger.info(f"[WEBAPP:TOPICS] Updated topic {topic_id} by admin={admin.id}")
        return {"status": "ok", "id": updated.id}
    except Exception as e:
        logger.error(f"Error updating topic: {e}")
        raise HTTPException(400, "Failed to update topic")

@router.patch("/{topic_id}/toggle")
async def toggle_topic(
    topic_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    topic = await TopicRepository.get(topic_id, db)
    if not topic:
        raise HTTPException(404, "Topic not found")
        
    topic.is_active = not topic.is_active
    await db.commit()
    logger.info(f"[WEBAPP:TOPICS] Toggled topic {topic_id} active={topic.is_active} by admin={admin.id}")
    return {"status": "ok", "is_active": topic.is_active}

@router.delete("/{topic_id}")
async def delete_topic(
    topic_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    from repositories.attachment_repo import AttachmentRepository
    from services.storage_service import StorageService
    
    file_keys = await AttachmentRepository.delete_all_for_entity("topic", topic_id, db)
    for key in file_keys:
        await StorageService.delete_file(key)
        
    deleted = await TopicRepository.delete(topic_id, db)
    if not deleted:
        raise HTTPException(404, "Topic not found")
    logger.info(f"[WEBAPP:TOPICS] Deleted topic {topic_id} by admin={admin.id}")
    return {"status": "deleted"}
