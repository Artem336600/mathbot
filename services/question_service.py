"""Question service — question selection and adaptive difficulty logic."""
import random

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Question
from repositories.question_repo import QuestionRepository

SPRINT_EASY = 5
SPRINT_MEDIUM = 6
SPRINT_HARD = 4
SPRINT_TOTAL = SPRINT_EASY + SPRINT_MEDIUM + SPRINT_HARD  # 15


async def get_sprint_questions(
    topic_ids: list[int] | None, db: AsyncSession
) -> list[int]:
    """
    Get 15 questions for sprint: 5 easy + 6 medium + 4 hard.
    Returns list of question IDs (shuffled).
    """
    all_topic_ids = topic_ids or []
    if not all_topic_ids:
        # Use all topics if none specified
        from repositories.topic_repo import TopicRepository
        topics = await TopicRepository.get_all(db)
        all_topic_ids = [t.id for t in topics]

    easy = await QuestionRepository.get_by_difficulty(all_topic_ids, 1, SPRINT_EASY, db)
    medium = await QuestionRepository.get_by_difficulty(all_topic_ids, 2, SPRINT_MEDIUM, db)
    hard = await QuestionRepository.get_by_difficulty(all_topic_ids, 3, SPRINT_HARD, db)

    questions = easy + medium + hard
    random.shuffle(questions)

    ids = [q.id for q in questions]
    logger.info(f"[SVC:Question] Sprint: {len(ids)} questions (e={len(easy)},m={len(medium)},h={len(hard)})")
    return ids


async def get_next_training_question(
    session: dict, db: AsyncSession
) -> Question | None:
    """
    Adaptive: select question matching current difficulty from session.
    Avoids repeating current question.
    """
    topic_ids = session.get("topic_ids", [])
    difficulty = session.get("difficulty", 1)
    exclude_id = session.get("current_question_id")

    candidates = await QuestionRepository.get_by_difficulty(topic_ids, difficulty, 10, db)

    # Filter out current question
    if exclude_id and len(candidates) > 1:
        candidates = [q for q in candidates if q.id != exclude_id]

    if not candidates:
        # Fallback: get any question
        candidates = await QuestionRepository.get_random(topic_ids, 5, db)

    if not candidates:
        return None

    question = random.choice(candidates)
    logger.debug(f"[SVC:Question] Next training q={question.id} difficulty={difficulty}")
    return question
