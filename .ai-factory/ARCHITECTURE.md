# Architecture: Layered Architecture

## Overview

MathTrainer использует **Layered Architecture (Послойная архитектура)** — классический и проверенный подход для Telegram-ботов на Aiogram 3. Приложение разделено на горизонтальные слои: хендлеры (presentation) → сервисы (business logic) → репозитории (data access) → база данных.

Этот выбор обусловлен небольшим размером команды, умеренной сложностью домена и тем, что Aiogram 3 уже диктует свои соглашения (Router, FSM, Middleware), которые естественно ложатся в слоистую модель.

## Decision Rationale

- **Project type:** Telegram-бот с несколькими игровыми режимами и админпанелью
- **Tech stack:** Python 3.12 + Aiogram 3 + PostgreSQL + Redis + SQLAlchemy 2.0
- **Team:** 1–2 разработчика
- **Key factor:** Высокая начальная скорость разработки, минимальный boilerplate, простота отладки

## Folder Structure

```
mathtrainer/
│
├── bot/                         # Слой Presentation (Aiogram handlers, keyboards, FSM)
│   ├── main.py                  # Точка входа: создание бота, dp, запуск polling
│   ├── config.py                # Pydantic BaseSettings, загрузка .env
│   │
│   ├── handlers/                # Aiogram Routers (один файл = один use-case)
│   │   ├── start.py             # /start, главное меню
│   │   ├── sprint.py            # режим Спринт
│   │   ├── training.py          # режим Тренировка
│   │   ├── topics.py            # каталог тем и теория
│   │   ├── mistakes.py          # работа над ошибками
│   │   ├── profile.py           # профиль пользователя
│   │   └── admin/
│   │       ├── menu.py          # /admin, главное меню админа
│   │       ├── content.py       # управление темами/задачами
│   │       ├── users.py         # управление пользователями
│   │       └── broadcast.py     # рассылка
│   │
│   ├── keyboards/               # Inline и Reply клавиатуры
│   │   ├── reply.py             # Reply Keyboard (меню, профиль) — постоянная
│   │   ├── main_menu.py         # Inline: главное меню
│   │   ├── sprint.py            # Inline: варианты ответов A/B/C/D в спринте
│   │   ├── training.py          # Inline: тренировка
│   │   ├── topics.py            # Inline: список тем, чекбоксы
│   │   ├── mistakes.py          # Inline: меню ошибок
│   │   └── admin.py             # Inline: админпанель
│   │
│   ├── fsm/                     # Aiogram FSM States
│   │   ├── sprint.py            # SprintState
│   │   ├── training.py          # TrainingState
│   │   └── admin.py             # AdminContentState, AdminBroadcastState
│   │
│   └── middlewares/             # Aiogram Middlewares
│       ├── database.py          # Инъекция AsyncSession в хендлеры
│       ├── ban_check.py         # Блокировка забаненных пользователей
│       └── admin_check.py       # Проверка прав admin
│
├── services/                    # Слой Business Logic (не знает об Aiogram)
│   ├── user_service.py          # регистрация, получение/обновление пользователя
│   ├── question_service.py      # выборка вопросов, адаптивность (difficulty +/-1)
│   ├── session_service.py       # работа с Redis-сессиями (init/get/update/close)
│   ├── stats_service.py         # начисление XP, streak, точность
│   ├── mistake_service.py       # добавление/исправление ошибок
│   └── broadcast_service.py     # массовая рассылка с задержкой
│
├── repositories/                # Слой Data Access (только SQL, никакой логики)
│   ├── user_repo.py             # CRUD пользователей
│   ├── topic_repo.py            # CRUD тем
│   ├── question_repo.py         # CRUD задач, выборка по сложности/теме
│   ├── mistake_repo.py          # CRUD ошибок пользователя
│   └── progress_repo.py         # история решений (user_progress)
│
├── db/                          # Слой Data (модели + подключение)
│   ├── models.py                # SQLAlchemy ORM модели всех таблиц
│   ├── session.py               # async_engine, async_session_factory
│   └── migrations/              # Alembic миграции
│       ├── env.py
│       └── versions/
│
├── data/
│   └── seed.py                  # Начальный банк тем и задач (тестовые данные)
│
├── docker-compose.yml           # bot + postgres + redis
├── Dockerfile
├── .env.example
├── requirements.txt
└── alembic.ini
```

## Dependency Rules

Слои зависят только от слоя **ниже** себя. Никогда не наоборот.

```
handlers  →  services  →  repositories  →  db/models
keyboards       ↓
fsm          (Redis через session_service)
middlewares
```

