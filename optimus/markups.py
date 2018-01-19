import abc
from typing import List


class ReplyMarkup(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_serializable(self) -> dict:
        raise NotImplementedError


class BaseKeyboardButton(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_serializable(self) -> dict:
        raise NotImplementedError


class InlineKeyboardButton(BaseKeyboardButton):

    def __init__(self, text,
                 url=None, callback_data=None, switch_inline_query=None,
                 switch_inline_query_current_chat=None, callback_game=None,
                 pay=None):
        self.text = text
        self.url = url
        self.callback_data = callback_data
        self.switch_inline_query = switch_inline_query
        self.switch_inline_query_current_chat =\
            switch_inline_query_current_chat
        self.callback_game = callback_game
        self.pay = pay

    def get_serializable(self) -> dict:
        data = {
            'text': self.text
        }
        if self.url is not None:
            data['url'] = self.url
        if self.callback_data is not None:
            data['callback_data'] = self.callback_data
        if self.switch_inline_query is not None:
            data['switch_inline_query'] = self.switch_inline_query
        if self.switch_inline_query_current_chat is not None:
            data['switch_inline_query_current_chat'] =\
                self.switch_inline_query_current_chat
        if self.callback_game is not None:
            data['callback_game'] = self.callback_game.get_serializable()
        if self.pay is not None:
            data['pay'] = self.pay
        return data


class InlineKeyboardMarkup(ReplyMarkup):

    def __init__(self,
                 inline_keyboard: List[List[InlineKeyboardButton]]) -> None:
        self.inline_keyboard = inline_keyboard

    def get_serializable(self) -> dict:
        return {
            'inline_keyboard': [[kb.get_serializable() for kb in kbs]
                                for kbs in self.inline_keyboard]
        }


class KeyboardButton(BaseKeyboardButton):

    def __init__(self, text, request_contact=False, request_location=False):
        self.text = text
        self.request_contact = request_contact
        self.request_location = request_location

    def get_serializable(self) -> dict:
        return {
            'text': self.text,
            'request_contact': self.request_contact,
            'request_location': self.request_location
        }


class ReplyKeyboardMarkup(ReplyMarkup):

    def __init__(self, keyboard: List[List[KeyboardButton]],
                 resize_keyboard=False, one_time_keyboard=False,
                 selective=False) -> None:
        self.keyboard = keyboard
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard
        self.selective = selective

    def get_serializable(self) -> dict:
        return {
            'keyboard': [[kb.get_serializable() for kb in kbs]
                         for kbs in self.keyboard],
            'resize_keyboard': self.resize_keyboard,
            'one_time_keyboard': self.one_time_keyboard,
            'selective': self.selective
        }


class ReplyKeyboardRemove(ReplyMarkup):

    def __init__(self, selective=False) -> None:
        self.remove_keyboard = True
        self.selective = selective

    def get_serializable(self) -> dict:
        return {
            'remove_keyboard': self.remove_keyboard,
            'selective': self.selective
        }


class ForceReply(ReplyMarkup):

    def __init__(self, selective=False) -> None:
        self.force_reply = True
        self.selective = selective

    def get_serializable(self) -> dict:
        return {
            'force_reply': self.force_reply,
            'selective': self.selective
        }
