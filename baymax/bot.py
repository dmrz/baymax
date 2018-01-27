import asyncio
import json
import keyword
from collections import UserDict, namedtuple
from functools import wraps
from typing import Callable, Optional

import aiohttp
import uvloop
from async_timeout import timeout

from .logger import get_logger
from .markups import ReplyMarkup


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def get_valid_key(key: str):
    return key if key not in keyword.kwlist else f'{key}_'


def get_namedtuple(name: str, **kwargs):
    return namedtuple(name, [get_valid_key(k) for k in kwargs])(
        **{get_valid_key(k): (v if not isinstance(v, dict) else get_namedtuple(
            k.title().replace('_', ''), **v))
           for k, v in kwargs.items()})


class Bot:
    logger = get_logger(__name__)

    def __init__(self, token, timeout=30):
        self.token = token
        self.timeout = timeout
        self.queue = asyncio.Queue()
        self.middlewares = set()
        self.handlers = {}
        self.state_handlers = {}
        self.state_predicates = {}
        self.callback_query_handler = None
        self.update_id = 0
        self._polling = False
        self._storage = Storage()

    @property
    def base_url(self):
        return f'https://api.telegram.org/bot{self.token}'

    async def dispatch(self, update):
        # TODO: Maybe we need to make it possible to add ordered middlewares
        # TODO: Do we really need to wait until all the middlewares are done?
        try:
            await asyncio.gather(
                *[middleware(update) for middleware in self.middlewares])
        except Exception:
            # FIXME: Find out why it sometimes fails with CancelledError
            self.logger.exception('Middleware error')
            return

        # TODO: Improve dispatching (especially for callback query handler)
        if 'message' in update:
            payload = get_namedtuple('Message', **update['message'])
            # Trying to handle it using state handlers
            state = await self.get_state(payload.from_)
            if state is not None:
                predicate = self.state_predicates.get(state)
                if predicate is not None:
                    if not predicate(payload.text):
                        return
                else:
                    self.logger.debug('No predicate found for state %s', state)

                handler = self.state_handlers.get(state)
                if handler is None:
                    self.logger.error('State handler %s not found for user %d',
                                      state, payload.from_.id)
            else:
                handler = self.handlers.get(payload.text)
                if handler is None:
                    self.logger.error('Handler not found for %s', payload.text)
                    return
        elif 'callback_query' in update:
            payload = get_namedtuple(
                'CallbackQuery', **update['callback_query'])
            handler = self.callback_query_handler
            if handler is None:
                self.logger.error('Callback query handler not set')
                return
        else:
            self.logger.error('Unhandled error')
            return

        self.logger.debug('Dispatching...')
        try:
            result = await handler(payload)
        except Exception:
            self.logger.exception('Handler error')
        else:
            return result

    @property
    def callback_query(self):
        def decorator(handler):
            self.callback_query_handler = handler

            @wraps(handler)
            def wrapper(*args, **kwargs):
                return handler(*args, **kwargs)

            return wrapper

        return decorator

    @property
    def middleware(self):
        def decorator(middleware):
            self.middlewares.add(middleware)

            @wraps(middleware)
            def wrapper(*args, **kwargs):
                return middleware(*args, **kwargs)

            return wrapper

        return decorator

    def on(self, message_text: str):
        def decorator(handler):
            self.handlers[message_text] = handler

            @wraps(handler)
            def wrapper(*args, **kwargs):
                return handler(*args, **kwargs)

            return wrapper

        return decorator

    def on_state(self, state: str,
                 predicate: Optional[Callable[[str], bool]] = None):
        def decorator(handler):
            self.state_handlers[state] = handler
            if predicate is not None:
                self.state_predicates[state] = predicate

            @wraps(handler)
            def wrapper(*args, **kwargs):
                return handler(*args, **kwargs)

            return wrapper

        return decorator

    async def reply(self, message, text: str,
                    reply_markup: Optional[ReplyMarkup] = None):
        payload = {
            'chat_id': message.chat.id,
            'text': text
        }
        if isinstance(reply_markup, ReplyMarkup):
            payload['reply_markup'] = reply_markup.get_serializable()
        response = await self.make_request('sendMessage', payload)
        self.logger.debug(response)
        return response

    async def answer_callback_query(self, callback_query, text: str,
                                    show_alert: bool = False,
                                    url: Optional[str] = None,
                                    cache_time: Optional[int] = None):
        payload = {
            'callback_query_id': callback_query.id,
            'text': text,
            'show_alert': show_alert
        }
        if url is not None:
            payload['url'] = url
        if cache_time is not None:
            payload['cache_time'] = cache_time
        response = await self.make_request('answerCallbackQuery', payload)
        self.logger.debug(response)
        return response

    async def make_request(self, method, payload=None, params=None):
        url = f'{self.base_url}/{method}'
        headers = {'content-type': 'application/json'}
        data = payload and json.dumps(payload)
        # FIXME: Sometimes CancelledError is raised on create_connection
        async with aiohttp.ClientSession() as client:
            async with client.post(
                    url, data=data, params=params, headers=headers) as resp:
                # TODO: Check response status
                json_response = await resp.json()
                return json_response

    async def consume(self):
        while self._polling:
            try:
                with timeout(self.timeout / 10):
                    update = await self.queue.get()
            except asyncio.TimeoutError:
                continue
            else:
                self.logger.debug('Got update: %s', update)
                await self.dispatch(update)

    async def start_polling(self):
        self._polling = True
        try:
            async for update in self.update_generator():
                await self.queue.put(update)
        except Exception:
            self.logger.exception('Polling cancelled')

    def stop_polling(self):
        self._polling = False

    async def update_generator(self):
        while True:
            try:
                with timeout(self.timeout):
                    updates = await self.get_updates()
            except asyncio.TimeoutError:
                continue
            else:
                for update in updates:
                    yield update

    async def get_updates(self):
        self.logger.debug('Getting updates...')
        params = {
            'timeout': self.timeout,
            'offset': self.update_id + 1
        }
        response = await self.make_request('getUpdates', params=params)
        updates = response['result']
        if updates:
            self.update_id = max(r['update_id'] for r in updates)
        return updates

    def run(self):
        loop = asyncio.get_event_loop()

        poller = loop.create_task(self.start_polling())
        consumer = loop.create_task(self.consume())

        try:
            loop.run_forever()
        # TODO: Handle termination in a more neat way (using signals)
        except KeyboardInterrupt:
            # TODO: Simplify shutdown
            self.logger.info('Shutting down...')
            self.stop_polling()
            self.logger.info('Waiting for poller to complete')
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(poller)
            self.logger.info('Waiting for consumer to complete')
            loop.run_until_complete(consumer)
            loop.close()

    async def set_state(self, user, state):
        await self._storage.set(f'state-{user.id}', state)

    async def get_state(self, user):
        state = await self._storage.get(f'state-{user.id}')
        return state

    async def delete_state(self, user):
        await self._storage.delete(f'state-{user.id}')


class Storage(UserDict):
    async def set(self, key, value):
        self.data[key] = value

    async def get(self, key):
        return self.data.get(key)

    async def delete(self, key):
        if key in self.data:
            del self.data[key]
