import argparse
import asyncio

import aiohttp

from baymax.bot import Bot
from baymax.markups import (ForceReply, InlineKeyboardButton,
                            InlineKeyboardMarkup, KeyboardButton,
                            ReplyKeyboardMarkup, ReplyKeyboardRemove)


def get_args():
    parser = argparse.ArgumentParser(description='Baymax arguments.')
    parser.add_argument('-t', '--token', metavar='token', type=str,
                        help='Telegram bot token', required=True)
    parser.add_argument('-to', '--timeout', metavar='timeout', type=int,
                        help='Telegram bot timeout', default=30)
    return parser.parse_args()


args = get_args()
bot = Bot(args.token, args.timeout)


@bot.on('hello')
async def hello_handler(message):
    await bot.reply(message, 'hello')


@bot.on('/start')
async def start_handler(message):
    await bot.reply(message, 'Welcome!')


@bot.on('/rate')
async def rate_handler(message):
    await bot.reply(message, 'Rate me', reply_markup=ReplyKeyboardMarkup(
        [
            [
                KeyboardButton('⭐️'),
                KeyboardButton('⭐️⭐️'),
                KeyboardButton('⭐️⭐️⭐️')
            ]
        ], resize_keyboard=True, one_time_keyboard=True))


@bot.on('/like')
async def like_handler(message):
    await bot.reply(message, 'How do you like this message?',
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    '⭐️', callback_data='1'),
                                InlineKeyboardButton(
                                    '⭐️⭐️', callback_data='2'),
                                InlineKeyboardButton(
                                    '⭐️⭐️⭐️', callback_data='3')
                            ]
                        ]))


@bot.on('/open')
async def open_handler(message):
    await bot.reply(message, 'Choices', reply_markup=ReplyKeyboardMarkup(
        [
            [
                KeyboardButton('1'),
                KeyboardButton('2'),
                KeyboardButton('3'),
            ],
            [
                KeyboardButton('4'),
                KeyboardButton('5'),
                KeyboardButton('6')
            ],
            [
                KeyboardButton('7'),
                KeyboardButton('8'),
                KeyboardButton('9')
            ],
        ], resize_keyboard=True))


@bot.on('/close')
async def close_handler(message):
    await bot.reply(message, 'Closing', reply_markup=ReplyKeyboardRemove())


@bot.on('/force')
async def force_handler(message):
    await bot.reply(message, 'Force Reply Test', reply_markup=ForceReply())


@bot.middleware
async def message_logging_middleware(raw_update):
    bot.logger.info('New update received: %s', raw_update['update_id'])


@bot.callback_query
async def callback_query_handler(callback_query):
    bot.logger.info('New callback query received: %s', callback_query)
    await bot.answer_callback_query(callback_query, 'Thanks!')


@bot.fsm('/age', target='wait_for_age_input')
async def age_handler(message):
    await bot.reply(message, 'How old are you?')


@bot.fsm_transition(
    source='wait_for_age_input', conditions=[str.isdigit], terminate=True)
async def age_input_handler(message):
    await bot.reply(message, 'Thank you!')
    age = int(message.text)
    bot.logger.info('User %d is %d years old', message.from_.id, age)


@bot.on('/me')
async def me_handler(message):
    me = await bot.api.get_me()
    first_name = me['result']['first_name']
    await bot.reply(message, f'I am {first_name}!')


@bot.on('/where')
async def where_handler(message):
    async with aiohttp.ClientSession() as client:
        async with client.get('http://ip-api.com/json') as resp:
            location_data = await resp.json()
    await bot.reply(message, 'I am here:')
    await bot.api.send_location(
        message.chat.id, location_data['lat'], location_data['lon'])


@bot.on('/markdown')
async def markdown_handler(message):
    msg = '''
    *Hello World*
    ```python
    def main():
        print('Hello World')
    ```
    '''
    await bot.reply_markdown(message, msg)


@bot.on('/html')
async def html_handler(message):
    msg = '''
    <b>Hello World</b>
    <a href="http://google.com">Visit Google!</a>
    '''
    await bot.reply_html(message, msg)


@bot.on('/long')
async def long_handler(message):
    await bot.reply(message, 'I will type something for 5 seconds')
    await bot.api.send_chat_action(message.chat.id, bot.api.ChatAction.TYPING)
    await asyncio.sleep(5)
    await bot.reply(message, 'Here it is...')


@bot.on('/photo')
async def photo_handler(message):
    await bot.reply(message, 'I will send you my photo now')
    await bot.api.send_chat_action(
        message.chat.id, bot.api.ChatAction.UPLOAD_PHOTO)
    with open('me.png', 'rb') as photo:
        await bot.api.send_photo(message.chat.id, photo)


bot.run()
