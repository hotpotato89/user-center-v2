from fastapi import FastAPI, Request, Depends, HTTPException, Query
from time import perf_counter
from typing import Annotated
from asyncpg import Pool
from redis.asyncio import Redis
import json
from datetime import datetime
from decimal import Decimal

#Для фронта
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path

import db
import schemas
from log import get_logger

app = FastAPI(lifespan=db.lifespan, title='Моя API')
logger = get_logger(__name__)
MAIN_TAG: list = ['Моя API']
TTL: int = 20
PAGINATION_TTL: int = 120

@app.get('/__flush_redis__')
async def flush_redis(request: Request):
    """Специальный эндпоинт для тестов, нужен для очистки кэша"""
    allowed_ips = [
        '127.0.0.1',
        '::1',
        '172.17.0.1',
        '172.18.0.1',
        '172.19.0.1'
    ]
    #Проверка:
    if request.client.host not in allowed_ips: #type: ignore
        raise HTTPException(status_code=403, detail='Method not allowed')
    redis = get_redis()
    await redis.flushall()
    return schemas.ReturnForm(success=True, message='Flushed')


app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def main_page():
    return FileResponse('static/index.html')

def get_pool():
    return app.state.pool

def get_redis() -> Redis:
    return app.state.redis

def json_encode(object):
    if isinstance(object, datetime):
        return object.isoformat()
    if isinstance(object, Decimal):
        return float(object)
    raise TypeError(f"Object of type {type(object)} is not JSON serializable")

@app.middleware('http')
async def middleware_(request: Request, next_call):
    start_time = perf_counter()
    result = await next_call(request)
    duration = perf_counter() - start_time
    if duration > 0.7:
        logger.warning(f'Долгое выполнение запроса: {duration:.4f}')
    return result

@app.get('/stats', tags=MAIN_TAG)
async def stats_page(pool: Annotated[Pool, Depends(get_pool)]):
    redis = get_redis()

    # Проверяем кэш
    cached = await redis.get('stats')
    logger.info('Проверяем кэш')
    
    if cached:
        logger.info('Кэш найден, возвращаем данные')
        return json.loads(cached)
    
    logger.info('Кэша нет, идём в БД')

    result = await db.get_stats_db(pool)
    if not result.success:
        await redis.delete('stats')
        if result.error_code == 'empty':
            raise HTTPException(status_code=404, detail=result.message)
    
    # Сохраняем в кэш
    await redis.setex('stats', TTL, json.dumps(result.dict(), default=json_encode))
    logger.info('Данные получены из БД и сохранены в кэш')
    
    return result

@app.get('/health', tags=MAIN_TAG)
async def healthcheck():
    return schemas.ReturnForm(success=True, message='Healthy')

@app.get('/users', tags=MAIN_TAG)
async def get_users(pool = Depends(get_pool),
                    limit: int = Query(..., ge=1, description='Лимит записей в одной странице'),
                    page: int = Query(..., ge=1, description='Какая страница будет просмотрена')):
    redis = get_redis()
    limit = min(limit, 50)
    skip = (page-1)*limit

    cache_key = f'users:limit={limit}:page={page}'
    logger.info('Проверяем кэш')
    cached = await redis.get(cache_key)
    if cached:
        logger.info('Кэш найден, возвращаем данные')
        return json.loads(cached)

    logger.info('Кэша нет, идём в БД')

    result = await db.get_users_db(pool=pool, limit=limit, skip=skip)
    if not result.success:
        if result.error_code == 'empty':
            raise HTTPException(status_code=404, detail=result.message)
        raise HTTPException(status_code=500, detail=result.message)
    
    await redis.setex(cache_key, PAGINATION_TTL, json.dumps(result.dict(), default=json_encode))

    logger.info('Данные получены из БД и сохранены в кэш')

    return result

@app.post('/add_user', tags=MAIN_TAG)
async def add_user(user_data: schemas.UserDataForm, pool=Depends(get_pool)):
    result = await db.add_user_db(pool, user_data)
    if result.success != True:
        if result.error_code == 'conflict':
            raise HTTPException(status_code=409, detail=result.message)
        raise HTTPException(status_code=500, detail=result.message)
    return result

@app.delete('/clear', tags=MAIN_TAG)
async def clear_all(password: schemas.PasswordForm, pool = Depends(get_pool)):
    result = await db.clear_all_db(pool, password)
    if not result.success:
        if result.error_code == 'unauthorized':
            raise HTTPException(status_code=401, detail=result.message)
        raise HTTPException(status_code=500, detail=result.message)
    return result

@app.delete('/delete_user', tags=MAIN_TAG)
async def delete_user(user_data: schemas.DeleteUserForm, pool = Depends(get_pool)):
    result = await db.delete_user_db(pool, user_data)
    if not result.success:
        if result.error_code == 'unauthorized':
            raise HTTPException(status_code=401, detail=result.message)
        if result.error_code == 'unknown_user':
            raise HTTPException(status_code=404, detail=result.message)
        raise HTTPException(status_code=500, detail=result.message)
    return result