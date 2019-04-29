from collections import UserDict
from dataclasses import asdict, dataclass, field
from json import JSONEncoder
from typing import Dict, Optional, List


class NoneLessDict(UserDict):
    """
    Dictionary that cannot have None as a value.
    """

    def __setitem__(self, key, value) -> None:
        if value is not None:
            super().__setitem__(key, value)


class Markup:
    """
    Base class for all the markup entities.
    """


class MarkupJSONEncoder(JSONEncoder):
    def default(self, o) -> Dict:
        if isinstance(o, Markup):
            return asdict(o, dict_factory=NoneLessDict)
        if isinstance(o, UserDict):
            return o.data
        return super().default()


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
