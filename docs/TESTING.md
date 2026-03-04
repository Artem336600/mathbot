# Testing Guide — MathTrainer

This project uses a testing pyramid strategy to ensure reliability while maintaining fast feedback loops.

## Testing Strategy

1.  **Unit Tests (Fastest):** Direct logic testing of services (`services/`) using an in-memory SQLite database.
2.  **Integration Tests (Medium):** Testing Telegram handlers (`bot/handlers/`) using Aiogram mocks and the in-memory DB.
3.  **API Integration Tests (Solid):** Testing the FastAPI WebApp endpoints (`webapp/routers/`) using `httpx.AsyncClient` and mocked dependencies.

## Setup

Tests use `pytest` with the following key plugins:
- `pytest-asyncio`: For `async def` tests.
- `aiosqlite`: For the in-memory database.
- `pytest-mock`: For mocking internal components (Redis, Bot).

## Running Tests

### All Tests
```bash
pytest
```

### Run Specific Layer
```bash
# Services only
pytest tests/services/

# Bot Handlers only
pytest tests/bot/handlers/

# WebApp API only
pytest tests/webapp/
```

### Verbose with Logs
```bash
pytest -v -s
```

### Coverage Report
```bash
pytest --cov=. --cov-report=html
```

## Writing New Tests

### 1. Using Domain Factories
Always use `tests/factories.py` to create test data. It ensures that models are populated with valid defaults:
```python
from tests.factories import create_user, create_question

user = create_user(id=123, xp=100)
q = create_question(topic_id=5)
```

### 2. Testing Bot Handlers
Handlers require mocking the `Message` or `CallbackQuery` and the `Database session`. Use the fixtures provided in `tests/bot/handlers/conftest.py`:
```python
@pytest.mark.asyncio
async def test_my_handler(mock_message, db):
    await my_handler(mock_message, db)
    assert mock_message.answer.called
```

### 3. Testing WebApp API
Use `authed_client` fixture to simulate a logged-in administrator. It uses a dev backdoor `test_dev={uid}` to bypass Telegram signature checks in test environments.
```python
@pytest.mark.asyncio
async def test_my_api(authed_client):
    resp = await authed_client.get("/api/my-endpoint")
    assert resp.status_code == 200
```

## Database for Tests
We use `sqlite+aiosqlite:///:memory:` for tests. 
- Tables are created automatically before each test.
- Every test is completely isolated with a fresh database.
- Redis is mocked via `mock_redis` fixture in `conftest.py`.

## Continuous Integration
Tests are automatically run on every Pull Request via GitHub Actions. A failure in any test prevents merging.
