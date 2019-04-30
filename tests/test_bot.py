import asyncio

import pytest

from async_timeout import timeout


pytestmark = pytest.mark.asyncio


# async def test_bot(loop, event_loop, bot):
#     @bot.on("hello")
#     async def hello_handler(message):
#         await bot.reply(message, "hello")

#     await bot.start_polling()
#     # bot.run()
#     # task = asyncio.create_task(bot.start_polling())
#     # await task


# async def test_timeout(event_loop, loop):
#     async with timeout(5, loop=event_loop):
#         await asyncio.sleep(3, loop=event_loop)
#         assert 1 == 1