- ✅ `handlers` вызывают `services`
- ✅ `services` вызывают `repositories`
- ✅ `repositories` используют `db/models` и `db/session`
- ✅ `keyboards` используют только примитивы Python (str, int, list) — без импортов сервисов
- ❌ `services` не знают об Aiogram (`Message`, `CallbackQuery`)
- ❌ `repositories` не содержат бизнес-логики (проверок XP, уровней и т.д.)
- ❌ `handlers` не обращаются к `repositories` напрямую — только через `services`
- ❌ Нельзя делать импорт из `handlers` в `services` или `repositories`

## Layer Communication

- **handlers → services:** передают параметры (user_id, topic_id, answer), получают результат (dict или dataclass)
- **services → repositories:** передают параметры, получают ORM-объекты или None
- **services → Redis:** через `session_service` (единственная точка работы с Redis)
- **middlewares → handlers:** инъекция `db_session` через `data["db"]` в хендлер

## Key Principles

1. **Хендлер — тонкий.** Хендлер только: парсит входные данные → вызывает сервис → формирует ответ (текст + клавиатура). Никакой логики внутри.
2. **Сервис — без Aiogram.** Сервисы — чистые Python-функции/классы. Их можно тестировать без поднятия бота.
3. **Один Router = один экран.** Каждый файл в `handlers/` регистрирует один Aiogram Router и отвечает за одну часть UX.
4. **FSM только в handlers.** State-машина управляется только из хендлеров, никогда из сервисов.
5. **Redis только через session_service.** Прямые вызовы Redis запрещены вне `session_service.py`.
6. **Все секреты через `.env`.** `BOT_TOKEN`, `DATABASE_URL`, `REDIS_URL` — только через переменные окружения.
7. **Весь I/O асинхронный.** Использовать `asyncpg` + `aioredis`. Синхронные блокирующие вызовы запрещены.

## Code Examples

### Handler (тонкий — только парсинг и вызов сервиса)
```python
# bot/handlers/sprint.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.session_service import SessionService
from services.question_service import QuestionService
from keyboards.sprint import build_question_keyboard

router = Router()

@router.callback_query(F.data == "start_sprint")
async def start_sprint(callback: CallbackQuery, db, user):
    session = await SessionService.create_sprint_session(user.id, db)
    question = await QuestionService.get_next(session, db)
    keyboard = build_question_keyboard(question)
    await callback.message.edit_text(
        f"❓ Вопрос {session.current}/{session.total}\n\n{question.text}",
        reply_markup=keyboard,
    )
    await callback.answer()
```

### Service (бизнес-логика без Aiogram)
```python
# services/stats_service.py
from repositories.user_repo import UserRepository

XP_CORRECT = 10
XP_FIX_MISTAKE = 5
XP_SPRINT_BONUS = 50

LEVELS = [
    (0, "Новичок"),
    (100, "Ученик"),
    (300, "Практик"),
    (600, "Профессионал"),
]

async def award_xp(user_id: int, amount: int, db) -> dict:
    user = await UserRepository.get(user_id, db)
    user.xp += amount
    new_level = next(
        name for threshold, name in reversed(LEVELS) if user.xp >= threshold
    )
    level_up = new_level != user.level
    user.level = new_level
    await db.commit()
    return {"xp": user.xp, "level": user.level, "level_up": level_up}
```

### Repository (только SQL, никакой логики)
```python
# repositories/question_repo.py
from sqlalchemy import select
from db.models import Question

class QuestionRepository:
    @staticmethod
    async def get_by_difficulty(topic_ids: list[int], difficulty: int, limit: int, db) -> list[Question]:
        result = await db.execute(
            select(Question)
            .where(Question.topic_id.in_(topic_ids))
            .where(Question.difficulty == difficulty)
            .order_by(func.random())
            .limit(limit)
        )
        return result.scalars().all()
```

### Middleware (инъекция db session)
```python
# bot/middlewares/database.py
from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from db.session import async_session_factory

class DatabaseMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: TelegramObject, data: dict) -> Any:
        async with async_session_factory() as session:
            data["db"] = session
            return await handler(event, data)
```

## Anti-Patterns

- ❌ **Логика в хендлерах.** `if user.xp >= 100: user.level = "Ученик"` — это в сервис.
- ❌ **Прямой SQL в хендлерах.** `await db.execute(select(User)...)` в хендлере — только через репозиторий.
- ❌ **Aiogram-типы в сервисах.** `from aiogram.types import Message` в `services/` — запрещено.
- ❌ **Синхронные блокирующие вызовы.** `requests.get(...)` вместо `aiohttp` — заблокирует event loop.
- ❌ **Redis напрямую из хендлеров.** Только через `SessionService`.
- ❌ **Хардкод токенов.** `BOT_TOKEN = "123:abc"` в коде — только через `.env`.
- ❌ **Один гигантский файл handlers.** Разбивать по экранам/режимам.
