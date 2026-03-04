import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import UserMistake, Question
from sqlalchemy import select
from services.mistake_service import add_mistake, get_mistakes, fix_mistake
from tests.factories import create_user, create_topic, create_question

@pytest.mark.asyncio
async def test_add_mistake_deduplication(db: AsyncSession):
    # Setup
    user = create_user(id=1)
    topic = create_topic(title="Math")
    db.add_all([user, topic])
    await db.commit()

    q = create_question(topic_id=topic.id, text="Q1")
    db.add(q)
    await db.commit()

    # Action 1: Add first mistake
    await add_mistake(1, q.id, db)
    
    # Verify
    mistakes = await get_mistakes(1, None, db)
    assert len(mistakes) == 1

    # Action 2: Add same mistake again
    await add_mistake(1, q.id, db)
    
    # Verify no duplication
    mistakes_after = await get_mistakes(1, None, db)
    assert len(mistakes_after) == 1

@pytest.mark.asyncio
async def test_fix_mistake(db: AsyncSession):
    # Setup
    user = create_user(id=2)
    topic = create_topic(title="Math 2")
    db.add_all([user, topic])
    await db.commit()

    q = create_question(topic_id=topic.id, text="Q1")
    db.add(q)
    await db.commit()

    await add_mistake(2, q.id, db)
    mistakes = await get_mistakes(2, None, db)
    assert len(mistakes) == 1
    m_id = mistakes[0].id

    # Action: Fix mistake
    success = await fix_mistake(m_id, 2, db)
    
    # Assert
    assert success is True
    
    # Should no longer be returned as active
    active_mistakes = await get_mistakes(2, None, db)
    assert len(active_mistakes) == 0

    # DB record is updated
    db_mistake = await db.get(UserMistake, m_id)
    assert db_mistake.is_fixed is True
