import asyncio
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from functools import partial, wraps
from logging import Logger
from typing import Any, Callable, Dict, List, Optional, Awaitable, Set, Text

# import uvloop
from async_timeout import timeout

from .api import TelegramApi
from .logger import get_logger
from .markups import Markup
from .trafarets import Update
from .storage import BaseStorage, StorageInMemory

# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class ParseMode(Enum):
    HTML: str = "HTML"
    MARKDOWN: str = "Markdown"


@dataclass
class Bot:
    token: str
    timeout: int = 30
    api_url: Optional[str] = None
    loop: Optional[asyncio.AbstractEventLoop] = None
    logger: Logger = field(default=get_logger(__name__), init=False)
    queue: asyncio.Queue = field(default_factory=asyncio.Queue, init=False)
    middlewares: Set[Awaitable] = field(default_factory=set, init=False)
    handlers: Dict[Text, Awaitable] = field(default_factory=dict, init=False)
    fsm_handlers: Dict[Text, Awaitable] = field(
        default_factory=dict, init=False
    )
    fsm_transition_handlers: Dict[Text, Awaitable] = field(
        default_factory=dict, init=False
    )
    callback_query_handler: Optional[Awaitable] = field(
        default=None, init=False
    )
    update_id: int = field(default=0, init=False)
    _polling: bool = field(default=False, init=False)
    _storage: BaseStorage = field(default_factory=StorageInMemory, init=False)

    # contextvars
    _update_var: Dict[Text, Any] = field(
        default=ContextVar("update"), init=False
    )

    def __post_init__(self):
        if self.api_url is None:
            self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.api = TelegramApi(self.api_url)
        # if self.loop is None:
        #     self.loop = asyncio.get_event_loop()
        # else:
        #     self.queue = asyncio.Queue(loop=self.loop)

    async def dispatch(self, update):

        # TODO: ISOLATE CONTEXT SO CONTEXTVARS WORK CORRECTLY BY RUNNING EVERYTHING IN A NEW TASK

        # TODO: Maybe we need to make it possible to add ordered middlewares
        # TODO: Do we really need to wait until all the middlewares are done?
        try:
            await asyncio.gather(
                *[middleware(update) for middleware in self.middlewares]
            )
        except Exception:
            self.logger.exception("Middleware error")
            return

        update = Update(update)

        # TODO: Improve dispatching (especially for callback query handler)
        if "message" in update:
            # Trying to handle it using transition handlers
            state = await self.get_state(update)
            # FIXME: Do we need a protection for
            # transition handler with key None?
            transition_handler = self.fsm_transition_handlers.get(state)
            if transition_handler is not None:
                if not all(
                    cond(update["message"]["text"])
                    for cond in transition_handler["conditions"] or []
                ):
                    self.logger.debug("Did not pass conditions check")
                    return
                if transition_handler["terminate"]:
                    await self.delete_state(update)
                else:
                    await self.set_state(update, transition_handler["target"])
                handler = transition_handler["handler"]
            else:
                # Trying to handle using FSM handler
                fsm_handler = self.fsm_handlers.get(update["message"]["text"])
                if fsm_handler is not None:
                    await self.set_state(update, fsm_handler["target"])
                    handler = fsm_handler["handler"]
                # Trying to handle using main handler
                else:
                    handler = self.handlers.get(update["message"]["text"])
                    if handler is None:
                        self.logger.error(
                            "Handler not found for %s",
                            update["message"]["text"],
                        )
                        return
        elif "callback_query" in update:
            handler = self.callback_query_handler
            if handler is None:
                self.logger.error("Callback query handler not set")
                return
        else:
            self.logger.error("Unhandled error")
            return

        self.logger.debug("Dispatching...")
        try:
            self._update_var.set(update)
            result = await asyncio.shield(handler(update))
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
        text: str,
        parse_mode: Optional[ParseMode] = None,
        reply_markup: Optional[Markup] = None,
    ):
        if isinstance(parse_mode, ParseMode):
            parse_mode = parse_mode.value
        update = self._update_var.get()
        self.logger.info("Current update context var, %s", update)
        response = await self.api.send_message(
            # FIXME: Message can be empty
            update["message"]["chat"]["id"],
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
        text: str,
        show_alert: bool = False,
        url: Optional[str] = None,
        cache_time: Optional[int] = None,
    ):
        update = self._update_var.get()
        response = await self.api.answer_callback_query(
            update["callback_query"]["id"], text, show_alert, url, cache_time
        )
        self.logger.debug(response)
        return response

    async def consume(self):
        while self._polling:
            try:
                # async with timeout(self.timeout / 10, loop=self.loop):
                async with timeout(self.timeout / 10):
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
                # async with timeout(self.timeout, loop=self.loop):
                async with timeout(self.timeout):
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

        if loop.is_running():
            return

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

    # FIXME: from.id is not available for messages sent to channels so we need
    # to use some other unique identifier for setting state
    # (probably chat.id if it's type is channel).

    async def set_state(self, update, state):
        await self._storage.set(
            f"state-{update['message']['from']['id']}", state
        )

    async def get_state(self, update):
        state = await self._storage.get(
            f"state-{update['message']['from']['id']}"
        )
        return state

    async def delete_state(self, update):
        await self._storage.delete(f"state-{update['message']['from']['id']}")

