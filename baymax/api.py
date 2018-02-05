import json

import aiohttp


class TelegramApi:
    base_url: str

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    async def request(self, url, payload=None, params=None, headers=None):
        headers = {'content-type': 'application/json', **(headers or {})}
        data = payload and json.dumps(payload)
        async with aiohttp.ClientSession() as client:
            async with client.post(
                    url, data=data, params=params, headers=headers) as resp:
                # TODO: Check response status
                json_response = await resp.json()
                return json_response

    async def get_updates(self, timeout, offset):
        params = {
            'timeout': timeout,
            'offset': offset
        }
        return await self.request(f'{self.base_url}/getUpdates', params=params)

    async def get_me(self):
        return await self.request(f'{self.base_url}/getMe')

    async def send_message(
            self, chat_id, text,
            parse_mode=None, disable_web_page_preview=None,
            disable_notification=None, reply_to_message_id=None,
            reply_markup=None):
        payload = {
            'chat_id': chat_id,
            'text': text
        }
        if parse_mode is not None:
            payload['parse_mode'] = parse_mode
        if disable_web_page_preview is not None:
            payload['disable_web_page_preview'] = disable_web_page_preview
        if disable_notification is not None:
            payload['disable_notification'] = disable_notification
        if reply_to_message_id is not None:
            payload['reply_to_message_id'] = reply_to_message_id
        if reply_markup is not None:
            payload['reply_markup'] = reply_markup
        return await self.request(f'{self.base_url}/sendMessage', payload)

    async def forward_message(
            self, chat_id, from_chat_id,
            message_id, disable_notification=None):
        payload = {
            'chat_id': chat_id,
            'from_chat_id': from_chat_id,
            'message_id': message_id
        }
        if disable_notification is not None:
            payload['disable_notification'] = disable_notification
        return await self.request(f'{self.base_url}/forwardMessage', payload)

    async def send_location(
            self, chat_id, latitude, longitude,
            live_period=None, disable_notification=None,
            reply_to_message_id=None, reply_markup=None):
        payload = {
            'chat_id': chat_id,
            'latitude': latitude,
            'longitude': longitude
        }
        if live_period is not None:
            payload['live_period'] = live_period
        if disable_notification is not None:
            payload['disable_notification'] = disable_notification
        if reply_to_message_id is not None:
            payload['reply_to_message_id'] = reply_to_message_id
        if reply_markup is not None:
            payload['reply_markup'] = reply_markup
        return await self.request(f'{self.base_url}/sendLocation', payload)

    async def answer_callback_query(
            self, callback_query_id, text, show_alert,
            url=None, cache_time=None):
        payload = {
            'callback_query_id': callback_query_id,
            'text': text,
            'show_alert': show_alert
        }
        if url is not None:
            payload['url'] = url
        if cache_time is not None:
            payload['cache_time'] = cache_time
        return await self.request(
            f'{self.base_url}/answerCallbackQuery', payload)
