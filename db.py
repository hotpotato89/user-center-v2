import asyncpg
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

import schemas
from log import get_logger

load_dotenv()

dsn = os.getenv('DATABASE_URL')
if not dsn:
    raise ValueError('Нет DATABASE_URL в файле .env')
admin_password = os.getenv('ADMIN_PASSWORD')
if not admin_password:
    raise ValueError('Нет ADMIN_PASSWORD в файле .env')
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=5,
        max_size=10,
    )
    logger.info('Пул соединений установлен')
    async with app.state.pool.acquire() as session:
        await session.execute('create table if not exists users (id serial primary key, name varchar(60), age integer, email varchar(45) unique, reg_time timestamp default now())')
        await session.execute('create index if not exists idx_regtime_desc on users(reg_time desc)')
        await session.execute('create index if not exists idx_age_max on users(age desc)')
        await session.execute('create index if not exists idx_age_min on users(age asc)')
    yield
    logger.info('Пул соединений разорван')
    await app.state.pool.close()

async def get_users_db(pool, limit: int, skip: int):
    async with pool.acquire() as session:
        data = await session.fetch('select * from users order by reg_time desc offset $1 limit $2', skip, limit)
        total = await session.fetchval('select count(*) from users')
    current_page = (skip // limit) + 1 if limit>0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    if not data:
        return schemas.ReturnForm(success=False, message='База данных пуста', error_code='empty')
    return schemas.ReturnForm(success=True, message=f'Найдено {len(data)} пользователей.', data=[dict(row) for row in data], total=total, page=current_page, total_pages=total_pages, limit=limit)

async def add_user_db(pool, user_data: schemas.UserDataForm):
    async with pool.acquire() as session:
        logger.info('Попытка создать пользователя')
        try:
            user_id = await session.fetchval('insert into users (name, age, email) values ($1, $2, $3) returning id', user_data.name, user_data.age, user_data.email)
            logger.info(f'Пользователь {user_data.email} создан, id={user_id}')
            return schemas.ReturnForm(success=True, message=f'Пользователь успешно добавлен', id=user_id)
        except asyncpg.UniqueViolationError:
            logger.error('Пользователь с ввел существующий email')
            return schemas.ReturnForm(success=False, message=f'Пользователь с email \'{user_data.email}\' уже существует', error_code='conflict')
        except Exception as e:
            logger.error(f'Ошибка {e}')
            return schemas.ReturnForm(success=False, message='Ошибка на стороне сервера')
        
async def clear_all_db(pool, password: schemas.PasswordForm):
    logger.info('Попытка очистить базу данных')
    if password.password != admin_password:
        logger.error('Был введён неверный пароль')
        return schemas.ReturnForm(success=False, message='Неверный админ-пароль', error_code='unauthorized')
    async with pool.acquire() as session:
        deleted = await session.fetchval('select count(*) from users')
        await session.execute('truncate users restart identity')
    logger.info(f'База данных очищена, удалено {deleted} записей.')
    return schemas.ReturnForm(success=True, message=f'Удалено {deleted} записей.')

async def delete_user_db(pool, user_data: schemas.DeleteUserForm):
    logger.info(f'Попытка удалить пользователя по айди {user_data.id}')
    if user_data.password != admin_password:
        logger.error('Был введен неверный пароль')
        return schemas.ReturnForm(success=False, message='Неверный админ-пароль', error_code='unauthorized')
    async with pool.acquire() as session:
        try:
            deleted_data = await session.fetch('delete from users where id=$1 returning *', user_data.id)
            if not deleted_data:
                logger.error(f'Пользователя по айди {user_data.id} не существует')
                return schemas.ReturnForm(success=False, message='Нет такого пользователя', error_code='unknown_user')
        except Exception as e:
            logger.error(f'Ошибка {e}')
            return schemas.ReturnForm(success=False, message='Ошибка внутри сервера', error_code='server_error')
    logger.info(f'Пользователь по айди {user_data.id} удален')
    return schemas.ReturnForm(success=True, message=f'Удален пользователь под айди {user_data.id}', data=[dict(row) for row in deleted_data])

async def get_stats_db(pool):
    async with pool.acquire() as session:
        total_users = await session.fetchval('select count(*) from users')
        if total_users == 0:
            return schemas.ReturnForm(success=False, message='База данных пуста', error_code='empty')
        oldest_user = await session.fetchrow('select * from users order by age desc limit 1')
        youngest_user = await session.fetchrow('select * from users order by age asc limit 1')
        mean_age = await session.fetchval('select avg(age) from users')
        stats = {
            'oldest_user': dict(oldest_user) if oldest_user else None,
            'youngest_user': dict(youngest_user) if youngest_user else None,
            'mean_age': round(mean_age, 2) if mean_age else 0,
            'total_users': total_users
        }
        return schemas.ReturnForm(success=True, message='Данные успешно получены', data=stats)