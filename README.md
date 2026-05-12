
![Python](https://img.shields.io/badge/Python-3.14-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green)
![Docker](https://img.shields.io/badge/Docker-ready-blue)
# User Center V2

REST API для управления пользователями с асинхронным кэшированием.

**Стек:** FastAPI, PostgreSQL, Redis, Docker, pytest.

## Запуск

cp .env.example .env && docker-compose up --build

## API

GET /users - список
GET /stats - статистика
POST /add_user - создать
DELETE /delete_user - удалить
DELETE /clear - очистить БД
GET /health - проверка

## .env

DB_USER=postgres
DB_PASSWORD=1234
DB_NAME=server1_db
ADMIN_PASSWORD=ssd
DATABASE_URL=postgresql://postgres:1234@db:5432/server1_db
REDIS_URL=redis://redis:6379