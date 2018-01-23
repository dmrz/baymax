from optimus.args import get_args
from optimus.bot import Bot
from optimus.markups import (ForceReply, InlineKeyboardButton,
                             InlineKeyboardMarkup, KeyboardButton,
                             ReplyKeyboardMarkup, ReplyKeyboardRemove)

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
async def message_logging_middleware(update):
    bot.logger.info('New update received: %s', update.update_id)


@bot.callback_query
async def callback_query_handler(callback_query):
    bot.logger.info('New callback query received: %s', callback_query)
    await bot.answer_callback_query(callback_query, 'Thanks!')


bot.run()
