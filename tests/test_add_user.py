import pytest

@pytest.mark.asyncio
async def test_add_user(session, url, random_user):
    async with session.post(f'{url}/add_user', json=random_user) as response:
        assert response.status == 200

@pytest.mark.asyncio
async def test_try_copy_email(session, url, random_user):
    async with session.post(f'{url}/add_user', json=random_user) as response:
        assert response.status == 200
    async with session.post(f'{url}/add_user', json=random_user) as response:
        assert response.status == 409
        data = await response.json()
        assert 'существует' in data['detail']