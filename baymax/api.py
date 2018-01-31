import json

import aiohttp


async def request(url, payload=None, params=None, headers=None):
    headers = {'content-type': 'application/json', **(headers or {})}
    data = payload and json.dumps(payload)
    async with aiohttp.ClientSession() as client:
        async with client.post(
                url, data=data, params=params, headers=headers) as resp:
            # TODO: Check response status
            json_response = await resp.json()
            return json_response


async def get_updates(base_url, timeout, offset):
    params = {
        'timeout': timeout,
        'offset': offset
    }
    return await request(f'{base_url}/getUpdates', params=params)


async def send_message(base_url, chat_id, text, reply_markup=None):
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    if reply_markup is not None:
        payload['reply_markup'] = reply_markup
    return await request(f'{base_url}/sendMessage', payload)


async def answer_callback_query(
        base_url, callback_query_id, text, show_alert,
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
    return await request(f'{base_url}/answerCallbackQuery', payload)
