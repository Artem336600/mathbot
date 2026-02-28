# MathTrainer Bot 🤖📚

Telegram-бот для тренировки математики на Python/Aiogram 3.

## Функции

- 🚀 **Спринт** — 15 вопросов случайной сложности, +50 XP за завершение
- 🏋️ **Тренировка** — адаптивная сложность (easy → medium → hard)
- 📚 **Каталог тем** — теория + задачи с маркерами прогресса
- ❌ **Ошибки** — работа над неверными ответами, +5 XP за исправление
- 👤 **Профиль** — XP bar, уровни, серия, точность
- 🔧 **Админка (Mini App)** — управление темами/вопросами (импорт JSON), бан пользователей, статистика, рассылка через FastAPI Dashboard

## Требования

- Docker & Docker Compose
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

## Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd mathtrainer

# 2. Настроить переменные окружения
cp .env.example .env
# Отредактировать .env — вставить BOT_TOKEN и ADMIN_IDS

# 3. Запустить инфраструктуру
docker-compose up -d postgres redis

# 4. Применить миграции
docker-compose run --rm bot alembic upgrade head

# 5. Загрузить тестовые данные (60 вопросов по 5 темам)
docker-compose run --rm bot python -m data.seed

# 6. Запустить бота
docker-compose up -d bot
```

## Переменные окружения

| Переменная | Описание | Пример |
|------------|----------|--------|
| `BOT_TOKEN` | Telegram Bot API токен | `123456:ABC...` |
| `DATABASE_URL` | PostgreSQL URL | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/0` |
| `LOG_LEVEL` | Уровень логирования | `DEBUG` / `INFO` |
| `ADMIN_IDS` | Telegram ID администраторов | `123456789,987654321` |

## Стек технологий

| Компонент | Технология |
|-----------|------------|
| Язык | Python 3.12 |
| Бот | Aiogram 3 |
| Админка | FastAPI, Telegram WebApp (SPA - HTML/JS/CSS) |
| БД | PostgreSQL 16 |
| ORM | SQLAlchemy 2 (async) |
| Миграции | Alembic |
| Кэш/сессии | Redis 7 |
| Деплой | Docker Compose |
| Логирование | Loguru |

## Структура проекта

```
mathtrainer/
├── bot/
│   ├── handlers/          # Обработчики сообщений и callback
│   │   ├── admin/         # Админпанель
│   │   ├── sprint.py      # Режим Спринт
│   │   ├── training.py    # Режим Тренировка
│   │   ├── topics.py      # Каталог тем
│   │   ├── mistakes.py    # Ошибки
│   │   ├── profile.py     # Профиль
│   │   └── start.py       # /start, главное меню
│   ├── keyboards/         # Клавиатуры (Inline + Reply)
│   ├── middlewares/       # DB, User, BanCheck
│   ├── fsm/               # Состояния FSM
│   ├── config.py          # Настройки (pydantic-settings)
│   └── main.py            # Точка входа
├── services/              # Бизнес-логика
├── repositories/          # Работа с БД
├── db/
│   ├── models.py          # SQLAlchemy ORM модели
│   ├── session.py         # Async engine
│   └── migrations/        # Alembic миграции
├── data/
│   └── seed.py            # Начальные данные
├── webapp/              # FastAPI админ-панель (Telegram Mini App)
│   ├── routers/           # API Endpoints (статистика, топики, пользователи)
│   ├── static/            # Frontend SPA (Vanilla JS + CSS)
│   ├── main.py            # FastAPI приложение
│   ├── auth.py            # Валидация initData
│   └── run.py             # Асинхронный запуск uvicorn
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## XP система

| Действие | XP |
|----------|----|
| Правильный ответ | +10 |
| Исправленная ошибка | +5 |
| Завершение спринта | +50 |

| Уровень | Порог XP |
|---------|----------|
| Новичок | 0 |
| Ученик | 100 |
| Практик | 300 |
| Профессионал | 600 |

## Команды бота

- `/start` — запустить бота
- `/admin` — открыть панель администратора (только для ADMIN_IDS)
