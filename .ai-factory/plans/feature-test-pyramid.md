# Plan: Test Pyramid Implementation

**Branch:** `feature/test-pyramid`
**Creation Date:** 2026-03-01

## Settings
- **Testing:** Yes (This feature IS test creation)
- **Logging:** Verbose (Use extensive logging in tests & mocks to catch issues)
- **Docs:** Yes (Add testing guide to `docs/` or `README.md` on how to run them)

## Tasks

### Phase 1: Test Infrastructure & Fixtures (aiosqlite)
- [x] **Task 1: Setup Core Fixtures with aiosqlite**
  - **File:** `tests/conftest.py`
  - **Action:** 
    - Create a global `pytest` fixture for tests that sets up an asynchronous in-memory SQLite database (`sqlite+aiosqlite:///:memory:`).
    - Before each test, run `Base.metadata.create_all` to generate the schema.
    - Create a session fixture that yields an `AsyncSession` using `async_sessionmaker`.
    - Create a fixture for `Redis` mocking (using `pytest-mock` or a library like `fakeredis` if available, or just mocking `SessionService`).
  - **Checklist:**
    - [x] DB engine uses `aiosqlite`.
    - [x] Tables are created/dropped between tests to ensure a clean slate.
    - [x] Setup loguru logging capture for tests if necessary.

- [x] **Task 2: Implement Domain Data Factories / Seeders**
  - **File:** `tests/factories.py` (New file)
  - **Action:** Create helper functions to quickly populate the mock DB during tests (e.g., `create_user()`, `create_topic()`, `create_question()`, `create_mistake()`).
  - **Checklist:**
    - [x] Support overriding default values (e.g., `create_user(xp=95)`).

### Phase 2: Unit Tests (Services Layer)
- [x] **Task 3: Test Stats Service (XP & Level progression)**
  - **File:** `tests/bot/services/test_stats_service.py`
  - **Action:** Test `award_xp` logic using in-memory DB.
  - **Checklist:**
    - [x] Verify standard XP gain.
    - [x] Verify streak logic (if applicable).
    - [x] Verify Level Up triggers precisely on threshold boundaries (`0->99` vs `100`).

- [x] **Task 4: Test Question Service (Adaptive difficulty)**
  - **File:** `tests/bot/services/test_question_service.py`
  - **Action:** Test logic for getting the next question and adjusting difficulty based on success/failure.
  - **Checklist:**
    - [x] Difficulty increases (+1) on correct answer, decreases on wrong answer (bound by min/max).
    - [x] History is tracked (deduplication of questions returned in a session).

- [x] **Task 5: Test Mistake Service**
  - **File:** `tests/bot/services/test_mistake_service.py`
  - **Action:** Test error tracking logic.
  - **Checklist:**
    - [x] Mistake is saved in DB.
    - [x] If mistake already exists, `attempts` counter increments.
    - [x] Mistake is marked as resolved upon correct answer.

### Commit Checkpoint 1
- **Message:** `test: add aiosqlite test infrastructure and service layer logic coverage`

### Phase 3: Integration Tests (Handlers Layer via Mocks)
- [x] **Task 6: Setup Aiogram Mocks**
  - **File:** `tests/bot/handlers/conftest.py` (New file)
  - **Action:** Add fixtures for mocking `Message`, `CallbackQuery`, and `Bot` instances so we can pass them into handlers.

- [x] **Task 7: Test Sprint Mode Handler Flow**
  - **File:** `tests/bot/handlers/test_sprint.py`
  - **Action:** Test `bot/handlers/sprint.py`. Verify that the callback handler starts a session and returns a question keyboard.
  - **Checklist:**
    - [x] Call `start_sprint` directly with a fake `CallbackQuery` and mock `db`.
    - [x] Assert `callback.message.edit_text` was called with expected question string.
    - [x] Assert `SessionService.create_sprint_session` is called or simulated correctly.

- [x] **Task 8: Test Training Mode Handler Flow & Error Recovery**
  - **File:** `tests/bot/handlers/test_training.py`
  - **Action:** Test `bot/handlers/training.py`. Specifically check edge cases like DB failures.
  - **Checklist:**
    - [x] Mock `db.commit()` to raise an `IntegrityError` to simulate a DB crash.
    - [x] Assert the handler gracefully catches the error (if global exception handler or try/except is used) or logs it properly without exploding silently.

### Commit Checkpoint 2
- [x] **Message:** `test: add integration tests for sprint/training handlers`

### Phase 4: Integration Tests (FastAPI WebApp Layer)
- [x] **Task 9: Fix & Enhance Authentication API Tests**
  - **File:** `tests/webapp/test_auth.py`
  - **Action:** Ensure existing auth tests are passing with the active SQLite mock db context and check edge cases. Add a test for a banned user trying to hit an API endpoint if applicable.

- [x] **Task 10: Test Admin Broadcast/Upload Endpoints**
  - **File:** `tests/webapp/test_admin_api.py` (New file or integrate to existing)
  - **Action:** Test importing a payload JSON for new topics/questions (e.g. simulate a POST request with invalid JSON -> verify `400 Bad Request`).
  - **Checklist:**
    - [x] Verify validation errors on broken JSON.
    - [x] Verify successful import writes safely to the mock database.

### Phase 5: Documentation
- [x] **Task 11: Add Testing Guide to documentation**
  - **File:** `docs/TESTING.md`
  - **Action:** Document how to run pytest locally, how the SQLite mocking works, and how to write new handler tests.
  - **Checklist:**
    - [x] Explain `pytest --cov` syntax.
    - [x] Document the `fake_bot` and `aiosqlite` mock DB principles.

### Final Commit
- [x] **Message:** `test: complete integration testing for webapp API and finalize test guides`
