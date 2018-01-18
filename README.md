### Optimus, simple telegram bot on top of Python asyncio

Work in progress


### Basic usage example

```python
from optimus.bot import Bot

bot = Bot('token')

@bot.on('/start')
async def start_handler(update):
    await bot.reply(update, 'Welcome!')

bot.run()
```


### Middleware example

```python
@bot.middleware
async def message_logging_middleware(update):
    bot.logger.info('New message received: %s', update['message']['text'])
```

> NOTE: All middleware functions should be coroutines for now, even if they do not have asynchronous actions.


### Reply keyboard markup example


```python
from optimus.markups import KeyboardButton, ReplyKeyboardMarkup

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
```

> NOTE: Reply markup API / objects will be changing, they are far from good now.