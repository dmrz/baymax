from optimus.args import get_args
from optimus.bot import Bot
from optimus.markups import KeyboardButton, ReplyKeyboardMarkup

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


@bot.middleware
async def message_logging_middleware(update):
    bot.logger.info('New message received: %s', update['message']['text'])


bot.run()
