import abc
from typing import List


class ReplyMarkup(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_serializable(self) -> dict:
        raise NotImplementedError


class KeyboardButton:

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
