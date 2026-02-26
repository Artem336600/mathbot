# Plan: MathTrainer MVP — Telegram Bot

**Branch:** `feature/mathtrainer-mvp`
**Created:** 2026-02-27
**Description:** Создать Telegram-бота MathTrainer на Python/Aiogram 3 с режимами Спринт, Тренировка, Каталог тем, Работа над ошибками, Профиль и Админкой.

## Settings

- **Testing:** No tests
- **Logging:** Verbose (loguru, LOG_LEVEL через env, DEBUG по умолчанию)
- **Docs:** Skip
- **Architecture:** Layered (handlers → services → repositories → db)

---

## Phase 1: Фундамент (Infrastructure & DB)

- [x] **Task 1: Настройка структуры проекта и зависимостей**
  - Создать структуру папок согласно ARCHITECTURE.md
  - Файлы: `requirements.txt`, `.env.example`, `bot/config.py`, `bot/__init__.py` и все `__init__.py`-пакеты
  - `requirements.txt` включает: aiogram==3.x, sqlalchemy[asyncio], asyncpg, alembic, redis, loguru, pydantic-settings, python-dotenv
  - `bot/config.py`: `class Settings(BaseSettings)` с полями BOT_TOKEN, DATABASE_URL, REDIS_URL, LOG_LEVEL, ADMIN_IDS
  - Логирование: настроить loguru в `bot/main.py` с LOG_LEVEL из env
  - Logging: `[BOOT] Config loaded: db={settings.DATABASE_URL[:20]}...`

- [x] **Task 2: SQLAlchemy модели (db/models.py)**
  - Создать `db/models.py` со всеми ORM-моделями:
    - `User`: id (tg_id), username, first_name, xp, level, streak_days, last_active, accuracy_rate, is_admin, is_banned, created_at
    - `Topic`: id, title, theory_text, is_active
    - `Question`: id, topic_id (FK), text, image_url (nullable), difficulty (1/2/3), option_a/b/c/d, correct_option (a/b/c/d), explanation
    - `UserMistake`: id, user_id (FK), question_id (FK), is_fixed, created_at
    - `UserProgress`: id, user_id (FK), question_id (FK), is_correct, answered_at
  - Создать `db/session.py`: async_engine, async_session_factory (AsyncSession)
  - Logging: `[DB] Engine created for: {url}`

- [x] **Task 3: Alembic + первая миграция**
  - Инициализировать alembic: `alembic init db/migrations`
  - Настроить `alembic.ini` и `db/migrations/env.py` для async (asyncpg), импорт моделей из `db/models`
  - Создать первую миграцию: `alembic revision --autogenerate -m "initial"`
  - Logging: описать в комментарии миграции что создаётся

- [x] **Task 4: Docker Compose окружение**
  - Создать `Dockerfile` (multi-stage: builder + runtime, python:3.12-slim)
  - Создать `docker-compose.yml`: сервисы `bot`, `postgres` (16-alpine), `redis` (7-alpine)
    - `bot` depends_on postgres и redis с healthcheck
    - volumes для postgres data persistence
    - `.env` файл как источник переменных
  - Создать `.env.example` с полями: BOT_TOKEN, DATABASE_URL, REDIS_URL, LOG_LEVEL=DEBUG, ADMIN_IDS
  - Logging: `[BOOT] Starting MathTrainer bot...`

- [x] **Task 5: Тестовый банк задач (data/seed.py)**
  - Создать `data/seed.py` — скрипт для наполнения БД начальными данными
  - **5 тем** с теорией: Дроби, Проценты, Уравнения, Геометрия (периметр/площадь), Степени и корни
  - **По 12 задач на тему** (4 easy, 4 medium, 4 hard), итого 60 задач
  - Каждая задача: текст + 4 варианта ответа (A/B/C/D) + верный вариант + краткое объяснение
  - Запуск: `python -m data.seed` (идемпотентно — не дублирует при повторном запуске)
  - Logging: `[SEED] Inserting topic: {title}`, `[SEED] Done: {n} questions inserted`

