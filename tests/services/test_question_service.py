import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from services.question_service import get_next_training_question, get_sprint_questions
from tests.factories import create_topic, create_question

@pytest.mark.asyncio
async def test_get_next_training_question_deduplication(db: AsyncSession):
    # Setup
    topic = create_topic(title="Math")
    db.add(topic)
    await db.commit()

    # Create two questions in same topic and same difficulty
    q1 = create_question(topic_id=topic.id, text="Q1", difficulty=1)
    q2 = create_question(topic_id=topic.id, text="Q2", difficulty=1)
    db.add_all([q1, q2])
    await db.commit()

    # Action 1: First question
    session_data = {"topic_ids": [topic.id], "difficulty": 1}
    first_q = await get_next_training_question(session_data, db)
    
    assert first_q is not None
    assert first_q.id in [q1.id, q2.id]

    # Action 2: Second question, passing current_question_id
    session_data["current_question_id"] = first_q.id
    second_q = await get_next_training_question(session_data, db)

    assert second_q is not None
    # We should get the OTHER question (deduplicated)
    assert second_q.id != first_q.id

@pytest.mark.asyncio
async def test_get_sprint_questions(db: AsyncSession):
    # Setup
    topic = create_topic(title="Math Sprint")
    db.add(topic)
    await db.commit()

    for i in range(15):
        diff = 1 if i < 5 else 2 if i < 11 else 3
        q = create_question(topic_id=topic.id, text=f"Q{i}", difficulty=diff)
        db.add(q)
    await db.commit()

    # Action
    ids = await get_sprint_questions([topic.id], db)

    # Assert
    assert len(ids) == 15
    assert len(set(ids)) == 15 # all unique

