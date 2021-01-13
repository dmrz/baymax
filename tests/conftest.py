from collections import UserDict
from dataclasses import dataclass, field
from functools import partial
from typing import Awaitable, Callable
from uuid import uuid4

import pytest
from aiohttp import web
from hypothesis import settings

from baymax.bot import Bot
from baymax.default.api import TelegramApi
from baymax.default.storage import StorageInMemory
from baymax.settings import Settings

from testutils.trafaret_faker_provider import Provider

pytest_plugins = ["aiohttp.pytest_plugin", "pytester"]

settings.register_profile("local", max_examples=3, database=None, deadline=None)

settings.register_profile("complex", max_examples=1000)


class TelegramEndpointHandlerRegistry(UserDict):
    def register(
        self,
        endpoint: str,
        handler: Callable[[web.Request], Awaitable[web.Response]],
    ) -> None:
        self[endpoint] = handler

    async def _default(self, endpoint: str, request: web.Request) -> web.Response:
        return web.json_response({"error": f"Missing {endpoint} handler"}, status=500)

    async def dispatch(self, endpoint: str, request: web.Request) -> web.Response:
        handler = self.get(endpoint, partial(self._default, endpoint))
        return await handler(request)


@pytest.fixture
async def telegram_endpoint_handler_registry():
    handler_registry = TelegramEndpointHandlerRegistry()
    yield handler_registry


@pytest.fixture
async def telegram_endpoint_dispatcher_factory(telegram_endpoint_handler_registry):
    async def telegram_endpoint(request):
        # token = request.match_info["token"]
        endpoint = request.match_info["endpoint"]
        return await telegram_endpoint_handler_registry.dispatch(endpoint, request)

    return telegram_endpoint


@pytest.fixture
async def telegram_server(
    event_loop, aiohttp_server, telegram_endpoint_dispatcher_factory
):
    # Create server
    app = web.Application()
    app.router.add_post(
        "/bot{token}/{endpoint:.*}", telegram_endpoint_dispatcher_factory
    )
    server = await aiohttp_server(app)
    yield server
    # Cleanup


@pytest.fixture
async def bot(event_loop, telegram_server):
    # Create bot
    settings = Settings(
        token=uuid4().hex, base_api_url=telegram_server.make_url("/bot"), timeout=10
    )
    # TODO: Do DI here like in baymax.default?
    bot = Bot(TelegramApi(settings), StorageInMemory(), settings)
    yield bot


@pytest.fixture
def tfaker(faker):
    faker.add_provider(Provider)
    yield faker