> 🔵 **Checkpoint 1** — commit: `feat(infra): add project structure, DB models, Docker and seed data`

---

## Phase 2: Ядро бота (Middlewares, Base, Navigation)

- [x] **Task 6: Middlewares и точка входа (bot/main.py)**
  - Создать `bot/middlewares/database.py`: `DatabaseMiddleware` — инъекция AsyncSession в `data["db"]`
  - Создать `bot/middlewares/user.py`: `UserMiddleware` — **обязательно после DatabaseMiddleware** — получает/создаёт пользователя через `user_repo.get_or_create()` и инъектирует в `data["user"]`. Порядок регистрации: 1) DatabaseMiddleware, 2) UserMiddleware, 3) BanCheckMiddleware
  - Создать `bot/middlewares/ban_check.py`: `BanCheckMiddleware` — использует `data["user"].is_banned` (уже инъектирован UserMiddleware), если True — отвечает «⛔ Вы заблокированы» и прерывает цепочку
  - Создать `bot/main.py`: создание `Bot`, `Dispatcher`, регистрация middlewares в правильном порядке (DB → User → Ban), заглушки для роутеров (реальная регистрация в Task 17), запуск `dp.start_polling(bot)`
  - Logging: `[MW:DB] Session opened`, `[MW:User] User {uid} fetched/created`, `[MW:BAN] Blocked user {uid}`

- [x] **Task 7: Репозитории (repositories/)**
  - Создать `repositories/user_repo.py`: `get_or_create(tg_id, username, first_name)`, `get(tg_id)`, `update(user)`, `get_all_ids()`
  - Создать `repositories/topic_repo.py`: `get_all()`, `get(id)`, `create(title, theory)`, `update(id, **kwargs)`, `delete(id)`
  - Создать `repositories/question_repo.py`: `get_by_topic(topic_id)`, `get_by_difficulty(topic_ids, difficulty, limit)`, `get_random(topic_ids, limit)`, `create(...)`, `update(id, **kwargs)`
  - Создать `repositories/mistake_repo.py`: `add(user_id, question_id)`, `get_all(user_id)`, `get_by_topic(user_id, topic_id)`, `mark_fixed(id)`, `count(user_id)`
  - Создать `repositories/progress_repo.py`: `add(user_id, question_id, is_correct)`, `get_accuracy(user_id)`
  - Logging: `[REPO:User] get_or_create tg_id={tg_id}`, `[REPO:Question] fetched {n} questions difficulty={d}`

- [x] **Task 8: Сервисы (services/)**
  - Создать `services/user_service.py`: `register_user(tg_id, username, first_name, db)` — регистрация или получение
  - Создать `services/stats_service.py`: `award_xp(user_id, amount, db)` → `{xp, level, level_up}`, `update_streak(user_id, db)`, `update_accuracy(user_id, db)`
  - Создать `services/session_service.py`: Redis-клиент; `create_sprint_session(user_id, questions)`, `get_session(user_id, mode)`, `update_session(user_id, mode, data)`, `delete_session(user_id, mode)`; ключи: `sprint:{user_id}`, `training:{user_id}`
    - **Формат Redis-сессии (JSON):**
      - Sprint: `{"questions": [id,...], "current_idx": 0, "correct_count": 0, "total": 15}`
      - Training: `{"topic_ids": [...], "difficulty": 1, "current_question_id": null, "solved_count": 0, "xp_earned": 0}`
  - Создать `services/question_service.py`: `get_sprint_questions(topic_ids, db)` → 15 вопросов (5 easy, 6 med, 4 hard), `get_next_training_question(session_data, db)` → с адаптивностью difficulty
  - Создать `services/mistake_service.py`: `add_mistake(user_id, question_id, db)`, `get_mistakes(user_id, topic_id, db)`, `fix_mistake(mistake_id, user_id, db)`
  - Создать `services/broadcast_service.py`: `send_to_all(text: str, bot: Bot, db) -> dict` — получает все user_ids через `user_repo.get_all_ids()`, отправляет каждому с задержкой `asyncio.sleep(0.05)`, считает `{sent: int, failed: int}`, обрабатывает `TelegramForbiddenError` (пользователь заблокировал бота) без остановки цикла
  - Logging: `[SVC:Stats] User {uid} +{xp}XP → total={total}, level={level}`, `[SVC:Session] Created sprint session {uid}: {n} questions`, `[SVC:Broadcast] Sending to {n} users`, `[SVC:Broadcast] Progress {sent}/{total}`, `[SVC:Broadcast] Done: sent={sent} failed={failed}`

