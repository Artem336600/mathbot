import pytest
import json
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import UploadFile
from webapp.routers.questions import import_questions
from pydantic import ValidationError

# Strategies to generate valid and invalid JSON structures
primitive = st.one_of(st.none(), st.booleans(), st.integers(), st.floats(), st.text())
json_st = st.recursive(
    primitive,
    lambda children: st.one_of(st.lists(children), st.dictionaries(st.text(), children)),
    max_leaves=10
)

@pytest.mark.asyncio
@given(json_data=json_st)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_import_questions_fuzz(db, json_data):
    # Mock repositories
    with patch("webapp.routers.questions.TopicRepository") as mock_t_repo, \
         patch("webapp.routers.questions.QuestionRepository") as mock_q_repo, \
         patch("webapp.routers.questions.get_admin_user") as mock_admin:
        
        # Admin is needed for the Depends, but we are calling the function directly
        mock_admin.return_value = MagicMock(id=1)
        mock_t_repo.get = AsyncMock(return_value=MagicMock(id=1))
        mock_q_repo.bulk_create = AsyncMock(return_value=5)
        
        # Prepare mock file
        content = json.dumps(json_data).encode("utf-8")
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.json"
        mock_file.read = AsyncMock(return_value=content)
        
        try:
            # We call the function directly. In FastAPI, Depends would be resolved earlier.
            # We pass mocks for db and admin manually.
            response = await import_questions(
                topic_id=1,
                file=mock_file,
                admin=mock_admin.return_value,
                db=db
            )
            
            # Assertions: the service should not CRASH. 
            # It should return either a success dict or a validation error dict.
            assert isinstance(response, dict)
            assert "status" in response or response.get("status") in ["success", "partial", "error"]
            
        except Exception as e:
            # If it's a known FastAPI/Pydantic error, it's fine.
            # But we want to avoid internal server errors or unhandled exceptions.
            from fastapi import HTTPException
            if not isinstance(e, (HTTPException, ValidationError)):
                raise e
