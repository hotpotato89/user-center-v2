import pytest
import aiohttp
from time import time
from random import randint
from typing import Dict
from os import getenv
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as sess:
        yield sess

@pytest.fixture
async def url():
    return f'http://localhost:8000'

@pytest.fixture
async def random_user() -> Dict:
    userdata = {
        'name': f'user-{randint(1, 100000)}',
        'age': randint(10, 50),
        'email': f'test-{time()}@example.com'
    }
    return userdata

@pytest.fixture
def password():
    return getenv('ADMIN_PASSWORD')

@pytest.fixture(autouse=True)
async def flush_redis(session, url):
    await session.get(f'{url}/__flush_redis__')
    yield
    await session.get(f'{url}/__flush_redis__')