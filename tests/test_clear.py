import pytest

@pytest.mark.asyncio
async def test_clear(session, url, password):
    clear_password = {'password': password}
    async with session.delete(f'{url}/clear', json=clear_password) as response:
        assert response.status == 200
        data = await response.json()
        assert 'Удалено' in data['message']

@pytest.mark.asyncio
async def test_wrong_password(session, url):
    async with session.delete(f'{url}/clear', json={'password': 'wrong'}) as response:
        assert response.status == 401
        data = await response.json()
        assert 'Неверный' in data['detail']