from optimus.bot import Bot
from optimus.args import get_args


args = get_args()
bot = Bot(args.token, args.timeout)


@bot.on('hello')
async def hello_handler(update):
    await bot.reply(update, 'hello')


@bot.on('/start')
async def start_handler(update):
    await bot.reply(update, 'Welcome!')


bot.run()
