import pytest
from os import getenv

@pytest.mark.asyncio
async def test_delete_user(session, url, random_user, password):
    async with session.post(f'{url}/add_user', json=random_user) as response:
        assert response.status == 200
        data = await response.json()
    delete_data = {
        'id': int(data['id']),
        'password': password
    }
    async with session.delete(f'{url}/delete_user', json=delete_data) as response:
        assert response.status == 200

@pytest.mark.asyncio
async def test_delete_unknown(session, url, password):
    unknown_user = {
        'id': 2100000000,
        'password': password
    }
    async with session.delete(f'{url}/delete_user', json=unknown_user) as response:
        assert response.status == 404
        data = await response.json()
        assert 'Нет' in data['detail']

async def test_wrong_password(session, url, random_user):
    async with session.post(f'{url}/add_user', json=random_user) as response:
        assert response.status == 200
        data = await response.json()
    delete_data = {
        'id': int(data['id']),
        'password': 'wrong'
    }
    async with session.delete(f'{url}/delete_user', json=delete_data) as response:
        assert response.status == 401
        data = await response.json()
        assert 'Неверный' in data['detail']