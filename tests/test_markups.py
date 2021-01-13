import json
from dataclasses import asdict

import pytest

from baymax.typedefs.markups import (
    CallbackGame,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ForceReply,
    MarkupJSONEncoder,
    NoneLessDict,
)


def test_inline_keyboard_button():
    inline_keyboard_button = InlineKeyboardButton(
        "click me", callback_data="result"
    )
    assert asdict(inline_keyboard_button) == {
        "text": "click me",
        "url": None,
        "callback_data": "result",
        "switch_inline_query": None,
        "switch_inline_query_current_chat": None,
        "callback_game": None,
        "pay": None,
    }
    assert asdict(inline_keyboard_button, dict_factory=NoneLessDict) == {
        "text": "click me",
        "callback_data": "result",
    }
    inline_keyboard_button = InlineKeyboardButton(
        "click me", callback_data="result", callback_game=CallbackGame()
    )
    assert asdict(inline_keyboard_button) == {
        "text": "click me",
        "url": None,
        "callback_data": "result",
        "switch_inline_query": None,
        "switch_inline_query_current_chat": None,
        "callback_game": {},
        "pay": None,
    }
    assert asdict(inline_keyboard_button, dict_factory=NoneLessDict) == {
        "text": "click me",
        "callback_data": "result",
        "callback_game": {},
    }


def test_keyboard_button():
    keyboard_button = KeyboardButton("click me")
    assert asdict(keyboard_button) == {
        "text": "click me",
        "request_contact": False,
        "request_location": False,
    }
    keyboard_button = KeyboardButton("click me", True, True)
    assert asdict(keyboard_button) == {
        "text": "click me",
        "request_contact": True,
        "request_location": True,
    }


def test_force_reply():
    force_reply = ForceReply()
    assert asdict(force_reply) == {"force_reply": True, "selective": False}
    force_reply = ForceReply(True)
    assert asdict(force_reply) == {"force_reply": True, "selective": True}


def test_reply_keyboard_remove():
    reply_keyboard_remove = ReplyKeyboardRemove()
    assert asdict(reply_keyboard_remove) == {
        "remove_keyboard": True,
        "selective": False,
    }

    reply_keyboard_remove = ReplyKeyboardRemove(True)
    assert asdict(reply_keyboard_remove) == {
        "remove_keyboard": True,
        "selective": True,
    }


def test_inline_keyboard_markup():
    inline_keyboard_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("1", callback_data="result1"),
                InlineKeyboardButton("2", callback_data="result2"),
                InlineKeyboardButton("3", callback_data="result3"),
            ]
        ]
    )
    assert asdict(inline_keyboard_markup) == {
        "inline_keyboard": [
            [
                {
                    "text": "1",
                    "url": None,
                    "callback_data": "result1",
                    "switch_inline_query": None,
                    "switch_inline_query_current_chat": None,
                    "callback_game": None,
                    "pay": None,
                },
                {
                    "text": "2",
                    "url": None,
                    "callback_data": "result2",
                    "switch_inline_query": None,
                    "switch_inline_query_current_chat": None,
                    "callback_game": None,
                    "pay": None,
                },
                {
                    "text": "3",
                    "url": None,
                    "callback_data": "result3",
                    "switch_inline_query": None,
                    "switch_inline_query_current_chat": None,
                    "callback_game": None,
                    "pay": None,
                },
            ]
        ]
    }
    assert asdict(inline_keyboard_markup, dict_factory=NoneLessDict) == {
        "inline_keyboard": [
            [
                {"text": "1", "callback_data": "result1"},
                {"text": "2", "callback_data": "result2"},
                {"text": "3", "callback_data": "result3"},
            ]
        ]
    }


def test_reply_keyboard_markup():
    reply_keyboard_markup = ReplyKeyboardMarkup(
        [[KeyboardButton("1"), KeyboardButton("2"), KeyboardButton("3")]]
    )
    assert asdict(reply_keyboard_markup) == {
        "keyboard": [
            [
                {
                    "text": "1",
                    "request_contact": False,
                    "request_location": False,
                },
                {
                    "text": "2",
                    "request_contact": False,
                    "request_location": False,
                },
                {
                    "text": "3",
                    "request_contact": False,
                    "request_location": False,
                },
            ]
        ],
        "resize_keyboard": False,
        "one_time_keyboard": False,
        "selective": False,
    }


def test_markup_json_encoder():
    inline_keyboard_button = InlineKeyboardButton(
        "click me", callback_data="result"
    )
    with pytest.raises(TypeError):
        json.dumps(inline_keyboard_button)

    json.dumps(inline_keyboard_button, cls=MarkupJSONEncoder)

    class VeryCustomClass:
        pass

    with pytest.raises(TypeError):
        json.dumps(VeryCustomClass(), cls=MarkupJSONEncoder)

