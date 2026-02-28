"""Questions CRUD API for Admin Dashboard."""
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from webapp.auth import get_admin_user, get_db_session
from db.models import User
from webapp.schemas import QuestionCreate, QuestionUpdate, QuestionResponse
from repositories.question_repo import QuestionRepository
from repositories.topic_repo import TopicRepository
from loguru import logger

router = APIRouter(prefix="/api/questions", tags=["questions"])

@router.get("/", response_model=List[QuestionResponse])
async def get_questions(
    topic_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get questions for a specific topic."""
    questions = await QuestionRepository.get_by_topic(topic_id, db)
    return questions

@router.post("/", response_model=QuestionResponse)
async def create_question(
    payload: QuestionCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    topic = await TopicRepository.get(payload.topic_id, db)
    if not topic:
        raise HTTPException(404, "Topic not found")
        
    try:
        q = await QuestionRepository.create(
            topic_id=payload.topic_id,
            text=payload.text,
            option_a=payload.option_a,
            option_b=payload.option_b,
            option_c=payload.option_c,
            option_d=payload.option_d,
            correct_option=payload.correct_option,
            difficulty=payload.difficulty,
            explanation=payload.explanation,
            image_url=payload.image_url,
            db=db
        )
        logger.info(f"[WEBAPP:QUESTIONS] Created question {q.id} in topic {payload.topic_id} by admin={admin.id}")
        return q
    except Exception as e:
        logger.error(f"Error creating question: {e}")
        raise HTTPException(400, "Failed to create question")

@router.patch("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    payload: QuestionUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    q = await QuestionRepository.get_by_id(question_id, db)
    if not q:
        raise HTTPException(404, "Question not found")
        
    update_data = {k: v for k, v in payload.dict(exclude_unset=True).items()}
    if not update_data:
        return q
        
    try:
        updated = await QuestionRepository.update(question_id, db, **update_data)
        logger.info(f"[WEBAPP:QUESTIONS] Updated question {question_id} by admin={admin.id}")
        return updated
    except Exception as e:
        logger.error(f"Error updating question: {e}")
        raise HTTPException(400, "Failed to update question")

@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    deleted = await QuestionRepository.delete(question_id, db)
    if not deleted:
        raise HTTPException(404, "Question not found")
    logger.info(f"[WEBAPP:QUESTIONS] Deleted question {question_id} by admin={admin.id}")
    return {"status": "deleted"}

@router.post("/import")
async def import_questions(
    topic_id: int = Form(...),
    file: UploadFile = File(...),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Import questions from a JSON file."""
    if not file.filename.endswith('.json'):
        raise HTTPException(400, "Only JSON files are supported")
        
    topic = await TopicRepository.get(topic_id, db)
    if not topic:
        raise HTTPException(404, "Topic not found")
        
    content = await file.read()
    try:
        data = json.loads(content)
    except Exception:
        raise HTTPException(400, "Invalid JSON format")
        
    if not isinstance(data, list):
        raise HTTPException(400, "JSON must be an array of questions")
        
    errors = []
    valid_data = []
    
    for idx, item in enumerate(data):
        try:
            # We use the QuestionCreate schema to validate each row
            item["topic_id"] = topic_id # force topic_id
            validated = QuestionCreate(**item)
            valid_data.append(validated.dict())
        except ValidationError as e:
            # Extract error summary
            error_msg = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in e.errors()])
            errors.append(f"Row {idx+1}: {error_msg}")
            
    if not valid_data and errors:
        return {"status": "error", "message": "All rows are invalid", "errors": errors}
        
    try:
        count = await QuestionRepository.bulk_create(valid_data, topic_id, db)
        logger.info(f"[WEBAPP:QUESTIONS] Imported {count} questions to topic {topic_id} by admin={admin.id}")
        return {
            "status": "partial" if errors else "success",
            "imported": count,
            "errors": errors
        }
    except Exception as e:
        logger.error(f"Error in bulk insert: {e}")
        raise HTTPException(400, "Database error during import")
