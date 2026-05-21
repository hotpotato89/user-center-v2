# User Center V2

# Устарело. Актуальная версия:
- **Репозиторий**: [https://sourcecraft.dev/hotpotato89/user-center-v3](https://sourcecraft.dev/hotpotato89/user-center-v3)

REST API для управления пользователями с асинхронным кэшированием.

## Стек технологий

- **Python**
- **FastAPI**
- **PostgreSQL** 15
- **Redis**
- **Docker** / Docker Compose
- **pytest** + aiohttp
- **Uvicorn**
- **asyncpg**
- **Pydantic**

**🚀 Быстрый старт:** `cp .env.example .env && docker-compose up --build`

## API

GET /`users` - список
GET /`stats` - статистика
POST /`add_user` - создать
DELETE /`delete_user` - удалить
DELETE /`clear` - очистить БД
GET /`health` - проверка
GET /`__flush_redis__` - специальный роут для тестов, защищен для локального использования

## .env

DB_USER=
DB_PASSWORD=
DB_NAME=
ADMIN_PASSWORD=
DATABASE_URL=
REDIS_URL=

## Тесты (pytest + aiohttp)
Были использованы фикстуры и одна авто-фикстура для очистки кэша. Всего **12** тестов