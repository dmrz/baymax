### Baymax, a simple telegram bot framework on top of Python asyncio

Work in progress

### Requirements

* Python 3.6 or higher

### Installation

```bash
pip install baymax
```


### Basic usage example

```python
from baymax.bot import Bot

bot = Bot('token')

@bot.on('/start')
async def start_handler(message):
    await bot.reply(message, 'Welcome!')

bot.run()
```


### Middleware example

```python
@bot.middleware
async def message_logging_middleware(raw_update):
    bot.logger.info('New update received: %s', raw_update['update_id'])
```

> NOTE: All middleware functions should be coroutines for now, even if they do not have asynchronous actions.


### Reply keyboard markup example


```python
from baymax.markups import KeyboardButton, ReplyKeyboardMarkup

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
```

> NOTE: Reply markup API / objects will be changing, they are far from good now.


### Using Telegram bot API methods

Here is an example of using `sendLocation` method:

```python
@bot.on('/where')
async def where_handler(message):
    async with aiohttp.ClientSession() as client:
        async with client.get('http://ip-api.com/json') as resp:
            location_data = await resp.json()
    await bot.reply(message, 'I am here:')
    await bot.api.send_location(
        message.chat.id, location_data['lat'], location_data['lon'])
```
