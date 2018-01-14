import asyncio

from async_timeout import timeout


class Updates:
    def __init__(self, bot):
        self.bot = bot
        self.update_id = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            if not self.bot._polling:
                break

            try:
                with timeout(self.bot.timeout):
                    response = await self.bot.getUpdates(self.update_id + 1)
                    result = response['result']

                    if not result:
                        continue

                    self.update_id = max(r['update_id'] for r in result)
                    return result
            except asyncio.TimeoutError:
                continue

        raise StopAsyncIteration