- [x] **Task 9: Клавиатуры и Reply Navigation (keyboards/)**
  - Создать `bot/keyboards/reply.py`: `main_reply_keyboard()` — Reply Keyboard с кнопками «🏠 Меню» и «👤 Профиль»
  - Создать `bot/keyboards/main_menu.py`: `main_menu_keyboard()` — Inline с кнопками: 🚀 Спринт, 🏋️ Тренировка, 📚 Темы, ❌ Мои ошибки, 👤 Профиль
  - Создать `bot/handlers/start.py`: router, хендлер `/start` (регистрирует пользователя через `user_service`, показывает главное меню), хендлер `«🏠 Меню»` (Reply), callback `main_menu`
  - Logging: `[HANDLER:start] User {uid} registered/found`

> 🔵 **Checkpoint 2** — commit: `feat(core): add middlewares, repos, services, keyboards and /start`

---

## Phase 3: Режим Спринт (US-002)

- [x] **Task 10: FSM и хендлеры Спринта (bot/handlers/sprint.py)**
  - Создать `bot/fsm/sprint.py`: `class SprintState(StatesGroup): in_progress = State()`
  - Создать `bot/keyboards/sprint.py`:
    - `sprint_intro_keyboard()` — кнопки «▶️ Поехали» и «🔙 Назад»
    - `answer_keyboard(options: dict)` → 4 кнопки: `A: {text}`, `B: {text}`, `C: {text}`, `D: {text}` + кнопка «🏠 Меню»
    - ⚠️ **callback_data лимит 64 байта:** НЕ передавать `question_id` в callback — хранить текущий вопрос в Redis-сессии (`current_question_id`). Кнопки ответа: `sprint_ans:a`, `sprint_ans:b`, `sprint_ans:c`, `sprint_ans:d` (~12 байт)
    - `sprint_result_keyboard()` — «🏠 В меню» и «🔄 Ещё раз»
  - Создать `bot/handlers/sprint.py` с полным SprintFlow:
    - `callback: sprint_start` → показать описание спринта
    - `callback: sprint_go` → загрузить вопросы через `question_service`, создать Redis-сессию (`questions=[id,...], current_idx=0, correct_count=0`), показать первый вопрос
    - `callback: sprint_ans:{option}` → получить `current_question_id` из Redis-сессии, проверить ответ:
      - Правильно: +10 XP, `progress_repo.add(is_correct=True)`, `session.correct_count += 1`, показать «✅ Правильно!» + следующий вопрос
      - Неправильно: `mistake_service.add_mistake(...)`, `progress_repo.add(is_correct=False)`, показать «❌ Неверно. Верный ответ: {X}\n\n{explanation}» + следующий вопрос
      - `session.current_idx += 1` → если `current_idx >= total`: конец спринта
      - Прогресс «Вопрос N/Total» в тексте
    - Конец спринта: +50 XP бонус, `delete_session`, показать «Ваш счёт: {correct}/{total}»
    - `callback: sprint_menu` → `delete_session`, вернуть в главное меню
  - Logging: `[HANDLER:sprint] User {uid} started sprint`, `[HANDLER:sprint] ans={opt} q={qid} correct={b}`, `[HANDLER:sprint] Done: {correct}/{total}`

> 🔵 **Checkpoint 3** — commit: `feat(sprint): implement Sprint mode US-002`

---

## Phase 4: Режим Тренировка (US-003)

