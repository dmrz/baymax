import asyncio
import keyword
from collections import namedtuple
from enum import Enum
from functools import partial, wraps
from typing import Any, Callable, List, Optional

import uvloop
from async_timeout import timeout

from .api import TelegramApi
from .logger import get_logger
from .markups import Markup
from .storage import StorageInMemory

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def get_valid_key(key: str):
    return key if key not in keyword.kwlist else f"{key}_"


def get_namedtuple(name: str, **kwargs):
    return namedtuple(name, [get_valid_key(k) for k in kwargs])(
        **{
            get_valid_key(k): (
                v
                if not isinstance(v, dict)
                else get_namedtuple(k.title().replace("_", ""), **v)
            )
            for k, v in kwargs.items()
        }
    )


class ParseMode(Enum):
    HTML: str = "HTML"
    MARKDOWN: str = "Markdown"


class Bot:
    logger = get_logger(__name__)

    def __init__(self, token, timeout=30):
        self.api = TelegramApi(f"https://api.telegram.org/bot{token}")
        self.timeout = timeout
        self.queue = asyncio.Queue()
        self.middlewares = set()
        self.handlers = {}
        self.fsm_handlers = {}
        self.fsm_transition_handlers = {}
        self.callback_query_handler = None
        self.update_id = 0
        self._polling = False
        self._storage = StorageInMemory()

    async def dispatch(self, update):
        # TODO: Maybe we need to make it possible to add ordered middlewares
        # TODO: Do we really need to wait until all the middlewares are done?
        try:
            await asyncio.gather(
                *[middleware(update) for middleware in self.middlewares]
            )
        except Exception:
            self.logger.exception("Middleware error")
            return

        # TODO: Improve dispatching (especially for callback query handler)
        if "message" in update:
            payload = get_namedtuple("Message", **update["message"])
            # Trying to handle it using transition handlers
            state = await self.get_state(payload.from_)
            # FIXME: Do we need a protection for
            # transition handler with key None?
            transition_handler = self.fsm_transition_handlers.get(state)
            if transition_handler is not None:
                if not all(
                    cond(payload.text)
                    for cond in transition_handler["conditions"] or []
                ):
                    self.logger.debug("Did not pass conditions check")
                    return
                if transition_handler["terminate"]:
                    await self.delete_state(payload.from_)
                else:
                    await self.set_state(
                        payload.from_, transition_handler["target"]
                    )
                handler = transition_handler["handler"]
            else:
                # Trying to handle using FSM handler
                fsm_handler = self.fsm_handlers.get(payload.text)
                if fsm_handler is not None:
                    await self.set_state(payload.from_, fsm_handler["target"])
                    handler = fsm_handler["handler"]
                # Trying to handle using main handler
                else:
                    handler = self.handlers.get(payload.text)
                    if handler is None:
                        self.logger.error(
                            "Handler not found for %s", payload.text
                        )
                        return
        elif "callback_query" in update:
            payload = get_namedtuple(
                "CallbackQuery", **update["callback_query"]
            )
            handler = self.callback_query_handler
            if handler is None:
                self.logger.error("Callback query handler not set")
                return
        else:
            self.logger.error("Unhandled error")
            return

        self.logger.debug("Dispatching...")
        try:
            result = await asyncio.shield(handler(payload))
        except Exception:
            # FIXME: Find out why there's CancelledError sometimes here
            # NOTE: Shield is a temporary workaround for an issue above.
            self.logger.exception("Handler error")
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

    def fsm(
        self, message_text: str, target: str
    ) -> Callable[[Callable[[Any], Any]], Any]:
        def decorator(handler):
            self.fsm_handlers[message_text] = {
                "handler": handler,
                "target": target,
            }

            @wraps(handler)
            def wrapper(*args, **kwargs):
                return handler(*args, **kwargs)

            return wrapper

        return decorator

    def fsm_transition(
        self,
        *,
        source: str,
        target: Optional[str] = None,
        conditions: Optional[List[Callable[[str], bool]]] = None,
        terminate: bool = False,
    ) -> Callable[[Callable[[Any], Any]], Any]:
        def decorator(handler):
            self.fsm_transition_handlers[source] = {
                "handler": handler,
                "target": target,
                "conditions": conditions,
                "terminate": terminate,
            }

            @wraps(handler)
            def wrapper(*args, **kwargs):
                return handler(*args, **kwargs)

            return wrapper

        return decorator

    async def reply(
        self,
        message,
        text: str,
        parse_mode: Optional[ParseMode] = None,
        reply_markup: Optional[Markup] = None,
    ):
        if isinstance(parse_mode, ParseMode):
            parse_mode = parse_mode.value
        response = await self.api.send_message(
            message.chat.id,
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
        self.logger.debug(response)
        return response

    async def reply_html(self, *args, **kwargs):
        return await partial(self.reply, parse_mode=ParseMode.HTML)(
            *args, **kwargs
        )

    async def reply_markdown(self, *args, **kwargs):
        return await partial(self.reply, parse_mode=ParseMode.MARKDOWN)(
            *args, **kwargs
        )

    async def answer_callback_query(
        self,
        callback_query,
        text: str,
        show_alert: bool = False,
        url: Optional[str] = None,
        cache_time: Optional[int] = None,
    ):
        response = await self.api.answer_callback_query(
            callback_query.id, text, show_alert, url, cache_time
        )
        self.logger.debug(response)
        return response

    async def consume(self):
        while self._polling:
            try:
                with timeout(self.timeout / 10):
                    update = await self.queue.get()
                    self.logger.debug("Got update: %s", update)
                await self.dispatch(update)
            except Exception as e:
                if not isinstance(e, asyncio.TimeoutError):
                    self.logger.exception("Dispatch error")
                continue

    async def start_polling(self):
        self._polling = True
        try:
            async for update in self.update_generator():
                await self.queue.put(update)
        except Exception:
            self.logger.exception("Polling cancelled")

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
        self.logger.debug("Getting updates...")
        response = await self.api.get_updates(self.timeout, self.update_id + 1)
        updates = response["result"]
        if updates:
            self.update_id = max(r["update_id"] for r in updates)
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
            self.logger.info("Shutting down...")
            self.stop_polling()
            self.logger.info("Waiting for poller to complete")
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(poller)
            self.logger.info("Waiting for consumer to complete")
            loop.run_until_complete(consumer)
            loop.close()

    async def set_state(self, user, state):
        await self._storage.set(f"state-{user.id}", state)

    async def get_state(self, user):
        state = await self._storage.get(f"state-{user.id}")
        return state

    async def delete_state(self, user):
        await self._storage.delete(f"state-{user.id}")

