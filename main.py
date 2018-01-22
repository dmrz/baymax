from optimus.args import get_args
from optimus.bot import Bot
from optimus.markups import (ForceReply, InlineKeyboardButton,
                             InlineKeyboardMarkup, KeyboardButton,
                             ReplyKeyboardMarkup, ReplyKeyboardRemove)

args = get_args()
bot = Bot(args.token, args.timeout)


@bot.on('hello')
async def hello_handler(update):
    await bot.reply(update, 'hello')


@bot.on('/start')
async def start_handler(update):
    await bot.reply(update, 'Welcome!')


@bot.on('/rate')
async def rate_handler(update):
    await bot.reply(update, 'Rate me', reply_markup=ReplyKeyboardMarkup(
        [
            [
                KeyboardButton('⭐️'),
                KeyboardButton('⭐️⭐️'),
                KeyboardButton('⭐️⭐️⭐️')
            ]
        ], resize_keyboard=True, one_time_keyboard=True))


@bot.on('/like')
async def like_handler(update):
    await bot.reply(update, 'How do you like this message?',
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
async def open_handler(update):
    await bot.reply(update, 'Choices', reply_markup=ReplyKeyboardMarkup(
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
async def close_handler(update):
    await bot.reply(update, 'Closing', reply_markup=ReplyKeyboardRemove())


@bot.on('/force')
async def force_handler(update):
    await bot.reply(update, 'Force Reply Test', reply_markup=ForceReply())


@bot.middleware
async def message_logging_middleware(update):
    bot.logger.info('New message received: %s', update.message.text)


bot.run()