- [ ] **Task 11: FSM и хендлеры Тренировки (bot/handlers/training.py)**
  - Создать `bot/fsm/training.py`: `class TrainingState(StatesGroup): in_progress = State()`
  - Создать `bot/keyboards/training.py`:
    - `training_setup_keyboard(topics, selected_ids)` → Inline: список тем с чекбоксами (✅/☐), кнопки «▶️ Начать» и «🔙 Назад»
    - `training_answer_keyboard(options: dict)` → 4 варианта + «🛑 Закончить»
    - ⚠️ **callback_data лимит 64 байта:** callback кнопок ответа: `train_ans:a`, `train_ans:b`, `train_ans:c`, `train_ans:d` — `current_question_id` берётся из Redis (`session["current_question_id"]`)
    - `training_summary_keyboard()` → «🏠 В меню»
  - Создать `bot/handlers/training.py`:
    - `callback: training_start` → показать экран выбора тем (все темы, изначально все выбраны)
    - `callback: training_toggle:{topic_id}` → переключить тему в Redis temp-хранилище, обновить клавиатуру
    - `callback: training_begin` → проверить: если нет выбранных тем → «⚠️ Выберите хотя бы одну тему»; создать Redis-сессию с `difficulty=1`, выбрать первый вопрос через `question_service`, записать `current_question_id`
    - `callback: train_ans:{option}` → получить `current_question_id` из Redis:
      - Правильно: `difficulty = min(3, difficulty+1)`, +10 XP, следующий вопрос
      - Неправильно: `difficulty = max(1, difficulty-1)`, ошибку в БД, показать объяснение
      - Записать новый `current_question_id` в Redis после каждого вопроса
    - `callback: training_stop` → `delete_session`, показать итог (решено вопросов, XP)
  - Logging: `[HANDLER:training] Started topics={t} difficulty=1`, `[HANDLER:training] ans={opt} correct={b} new_diff={d}`

> 🔵 **Checkpoint 4** — commit: `feat(training): implement Training mode US-003`

---

## Phase 5: Каталог тем (US-004)

- [ ] **Task 12: Хендлеры каталога тем (bot/handlers/topics.py)**
  - Создать `bot/keyboards/topics.py`:
    - `topics_list_keyboard(topics)` → Inline: список тем (каждая — кнопка) + «🔙 Назад»
    - `topic_card_keyboard(topic_id)` → «📖 Теория», «📝 Задачи», «🔙 Назад»; callback: `topic_card:{id}` (~18 байт ✅)
    - `tasks_list_keyboard(questions, solved_ids)` → список задач с маркерами ✅/☐ + «🔙 Назад»; callback: `solve_q:{id}` (~15 байт ✅)
    - `task_solve_keyboard(options: dict)` → 4 варианта ответа
    - ⚠️ **callback_data лимит:** кнопки ответа: `topic_ans:a`, `topic_ans:b`, `topic_ans:c`, `topic_ans:d` (~12 байт); `question_id` хранить в Redis temp: `topics_session:{user_id}` = `{"current_question_id": id, "topic_id": id}`
    - `task_feedback_keyboard(topic_id)` → «🔙 К списку», «➡️ Следующая»
  - Добавить в `repositories/progress_repo.py` метод `get_solved_ids(user_id, topic_id) -> list[int]` — нужен для маркеров ✅ в списке задач
  - Создать `bot/handlers/topics.py`:
    - `callback: topics_list` → показать список всех тем
    - `callback: topic_card:{topic_id}` → показать карточку темы
    - `callback: topic_theory:{topic_id}` → показать `topic.theory_text`
    - `callback: topic_tasks:{topic_id}` → список задач по difficulty, маркеры через `progress_repo.get_solved_ids()`
    - `callback: solve_q:{question_id}` → записать `current_question_id` в Redis, показать задачу
    - `callback: topic_ans:{option}` → взять `current_question_id` из Redis, проверить, сохранить прогресс, показать фидбек
  - Logging: `[HANDLER:topics] opened topic {tid}`, `[HANDLER:topics] solved q={qid} correct={b}`

---

## Phase 6: Работа над ошибками (US-006)

