from collections import UserDict
from dataclasses import dataclass, field
from functools import partial
from typing import Awaitable, Callable
from uuid import uuid4

import pytest
from aiohttp import web
from hypothesis import settings

from baymax.bot import Bot

from .trafaret_faker_provider import Provider

pytest_plugins = ["aiohttp.pytest_plugin", "pytester"]

settings.register_profile("local", max_examples=3, database=None, deadline=None)

settings.register_profile("complex", max_examples=1000)


class TelegramEndpointHandlerRegistry(UserDict):
    def register(
        self,
        method: str,
        handler: Callable[[web.Request], Awaitable[web.Response]],
    ) -> None:
        self[method] = handler

    async def _default(self, method: str, request: web.Request) -> web.Response:
        return web.json_response({"error": f"Missing {method} handler"}, status=500)

    async def dispatch(self, method: str, request: web.Request) -> web.Response:
        handler = self.get(method, partial(self._default, method))
        return await handler(request)


@pytest.fixture
async def telegram_endpoint_handler_registry():
    handler_registry = TelegramEndpointHandlerRegistry()
    yield handler_registry


@pytest.fixture
async def telegram_endpoint_dispatcher_factory(telegram_endpoint_handler_registry):
    async def telegram_endpoint(request):
        # token = request.match_info["token"]
        method = request.match_info["method"]
        return await telegram_endpoint_handler_registry.dispatch(method, request)

    return telegram_endpoint


# @pytest.fixture
# async def telegram_server(
#     aiohttp_server, telegram_endpoint_dispatcher_factory
# ):
#     app = web.Application()
#     app.router.add_post(
#         "/bot{token}/{method:.*}", telegram_endpoint_dispatcher_factory
#     )
#     server = await aiohttp_server(app)
#     yield server


@pytest.fixture
async def bot(event_loop, aiohttp_server, telegram_endpoint_dispatcher_factory):

    # Create server
    app = web.Application()
    app.router.add_post("/bot{token}/{method:.*}", telegram_endpoint_dispatcher_factory)
    server = await aiohttp_server(app)

    # Create bot
    token = uuid4().hex
    api_url = server.make_url(f"/bot{token}")
    yield Bot(token=token, timeout=10, api_url=api_url)


@pytest.fixture
def tfaker(faker):
    faker.add_provider(Provider)
    yield faker
