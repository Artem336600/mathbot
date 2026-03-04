import pytest
import random
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import AsyncMock, patch
from services.question_service import get_sprint_questions, get_next_training_question
from db.models import Question

# Strategies
topic_ids_st = st.lists(st.integers(min_value=1, max_value=100), min_size=0, max_size=10)
difficulty_st = st.integers(min_value=-10, max_value=10)
session_st = st.fixed_dictionaries({
    "topic_ids": topic_ids_st,
    "difficulty": difficulty_st,
    "current_question_id": st.one_of(st.none(), st.integers(min_value=1, max_value=1000))
})

@pytest.mark.asyncio
@given(topic_ids=topic_ids_st)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_get_sprint_questions_fuzz(db, topic_ids):
    # Use direct patch instead of mocker fixture for hypothesized tests if possible
    with patch("services.question_service.QuestionRepository") as mock_q_repo, \
         patch("repositories.topic_repo.TopicRepository") as mock_t_repo, \
         patch("services.question_service.random.shuffle") as mock_shuffle:
        
        # Setup mock behavior
        mock_q_repo.get_by_difficulty = AsyncMock(return_value=[AsyncMock(id=i) for i in range(5)])
        mock_t_repo.get_all = AsyncMock(return_value=[AsyncMock(id=1), AsyncMock(id=2)])
        
        # Action
        ids = await get_sprint_questions(topic_ids, db)
        
        # Assert
        assert isinstance(ids, list)
        assert len(ids) <= 15

@pytest.mark.asyncio
@given(session=session_st, num_results=st.integers(min_value=0, max_value=5))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_get_next_training_question_fuzz(db, session, num_results):
    with patch("services.question_service.QuestionRepository") as mock_repo, \
         patch("services.question_service.random.choice") as mock_choice:
        
        mock_results = [AsyncMock(id=i) for i in range(num_results)]
        mock_repo.get_by_difficulty = AsyncMock(return_value=mock_results)
        mock_repo.get_random = AsyncMock(return_value=mock_results)
        mock_choice.side_effect = lambda x: x[0] if x else None
        
        # Action
        question = await get_next_training_question(session, db)
        
        # Assert
        if num_results == 0:
            assert question is None
        else:
            assert question is not None