- [ ] **Task 13: Хендлеры работы над ошибками (bot/handlers/mistakes.py)**
  - Создать `bot/keyboards/mistakes.py`:
    - `mistakes_menu_keyboard(has_mistakes, topics_with_mistakes)` → «🎲 Все подряд», «📂 По теме» + список тем + «🔙 Назад»
    - `mistake_answer_keyboard(options: dict)` → 4 варианта
    - ⚠️ **callback_data лимит:** НЕ передавать `mistake_id` + `question_id` + `option` в одном callback (превысит 64б). Хранить `{current_mistake_id, current_question_id}` в Redis: `mistakes_session:{user_id}`. Кнопки: `mis_ans:a`, `mis_ans:b`, `mis_ans:c`, `mis_ans:d` (~10 байт ✅)
    - `mistakes_empty_keyboard()` → «🎉 Все исправлено!» + «🏠 В меню»
  - Создать `bot/handlers/mistakes.py`:
    - `callback: mistakes_menu` → `mistake_repo.count(user_id)`, показать меню
    - `callback: mistakes_all` → взять случайную ошибку, записать в Redis-сессию `{current_mistake_id, current_question_id}`, показать задачу
    - `callback: mis_topic:{topic_id}` → случайная ошибка по теме, записать в Redis
    - `callback: mis_ans:{option}` → взять `current_mistake_id` + `current_question_id` из Redis:
      - Правильно: `mistake_service.fix_mistake(current_mistake_id)`, +5 XP, взять следующую ошибку или показать «Все исправлено!»
      - Неправильно: показать решение, взять следующую ошибку
  - Logging: `[HANDLER:mistakes] mistakes count={n}`, `[HANDLER:mistakes] fixed mistake {mid} q={qid}`

> 🔵 **Checkpoint 5** — commit: `feat(topics,mistakes): implement Topics catalog US-004 and Mistakes US-006`

---

## Phase 7: Профиль (US-007)

- [ ] **Task 14: Хендлер профиля (bot/handlers/profile.py)**
  - Создать `bot/keyboards/profile_kb.py`: `profile_keyboard()` → «🔙 Назад в меню»
  - Создать `bot/handlers/profile.py`:
    - Хендлеры для `callback: profile` и Reply-кнопки «👤 Профиль»
    - Формировать и отправлять карточку пользователя:
      ```
      👤 Ваш профиль
      
      🏅 Уровень: Практик
      ⭐ XP: 450 / 600 до Профессионала
      ████████░░ 75%
      
      ✅ Задач выполнено: 87
      🎯 Точность: 82%
      🔥 Серия: 5 дней
      💎 Статус: FREE
      ```
    - XP-бар: 10 символов `█/░`, процент до следующего уровня
  - Logging: `[HANDLER:profile] User {uid} opened profile. xp={xp}, level={level}`

---

## Phase 8: Админпанель (US-008, 009, 011)

- [ ] **Task 15: Структура и FSM админки**
  - Создать `bot/fsm/admin.py`:
    - `AdminAddTopicState`: `waiting_title`, `waiting_theory`
    - `AdminAddQuestionState`: `waiting_topic`, `waiting_text`, `waiting_options`, `waiting_answer`, `waiting_difficulty`, `waiting_explanation`
    - `AdminBroadcastState`: `waiting_message`, `confirm`
  - Создать `bot/keyboards/admin.py`:
    - `admin_menu_keyboard()` → «📚 Контент», «📢 Рассылка», «🔙 Выход»
    - `admin_content_keyboard()` → «➕ Добавить тему», «📋 Список тем», «🔙 Назад»
    - `admin_topics_keyboard(topics)` → список тем с кнопками редактирования
    - `admin_topic_manage_keyboard(topic_id)` → «➕ Добавить задачу», «✏️ Переименовать», «🗑 Удалить», «🔙 Назад»
    - `admin_confirm_keyboard()` → «✅ Подтвердить», «❌ Отмена»

