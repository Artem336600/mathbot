"""Stats router for Admin Dashboard."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from webapp.auth import get_admin_user, get_db_session
from db.models import User, Topic, Question, UserProgress
from repositories.user_repo import UserRepository
from repositories.topic_repo import TopicRepository
from loguru import logger

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("/")
async def get_dashboard_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get aggregated stats for the admin dashboard."""
    logger.debug(f"[WEBAPP:STATS] Dashboard requested by admin={admin.id}")
    
    # User stats
    total_users = await UserRepository.count_all(db)
    banned_users = await UserRepository.count_banned(db)
    # Active inside last 7 days? Or total active (not banned). We will use simple total-banned for 'active'
    active_users = total_users - banned_users
    
    # Topic & Questions stats
    topics = await TopicRepository.get_all(db)
    total_topics = len(topics)
    
    q_result = await db.execute(select(func.count(Question.id)))
    total_questions = q_result.scalar() or 0
    
    # Progress (answers)
    ans_result = await db.execute(select(func.count(UserProgress.id)))
    total_answers = ans_result.scalar() or 0
    
    # Answers today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    ans_today_result = await db.execute(
        select(func.count(UserProgress.id)).where(UserProgress.answered_at >= today_start)
    )
    answers_today = ans_today_result.scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "banned_users": banned_users,
        "total_topics": total_topics,
        "total_questions": total_questions,
        "total_answers": total_answers,
        "answers_today": answers_today
    }
