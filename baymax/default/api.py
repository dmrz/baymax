from collections import UserDict
from dataclasses import asdict
from enum import Enum
from functools import partial
from io import BufferedReader
from json import dumps as json_dumps, JSONEncoder
from typing import Any, Awaitable, Dict, List, Mapping, Optional, Union, BinaryIO

import aiohttp
from trafaret import guard

from ..base import BaseTelegramApi
from ..trafarets import AnswerInlineQuery
from ..typedefs.common import ParseMode
from ..typedefs.markups import Markup


class TelegramApi(BaseTelegramApi):
    """
    Simple Telegram API implementation, using aiohttp client for http requests.
    """

    class ChatAction(Enum):
        TYPING: str = "typing"
        UPLOAD_PHOTO: str = "upload_photo"
        RECORD_VIDEO: str = "record_video"
        UPLOAD_VIDEO: str = "upload_video"
        RECORD_AUDIO: str = "record_audio"
        UPLOAD_AUDIO: str = "upload_audio"
        UPLOAD_DOCUMENT: str = "upload_document"
        FIND_LOCATION: str = "find_location"
        RECEIVE_VIDEO_NOTE: str = "record_video_note"
        UPLOAD_VIDEO_NOTE: str = "upload_video_note"

    form_data_type = aiohttp.formdata.FormData

    async def request(
        self,
        endpoint: str,
        params: Optional[Mapping[str, str]] = None,
        data: Any = None,
        json: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        **kwargs: Any
    ) -> Union[Dict[str, str], List[Any], str, int, float, bool]:
        async with aiohttp.ClientSession(
            json_serialize=partial(json_dumps, cls=MarkupJSONEncoder)
        ) as client:

            async with client.post(
                self.get_api_url(endpoint),
                params=params,
                data=data,
                json=json,
                headers=headers,
                **kwargs
            ) as response:
                # TODO: Handle errors
                return await response.json()

    async def get_updates(self, timeout, offset):
        params = {"timeout": timeout, "offset": offset}
        return await self.request("getUpdates", params=params)

    async def get_me(self):
        return await self.request("getMe")

    async def send_message(
        self,
        chat_id,
        text,
        parse_mode: Optional[ParseMode] = None,
        disable_web_page_preview=None,
        disable_notification=None,
        reply_to_message_id=None,
        reply_markup=None,
    ):
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode is not None:
            payload["parse_mode"] = parse_mode
        if disable_web_page_preview is not None:
            payload["disable_web_page_preview"] = disable_web_page_preview
        if disable_notification is not None:
            payload["disable_notification"] = disable_notification
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return await self.request("sendMessage", json=payload)

    async def send_photo(
        self,
        chat_id,
        photo: Union[BinaryIO, str],
        caption=None,
        parse_mode=None,
        disable_notification=None,
        reply_to_message_id=None,
        reply_markup=None,
    ):
        payload = {"chat_id": chat_id, "photo": photo}
        if caption is not None:
            payload["caption"] = caption
        if parse_mode is not None:
            payload["parse_mode"] = parse_mode
        if disable_notification is not None:
            payload["disable_notification"] = disable_notification
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        if isinstance(photo, BufferedReader):
            data = self.form_data_type()
            for k, v in payload.items():
                if k == "photo":
                    data.add_field(k, v, filename=photo.name)
                else:
                    data.add_field(k, str(v))
            return await self.request("sendPhoto", data=data)
        return await self.request("sendPhoto", json=payload)

    async def forward_message(
        self, chat_id, from_chat_id, message_id, disable_notification=None
    ):
        payload = {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
        }
        if disable_notification is not None:
            payload["disable_notification"] = disable_notification
        return await self.request("forwardMessage", json=payload)

    async def send_location(
        self,
        chat_id,
        latitude,
        longitude,
        live_period=None,
        disable_notification=None,
        reply_to_message_id=None,
        reply_markup=None,
    ):
        payload = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
        }
        if live_period is not None:
            payload["live_period"] = live_period
        if disable_notification is not None:
            payload["disable_notification"] = disable_notification
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return await self.request("sendLocation", json=payload)

    async def send_chat_action(self, chat_id: Union[int, str], action: ChatAction):
        payload = {"chat_id": chat_id, "action": action.value}
        return await self.request("sendChatAction", json=payload)

    async def kick_chat_member(self, chat_id, user_id: int, until_date=None):
        payload = {"chat_id": chat_id, "user_id": user_id}
        if until_date is not None:
            payload["until_date"] = until_date
        return await self.request("kickChatMember", json=payload)

    async def unban_chat_member(self, chat_id, user_id: int):
        payload = {"chat_id": chat_id, "user_id": user_id}
        return await self.request("unbanChatMember", json=payload)

    async def restrict_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        until_date: Optional[int] = None,
        can_send_messages: Optional[bool] = None,
        can_send_media_messages: Optional[bool] = None,
        can_send_other_messages: Optional[bool] = None,
        can_add_web_page_previews: Optional[bool] = None,
    ) -> Awaitable[Dict[str, Any]]:
        payload = {"chat_id": chat_id, "user_id": user_id}
        if until_date is not None:
            payload["until_date"] = until_date
        if can_send_messages is not None:
            payload["can_send_messages"] = can_send_messages
        if can_send_media_messages is not None:
            payload["can_send_media_messages"] = can_send_media_messages
        if can_send_other_messages is not None:
            payload["can_send_other_messages"] = can_send_other_messages
        if can_add_web_page_previews is not None:
            payload["can_add_web_page_previews"] = can_add_web_page_previews
        return await self.request("restrictChatMember", json=payload)

    async def promote_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        can_change_info: Optional[int] = None,
        can_post_messages: Optional[bool] = None,
        can_edit_messages: Optional[bool] = None,
        can_delete_messages: Optional[bool] = None,
        can_invite_users: Optional[bool] = None,
        can_restrict_members: Optional[bool] = None,
        can_pin_messages: Optional[bool] = None,
        can_promote_members: Optional[bool] = None,
    ) -> Awaitable[Dict[str, Any]]:
        payload = {"chat_id": chat_id, "user_id": user_id}
        if can_change_info is not None:
            payload["can_change_info"] = can_change_info
        if can_post_messages is not None:
            payload["can_post_messages"] = can_post_messages
        if can_edit_messages is not None:
            payload["can_edit_messages"] = can_edit_messages
        if can_delete_messages is not None:
            payload["can_delete_messages"] = can_delete_messages
        if can_invite_users is not None:
            payload["can_invite_users"] = can_invite_users
        if can_restrict_members is not None:
            payload["can_restrict_members"] = can_restrict_members
        if can_pin_messages is not None:
            payload["can_pin_messages"] = can_pin_messages
        if can_promote_members is not None:
            payload["can_promote_members"] = can_promote_members
        return await self.request("promoteChatMember", json=payload)

    async def export_chat_invite_link(
        self, chat_id: Union[int, str]
    ) -> Awaitable[Dict[str, Any]]:
        payload = {"chat_id": chat_id}
        return await self.request("exportChatInviteLink", json=payload)

    async def set_chat_photo(
        self, chat_id: Union[int, str], photo: Union[BinaryIO, str]
    ) -> Awaitable[Dict[str, Any]]:
        payload = {"chat_id": chat_id, "photo": photo}
        if isinstance(photo, BufferedReader):
            data = self.form_data_type()
            for k, v in payload.items():
                if k == "photo":
                    data.add_field(k, v, filename=photo.name)
                else:
                    data.add_field(k, str(v))
            payload = data
            return await self.request("setChatPhoto", data=payload)
        return await self.request("setChatPhoto", json=payload)

    async def delete_chat_photo(
        self, chat_id: Union[int, str]
    ) -> Awaitable[Dict[str, Any]]:
        payload = {"chat_id": chat_id}
        return await self.request("deleteChatPhoto", json=payload)

    async def set_chat_title(self, chat_id, title):
        payload = {"chat_id": chat_id, "title": title}
        return await self.request("setChatTitle", json=payload)

    async def set_chat_description(self, chat_id, description):
        payload = {"chat_id": chat_id, "description": description}
        return await self.request("setChatDescription", json=payload)

    async def leave_chat(self, chat_id):
        payload = {"chat_id": chat_id}
        return await self.request("leaveChat", json=payload)

    async def get_chat(self, chat_id):
        payload = {"chat_id": chat_id}
        return await self.request("getChat", json=payload)

    async def get_chat_administrators(self, chat_id):
        payload = {"chat_id": chat_id}
        return await self.request("getChatAdministrators", json=payload)

    async def get_chat_members_count(self, chat_id):
        payload = {"chat_id": chat_id}
        return await self.request("getChatMembersCount", json=payload)

    async def get_chat_member(self, chat_id, user_id):
        payload = {"chat_id": chat_id, "user_id": user_id}
        return await self.request("getChatMember", json=payload)

    async def answer_callback_query(
        self, callback_query_id, text, show_alert, url=None, cache_time=None
    ):
        payload = {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert,
        }
        if url is not None:
            payload["url"] = url
        if cache_time is not None:
            payload["cache_time"] = cache_time
        return await self.request("answerCallbackQuery", json=payload)

    @guard(AnswerInlineQuery)
    async def answer_inline_query(self, **payload):
        return await self.request("answerInlineQuery", json=payload)


class NoneLessDict(UserDict):
    """
    Dictionary that cannot have None as a value.
    """

    def __setitem__(self, key, value) -> None:
        if value is not None:
            super().__setitem__(key, value)


class MarkupJSONEncoder(JSONEncoder):
    def default(self, o) -> Dict:
        if isinstance(o, Markup):
            return asdict(o, dict_factory=NoneLessDict)
        if isinstance(o, UserDict):
            return o.data
        return super().default(o)