- [ ] **Task 16: Хендлеры админпанели (bot/handlers/admin/)**
  - Создать `bot/handlers/admin/menu.py`:
    - `/admin` → проверка `user.is_admin` (иначе «⛔ Нет доступа»), показать `admin_menu_keyboard()`
    - `callback: admin_menu` → показать меню
  - Создать `bot/handlers/admin/content.py`:
    - `callback: admin_content` → показать управление контентом
    - FSM-диалог добавления темы: запрос названия → запрос теории → `topic_repo.create()` → OK
    - FSM-диалог добавления задачи: запрос текста → 4 варианта → верный → сложность (1/2/3) → объяснение → `question_repo.create()` → OK
    - Переименование темы: FSM с запросом нового названия → `topic_repo.update()`
    - Удаление темы: подтверждение → `topic_repo.delete()`
  - Создать `bot/handlers/admin/broadcast.py`:
    - `callback: admin_broadcast` → запрос текста рассылки (FSM)
    - Предпросмотр → «Выглядит так: {text}» + кнопки подтверждения
    - Подтверждение → `broadcast_service.send_to_all(text, db)` — отправка с задержкой 0.05s между пользователями
    - Отчёт: «Отправлено N из M пользователей»
  - Middleware `admin_check.py` не требуется — проверка внутри хендлера через `user.is_admin`
  - Logging: `[ADMIN] /admin by uid={uid}`, `[ADMIN:broadcast] Starting to {n} users`, `[ADMIN:broadcast] Done: {sent}/{total}`

> 🔵 **Checkpoint 6** — commit: `feat(profile,admin): implement Profile US-007 and Admin Panel US-008/009/011`

---

## Phase 9: Финальная сборка

- [ ] **Task 17: Регистрация всех роутеров и финальная интеграция**
  - В `bot/main.py` зарегистрировать все роутеры в правильном порядке:
    `start → sprint → training → topics → mistakes → profile → admin/menu → admin/content → admin/broadcast`
  - Добавить глобальный exception handler (логировать traceback, куда пишет loguru, юзеру — «Произошла ошибка. Попробуйте ещё раз.»)
  - Добавить `on_startup`: запустить `alembic upgrade head` программно, проверить подключение к Redis
  - Проверить все callback_data на уникальность, отсутствие коллизий
  - Logging: `[BOOT] All routers registered`, `[BOOT] DB migrated`, `[BOOT] Redis connected`

- [ ] **Task 18: Финальная проверка и README**
  - Проверить `docker-compose up --build` — бот стартует, БД создаётся, seed отрабатывает
  - Пройти базовый user-flow вручную: /start → Спринт → ответить 3 вопроса → проверить XP в профиле
  - Создать `README.md` с: описанием, требованиями (Docker), инструкцией запуска (`cp .env.example .env`, заполнить `BOT_TOKEN`, `docker-compose up -d`, `python -m data.seed`)
  - Logging: любые критические запуски логировать на уровне INFO

> 🔵 **Checkpoint 7 (Final)** — commit: `feat(bot): complete MathTrainer MVP — all features integrated`

---

## Commit Plan

| Checkpoint | Tasks | Commit Message |
|------------|-------|----------------|
| 1 | 1–5 | `feat(infra): add project structure, DB models, Docker and seed data` |
| 2 | 6–9 | `feat(core): add middlewares, repos, services, keyboards and /start` |
| 3 | 10 | `feat(sprint): implement Sprint mode US-002` |
| 4 | 11 | `feat(training): implement Training mode US-003` |
| 5 | 12–13 | `feat(topics,mistakes): implement Topics catalog US-004 and Mistakes US-006` |
| 6 | 14–16 | `feat(profile,admin): implement Profile US-007 and Admin Panel US-008/009/011` |
| 7 | 17–18 | `feat(bot): complete MathTrainer MVP — all features integrated` |

---

## Summary

**18 задач / 7 коммит-чекпоинтов / 9 фаз**

Порядок реализации строго последовательный:
1. Фундамент (инфраструктура, БД, Docker) — Phase 1
2. Ядро бота (middlewares, repos, services, navigation) — Phase 2
3. Игровые режимы (Sprint → Training → Topics → Mistakes) — Phase 3–6
4. Профиль и Админка — Phase 7–8
5. Интеграция и проверка — Phase 9
