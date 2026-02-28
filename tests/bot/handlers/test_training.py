import pytest
import json
from unittest.mock import AsyncMock
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from bot.handlers.training import training_begin, training_answer
from tests.factories import create_user, create_topic, create_question

@pytest.mark.asyncio
async def test_training_begin(mock_callback_query: CallbackQuery, db: AsyncSession, mock_redis):
    # Setup
    user = create_user(id=1)
    topic = create_topic(id=10, title="Math Training")
    db.add_all([user, topic])
    await db.commit()

    q = create_question(topic_id=10, text="Q Train", difficulty=1)
    db.add(q)
    await db.commit()

    # Mock Redis temp storage for topic selection
    mock_redis.get.return_value = json.dumps({"selected": [10]})
    
    # Action
    await training_begin(mock_callback_query, db)

    # Assert
    # Session created
    assert mock_redis.setex.called
    # Check session data (should contain topics and current question)
    # The last call to setex should be the session update
    last_call = mock_redis.setex.call_args_list[-1]
    session_json = last_call.args[2]
    session = json.loads(session_json)
    assert session["topic_ids"] == [10]
    assert session["current_question_id"] == q.id

@pytest.mark.asyncio
async def test_training_answer_adaptive_difficulty(mock_callback_query: CallbackQuery, db: AsyncSession, mock_redis):
    # Setup
    user = create_user(id=1)
    topic = create_topic(id=11, title="Math Training 2")
    db.add_all([user, topic])
    await db.commit()

    q1 = create_question(topic_id=11, text="Q Easy", difficulty=1, correct_option="a")
    q2 = create_question(topic_id=11, text="Q Medium", difficulty=2)
    db.add_all([q1, q2])
    await db.commit()

    # Mock Session
    session_data = {
        "topic_ids": [11],
        "difficulty": 1,
        "current_question_id": q1.id,
        "solved_count": 0,
        "xp_earned": 0
    }
    mock_redis.get.return_value = json.dumps(session_data)
    mock_callback_query.data = "train_ans:a"

    # Action: Correct answer on 1 difficulty
    await training_answer(mock_callback_query, db, user)

    # Assert: difficulty should increase to 2
    last_call = mock_redis.setex.call_args_list[-1]
    updated_session = json.loads(last_call.args[2])
    assert updated_session["difficulty"] == 2
    assert updated_session["solved_count"] == 1
    
    # Check XP awarded
    await db.refresh(user)
    assert user.xp == 10

@pytest.mark.asyncio
async def test_training_answer_db_error_handling(mock_callback_query: CallbackQuery, db: AsyncSession, mock_redis, mocker):
    # Setup
    user = create_user(id=1)
    topic = create_topic(id=12, title="Math Training Fail")
    db.add_all([user, topic])
    await db.commit()

    q = create_question(topic_id=12, text="Q Fail")
    db.add(q)
    await db.commit()

    session_data = {
        "topic_ids": [12],
        "difficulty": 1,
        "current_question_id": q.id,
        "solved_count": 0
    }
    mock_redis.get.return_value = json.dumps(session_data)
    mock_callback_query.data = "train_ans:a" # any answer

    # Mock ProgressRepository.add to raise error
    mocker.patch("repositories.progress_repo.ProgressRepository.add", side_effect=IntegrityError("stmt", "params", "orig"))

    # Action & Assert
    # We expect the exception to propagate (so it can be caught by global error handler)
    with pytest.raises(IntegrityError):
        await training_answer(mock_callback_query, db, user)
