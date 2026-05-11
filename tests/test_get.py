import pytest

@pytest.mark.asyncio
async def test_get(session, url):
    async with session.get(f'{url}/users?limit=10&page=1') as response:
        assert response.status in [200, 404]

@pytest.mark.asyncio
async def test_get_stats(session, url):
    async with session.get(f'{url}/stats') as response:
        assert response.status in [200, 404]

@pytest.mark.asyncio
async def test_get_empty_stats(session, url, password):
    async with session.delete(f'{url}/clear', json={'password': password}) as response:
        assert response.status == 200
    async with session.get(f'{url}/stats') as response:
        assert response.status == 404

@pytest.mark.asyncio
async def test_empty_db(session, url, password):
    async with session.delete(f'{url}/clear', json={'password': password}) as response:
        assert response.status == 200
    async with session.get(f'{url}/users?limit=10&page=1') as response:
        assert response.status == 404
        data = await response.json()
        assert 'пуста' in data['detail']