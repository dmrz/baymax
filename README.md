### Baymax, a simple telegram bot framework on top of Python asyncio

Work in progress. Currently trying contextvars, so it's very unsafe to use experimental branch.

### Requirements

- Python 3.9 or higher (might work on 3.8 though, but recent changes tested on 3.9)

### Installation

```bash
pip install baymax
```

### Basic usage example

```python
from baymax.bot import Bot

bot = Bot('token')

@bot.on('/start')
async def start_handler(update):
    await bot.reply('Welcome!')

bot.run()
```

### Middleware example

```python
@bot.middleware
async def message_logging_middleware(raw_update):
    bot.logger.info('New update received: %s', raw_update['update_id'])
```

> NOTE: All middleware functions should be coroutines for now, even if they do not have asynchronous actions.

### FSM example

```python
@bot.fsm('/age', target='wait_for_age_input')
async def age_handler(update):
    await bot.reply('How old are you?')


@bot.fsm_transition(source='wait_for_age_input', conditions=[str.isdigit], terminate=True)
async def age_input_handler(update):
    await bot.reply('Thank you!')
    age = int(update["message"]["text"])
    bot.logger.info('User %d is %d years old', update["message"]["from"]["id"], age)
```

### Reply keyboard markup example

```python
from baymax.markups import KeyboardButton, ReplyKeyboardMarkup

@bot.on('/rate')
async def rate_handler(update):
    await bot.reply('Rate me', reply_markup=ReplyKeyboardMarkup(
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
async def where_handler(update):
    async with aiohttp.ClientSession() as client:
        async with client.get('http://ip-api.com/json') as resp:
            location_data = await resp.json()
    await bot.reply('I am here:')
    await bot.api.send_location(
        update["message"]["chat"]["id"], location_data['lat'], location_data['lon'])
```

### Chat action example

```python
@bot.on('/long')
async def long_handler(update):
    await bot.reply('I will type something for 5 seconds')
    await bot.api.send_chat_action(update["message"]["chat"]["id"], bot.api.ChatAction.TYPING)
    await asyncio.sleep(5)
    await bot.reply('Here it is...')
```

### Send photo example

```python
@bot.on('/photo')
async def photo_handler(update):
    await bot.reply('I will send you my photo now')
    await bot.api.send_chat_action(
        update["message"]["chat"]["id"], bot.api.ChatAction.UPLOAD_PHOTO)
    with open('me.png', 'rb') as photo:
        await bot.api.send_photo(update["message"]["chat"]["id"], photo)
```

### Running tests

```bash
git clone git@github.com:dmrz/baymax.git
pip install -e .
pip install -r requirements-test.txt
pytest
```
