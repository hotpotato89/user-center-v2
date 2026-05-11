import pytest
import aiohttp

@pytest.mark.asyncio
async def test_health(session, url):
    async with session.get(f'{url}/health') as response:
        assert response.status == 200