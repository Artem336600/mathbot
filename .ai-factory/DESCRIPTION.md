# Project: MathTrainer

## Overview
MathTrainer — Telegram-бот для микрообучения математике. Пользователи решают задачи прямо в мессенджере, не покидая Telegram. Ориентирован на короткие сессии "на ходу". Ответы — через Inline-кнопки (варианты A/B/C/D).

## Core Features (MVP)

- **US-001: Навигация** — Reply Keyboard (меню, профиль) + Inline (режимы, задачи)
- **US-002: Режим Спринт** — 10–20 вопросов с мгновенной проверкой после каждого
- **US-003: Режим Тренировка** — бесконечный поток задач с адаптивной сложностью (+1/-1)
- **US-004: Каталог тем и теория** — список тем, вкладки Теория/Задачи, сортировка по сложности
- **US-006: Работа над ошибками** — отдельный раздел, фильтр по темам, перерешивание
- **US-007: Профиль** — XP, уровни, streak, точность, статус подписки
- **US-008/009: Админпанель (Telegram WebApp)** — полноценный дашборд (FastAPI + HTML/JS/CSS), управление темами/задачами (поштучно + импорт JSON), бан пользователей
- **US-011: Рассылка** — массовая отправка с предпросмотром через WebApp и progress-баром на базе Redis

## Tech Stack

- **Language:** Python 3.12
- **Bot Framework:** Aiogram 3
- **Database:** PostgreSQL 16
- **Cache / Sessions:** Redis 7
- **ORM:** SQLAlchemy 2.0 (async) + Alembic (миграции)
- **Admin Dashboard:** FastAPI + Telegram Mini App (HTML/JS/CSS SPA)
- **Deploy:** Docker Compose на VPS

## XP & Levels

- Правильный ответ: +10 XP
- Исправление ошибки: +5 XP
- Бонус за завершённый спринт: +50 XP
- Уровни: Новичок (0–99) / Ученик (100–299) / Практик (300–599) / Профессионал (600+)

## Non-Functional Requirements

- Logging: структурированный лог (loguru), LOG_LEVEL через env
- Error handling: graceful degradation, пользователь видит понятное сообщение об ошибке
- Security: проверка бана через middleware, проверка роли admin через middleware
- Environment: все секреты через `.env` (BOT_TOKEN, DATABASE_URL, REDIS_URL)

## Architecture
See `.ai-factory/ARCHITECTURE.md` for detailed architecture guidelines.
Pattern: Layered Architecture (handlers → services → repositories → db)
