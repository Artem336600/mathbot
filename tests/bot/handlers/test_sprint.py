import pytest
import json
from unittest.mock import AsyncMock
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.sprint import sprint_go, sprint_answer
from tests.factories import create_user, create_topic, create_question

@pytest.mark.asyncio
async def test_sprint_go(mock_callback_query: CallbackQuery, db: AsyncSession, mock_redis):
    # Setup
    user = create_user(id=1)
    topic = create_topic(title="Math Sprint")
    db.add_all([user, topic])
    await db.commit()

    # Create 15 questions to simulate full sprint
    for i in range(15):
        diff = 1 if i < 5 else 2 if i < 11 else 3
        q = create_question(topic_id=topic.id, text=f"Q{i}", difficulty=diff)
        db.add(q)
    await db.commit()

    # Action
    await sprint_go(mock_callback_query, db, user)

    # Assert
    # 1. Redis setex was called to store session (at least twice: create and update in _show_question)
    assert mock_redis.setex.called
    
    # 2. Check payload sent to string
    # We simply check that mock_callback_query.message.answer or edit_text got called with the question text
    assert mock_callback_query.message.edit_text.called or mock_callback_query.message.answer.called or mock_callback_query.message.answer_photo.called

@pytest.mark.asyncio
async def test_sprint_answer_correct(mock_callback_query: CallbackQuery, db: AsyncSession, mock_redis):
    # Setup
    user = create_user(id=1)
    topic = create_topic(title="Math Sprint 2")
    db.add_all([user, topic])
    await db.commit()

    q1 = create_question(topic_id=topic.id, text="Q Test1", correct_option="a")
    db.add(q1)
    await db.commit()

    # Mock the callback data
    mock_callback_query.data = "sprint_ans:a"

    # Mock Redis payload to return a proper session
    session_data = {
        "questions": [q1.id],
        "current_idx": 0,
        "correct_count": 0,
        "total": 1
    }
    # get_redis().get(...)
    mock_redis.get.return_value = json.dumps(session_data)

    # Action
    await sprint_answer(mock_callback_query, db, user)

    # Assert
    # The sprint finishes (current_idx == total), so session is deleted
    mock_redis.delete.assert_called_once_with(f"sprint:1")
    
    # Check that user received XP bonus
    await db.refresh(user)
    # XP Correct (10) + XP Sprint Bonus (50) = 60
    assert user.xp == 60

    # User progress checked
    assert mock_callback_query.answer.called
