from fastapi import FastAPI, Request, Depends, HTTPException, Query
from time import perf_counter
from typing import Annotated
from asyncpg import Pool

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

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def main_page():
    return FileResponse('static/index.html')

async def get_pool():
    return app.state.pool

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
    result = await db.get_stats_db(pool)
    if not result.success:
        if result.error_code == 'empty':
            raise HTTPException(status_code=404, detail=result.message)
    return result

@app.get('/health', tags=MAIN_TAG)
async def healthcheck():
    return schemas.ReturnForm(success=True, message='Healthy')

@app.get('/users', tags=MAIN_TAG)
async def get_users(pool = Depends(get_pool),
                    limit: int = Query(..., ge=1, description='Лимит записей в одной странице'),
                    page: int = Query(..., ge=1, description='Какая страница будет просмотрена')):
    limit = min(limit, 50)
    skip = (page-1)*limit
    result = await db.get_users_db(pool=pool, limit=limit, skip=skip)
    if result.success != True:
        if result.error_code == 'empty':
            raise HTTPException(status_code=404, detail=result.message)
        raise HTTPException(status_code=500, detail=result.message)
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