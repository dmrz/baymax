from uuid import uuid4

import pytest
from aiohttp import web
from hypothesis import settings

from baymax.bot import Bot

pytest_plugins = ["aiohttp.pytest_plugin", "pytester"]

settings.register_profile(
    "local", max_examples=3, database=None, deadline=None
)

settings.register_profile("complex", max_examples=1000)


def get_telegram_endpoint_handler(faker):
    async def telegram_endpoint(request):
        token = request.match_info["token"]
        return web.Response(text=f"Hello, {token}")

    return telegram_endpoint


@pytest.fixture
async def telegram_server(aiohttp_server, faker):
    app = web.Application()
    app.router.add_post(
        "/bot{token}/{method:.*}", get_telegram_endpoint_handler(faker)
    )
    server = await aiohttp_server(app)
    yield server


@pytest.fixture
def bot(event_loop, telegram_server):
    token = uuid4().hex
    api_url = telegram_server.make_url(f"/bot{token}")
    yield Bot(token=token, timeout=10, api_url=api_url)
