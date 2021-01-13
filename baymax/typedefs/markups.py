from dataclasses import dataclass, field
from typing import Optional, List


class Markup:
    """
    Base class for all the markup entities.
    """


@dataclass
class CallbackGame(Markup):
    pass


@dataclass
class InlineKeyboardButton(Markup):
    text: str
    url: Optional[str] = None
    callback_data: Optional[str] = None
    switch_inline_query: Optional[str] = None
    switch_inline_query_current_chat: Optional[str] = None
    callback_game: Optional[CallbackGame] = None
    pay: Optional[bool] = None


@dataclass
class InlineKeyboardMarkup(Markup):
    inline_keyboard: List[List[InlineKeyboardButton]]


@dataclass
class KeyboardButton(Markup):
    text: str
    request_contact: bool = False
    request_location: bool = False


@dataclass
class ReplyKeyboardMarkup(Markup):
    keyboard: List[List[KeyboardButton]]
    resize_keyboard: bool = False
    one_time_keyboard: bool = False
    selective: bool = False


@dataclass
class ReplyKeyboardRemove(Markup):
    selective: bool = False
    remove_keyboard: bool = field(default=True, init=False)


@dataclass
class ForceReply(Markup):
    selective: bool = False
    force_reply: bool = field(default=True, init=False)
