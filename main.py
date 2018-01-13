import argparse
import asyncio
import logging
import json
from functools import wraps

import aiohttp
import colorlog
from async_timeout import timeout

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s %(levelname)s:%(name)s: %(white)s%(message)s',
    datefmt=None,
    reset=True))
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class Bot:
    def __init__(self, token, timeout):
        self.token = token
        self.timeout = timeout
        self.updates = Updates(self)
        self.queue = asyncio.Queue()
        self.handlers = {}
        self._polling = False

    @property
    def base_url(self):
        return f'https://api.telegram.org/bot{self.token}'

    async def dispatch(self, update):
        handler = self.handlers.get(update['message']['text'])
        if handler is not None:
            logger.debug('Dispatching...')
            result = await handler(update)
            return result
        logger.error('Handler not found')

    def on(self, message_text):
        def decorator(handler):
            self.handlers[message_text] = handler

            @wraps(handler)
            def wrapper(*args, **kwargs):
                return handler(*args, **kwargs)

            return wrapper

        return decorator

    async def reply(self, update, text):
        # TODO: Recall why exception (KeyError for instance)
        # is suppressed here and execution just hangs
        response = await self.make_request(
            'sendMessage', {'chat_id': update['message']['chat']['id'], 'text': text})
        logger.debug(response)
        return response

    async def make_request(self, method, payload=None):
        url = f'{self.base_url}/{method}'
        headers = {'content-type': 'application/json'}
        data = payload and json.dumps(payload)
        async with aiohttp.ClientSession() as client:
            async with client.post(url, data=data, headers=headers) as resp:
                logger.debug(resp.status)
                json_response = await resp.json()
                logger.debug(json_response)
                return json_response

    async def consume(self):
        while True:
            if not self._polling:
                break
            try:
                with timeout(self.timeout / 10):
                    update = await self.queue.get()
                    logger.debug(update)
                    await self.dispatch(update)
            except asyncio.TimeoutError:
                continue

    async def start_polling(self):
        self._polling = True
        async for updates in self.updates:
            for update in updates:
                await self.queue.put(update)

    def stop_polling(self):
        self._polling = False

    async def getUpdates(self, offset):
        logger.debug('Getting updates...')
        url = f'{self.base_url}/getUpdates?timeout={self.timeout}&offset={offset}'
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as resp:
                # TODO: Check response status
                json_response = await resp.json()
                return json_response


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


def parse_args():
    parser = argparse.ArgumentParser(description='Optimus arguments.')
    parser.add_argument('-t', '--token', metavar='token', type=str,
                        help='Telegram bot token', required=True)
    parser.add_argument('-to', '--timeout', metavar='timeout', type=int,
                        help='Telegram bot timeout', default=30)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    loop = asyncio.get_event_loop()
    bot = Bot(args.token, args.timeout)

    @bot.on('hello')
    async def hello_handler(update):
        await bot.reply(update, 'hello')

    poller = loop.create_task(bot.start_polling())
    consumer = loop.create_task(bot.consume())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('Shutting down...')
        bot.stop_polling()
        logger.info('Waiting for poller to complete')
        loop.run_until_complete(poller)
        logger.info('Waiting for consumer to complete')
        loop.run_until_complete(consumer)
        loop.close()
