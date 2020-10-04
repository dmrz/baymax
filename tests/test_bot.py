import asyncio
from collections import deque

import pytest
from aiohttp import web

from baymax.trafarets import Chat, Message, Update, User


pytestmark = pytest.mark.asyncio


async def test_bot_hello(
    loop, bot, telegram_endpoint_handler_registry, tfaker
):
    updates = deque()
    update = tfaker.t_dict(Update)
    message = tfaker.t_dict(Message)
    message["text"] = "hello"
    chat = tfaker.t_dict(Chat)
    message["chat"] = chat
    user = tfaker.t_dict(User)
    message["from"] = user
    update["message"] = message
    updates.append(update)

    async def get_updates(request: web.Request) -> web.Response:
        result = []
        try:
            update = updates.pop()
            result.append(update)
        except IndexError:
            await asyncio.sleep(bot.timeout)

        return web.json_response({"result": result})

    send_message_payload_future = asyncio.Future()

    async def send_message(request: web.Request) -> web.Response:
        payload = await request.json()
        send_message_payload_future.set_result(payload)
        return web.json_response({"result": tfaker.t_dict(Message)})

    telegram_endpoint_handler_registry.register("getUpdates", get_updates)
    telegram_endpoint_handler_registry.register("sendMessage", send_message)

    @bot.on("hello")
    async def hello_handler(update):
        await bot.reply("hello")

    bot_task = asyncio.create_task(bot.main())

    send_message_payload = await send_message_payload_future
    assert send_message_payload["chat_id"] == chat["id"]
    assert send_message_payload["text"] == "hello"

    print('cancelling bot task')
    bot_task.cancel()
    print('unwrapping')
    await loop.shutdown_asyncgens()
    # await bot_task
