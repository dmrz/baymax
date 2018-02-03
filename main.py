import argparse

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
    # FIXME: Does not work for now
    await bot.answer_callback_query(callback_query, 'Thanks!')


AGE_STATE = 'age_state'


@bot.on('/age')
async def age_handler(message):
    await bot.set_state(message.from_, AGE_STATE)
    await bot.reply(message, 'How old are you?')


@bot.on_state(AGE_STATE, predicate=str.isdigit)
async def age_answer_handler(message):
    try:
        age = int(message.text)
    except ValueError:
        # We will never get here with predicate
        await bot.reply(message, 'Write a number')
    else:
        await bot.delete_state(message.from_)
        await bot.reply(message, 'Thank you!')
        bot.logger.info('User %d is %d years old', message.from_.id, age)


@bot.on('/me')
async def me_handler(message):
    me = await bot.api.get_me()
    first_name = me['result']['first_name']
    await bot.reply(message, f'I am {first_name}!')


bot.run()
