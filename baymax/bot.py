import asyncio
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import partial, wraps
from typing import Any, Callable, Dict, List, Optional, Awaitable, Set, Text

from async_timeout import timeout

from .base import BaseTelegramApi, BaseStorage
from .markups import Markup, ParseMode
from .settings import BotSettings
from .trafarets import Update


@dataclass
class Bot:
    api: BaseTelegramApi
    storage: BaseStorage
    settings: BotSettings

    # bot instance settings
    queue: Optional[asyncio.Queue] = field(default=None, init=False)
    middlewares: Set[Awaitable] = field(default_factory=set, init=False)
    handlers: Dict[Text, Awaitable] = field(default_factory=dict, init=False)
    fsm_handlers: Dict[Text, Awaitable] = field(default_factory=dict, init=False)
    fsm_transition_handlers: Dict[Text, Awaitable] = field(
        default_factory=dict, init=False
    )
    callback_query_handler: Optional[Awaitable] = field(default=None, init=False)
    inline_query_handler: Optional[Awaitable] = field(default=None, init=False)
    update_id: int = field(default=0, init=False)
    _polling: bool = field(default=False, init=False)

    # contextvars
    _update_var: Dict[Text, Any] = field(default=ContextVar("update"), init=False)

    async def dispatch(self, update):

        # TODO: ISOLATE CONTEXT SO CONTEXTVARS WORK CORRECTLY BY RUNNING EVERYTHING IN A NEW TASK

        # TODO: Maybe we need to make it possible to add ordered middlewares
        # TODO: Do we really need to wait until all the middlewares are done?
        try:
            await asyncio.gather(
                *[middleware(update) for middleware in self.middlewares]
            )
        except Exception:
            self.settings.logger.exception("Middleware error")
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
                    self.settings.logger.debug("Did not pass conditions check")
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
                        self.settings.logger.error(
                            "Handler not found for %s",
                            update["message"]["text"],
                        )
                        return
        elif "callback_query" in update:
            handler = self.callback_query_handler
            if handler is None:
                self.settings.logger.error("Callback query handler not set")
                return
        elif "inline_query" in update:
            handler = self.inline_query_handler
            if handler is None:
                self.settings.logger.error("Inline query handler is not set")
                return
        else:
            self.settings.logger.error("Unhandled error")
            return

        self.settings.logger.debug("Dispatching...")
        try:
            # Running update handling in task for contextvars to be happy
            result = await asyncio.create_task(self._handle_update(handler, update))
        except Exception:
            # FIXME: Find out why there's CancelledError sometimes here
            # NOTE: Shield is a temporary workaround for an issue above.
            self.settings.logger.exception("Handler error")
        else:
            return result

    async def _handle_update(self, handler, update):
        self._update_var.set(update)
        return await asyncio.shield(handler(update))

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

    @property
    def inline_query(self):
        """
        Registers inline query handler.
        """

        def decorator(handler):
            self.inline_query_handler = handler

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
        self.settings.logger.info("Current update context var, %s", update)
        response = await self.api.send_message(
            # FIXME: Message can be empty
            update["message"]["chat"]["id"],
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
        self.settings.logger.debug(response)
        return response

    async def reply_html(self, *args, **kwargs):
        return await partial(self.reply, parse_mode=ParseMode.HTML)(*args, **kwargs)

    async def reply_markdown(self, *args, **kwargs):
        return await partial(self.reply, parse_mode=ParseMode.MARKDOWN)(*args, **kwargs)

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
        self.settings.logger.debug(response)
        return response

    async def consume(self):
        while self._polling:
            try:
                async with timeout(self.settings.timeout / 10):
                    update = await self.queue.get()
                    self.settings.logger.debug("Got update: %s", update)
                await self.dispatch(update)
            except asyncio.CancelledError:
                self.settings.logger.info("Consuming cancelled")
                return
            except Exception as e:
                if not isinstance(e, asyncio.TimeoutError):
                    self.settings.logger.exception("Dispatch error")
                continue

    async def start_polling(self):
        self._polling = True
        try:
            async for update in self.update_generator():
                await self.queue.put(update)
        except asyncio.CancelledError:
            self.settings.logger.info("Polling cancelled")
            return
        except Exception:
            self.settings.logger.exception("Polling cancelled unexpectedly")

    def stop_polling(self):
        self._polling = False

    async def update_generator(self):
        while self._polling:
            try:
                async with timeout(self.settings.timeout):
                    updates = await self.get_updates()
            except asyncio.TimeoutError:
                continue
            else:
                for update in updates:
                    yield update

    async def get_updates(self):
        self.settings.logger.debug("Getting updates...")
        response = await self.api.get_updates(self.settings.timeout, self.update_id + 1)
        updates = response["result"]
        if updates:
            self.update_id = max(r["update_id"] for r in updates)
        return updates

    async def setup(self):
        # Prepare artifacts
        self.queue = asyncio.Queue()

    async def main(self):
        """
        Main entry point for running all the bot dependent async tasks.
        """

        await self.setup()

        # Run workers
        poller = asyncio.create_task(self.start_polling())
        consumer = asyncio.create_task(self.consume())
        await asyncio.gather(poller, consumer)

    def run(self):
        try:
            asyncio.run(self.main())
        except KeyboardInterrupt:
            pass

    # FIXME: from.id is not available for messages sent to channels so we need
    # to use some other unique identifier for setting state
    # (probably chat.id if it's type is channel).

    async def set_state(self, update, state):
        await self.storage.set(f"state-{update['message']['from']['id']}", state)

    async def get_state(self, update):
        state = await self.storage.get(f"state-{update['message']['from']['id']}")
        return state

    async def delete_state(self, update):
        await self.storage.delete(f"state-{update['message']['from']['id']}")
