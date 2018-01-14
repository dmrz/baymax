import asyncio

from optimus.bot import Bot
from optimus.args import get_args


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    args = get_args()
    bot = Bot(args.token, args.timeout)

    @bot.on('hello')
    async def hello_handler(update):
        await bot.reply(update, 'hello')

    poller = loop.create_task(bot.start_polling())
    consumer = loop.create_task(bot.consume())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        bot.logger.info('Shutting down...')
        bot.stop_polling()
        bot.logger.info('Waiting for poller to complete')
        loop.run_until_complete(poller)
        bot.logger.info('Waiting for consumer to complete')
        loop.run_until_complete(consumer)
        loop.close()
