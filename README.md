### Baymax, a simple telegram bot framework on top of Python asyncio

Work in progress

### Requirements

- Python 3.7 or higher

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

### FSM example

```python
@bot.fsm('/age', target='wait_for_age_input')
async def age_handler(message):
    await bot.reply(message, 'How old are you?')


@bot.fsm_transition(source='wait_for_age_input', conditions=[str.isdigit], terminate=True)
async def age_input_handler(message):
    await bot.reply(message, 'Thank you!')
    age = int(message.text)
    bot.logger.info('User %d is %d years old', message.from_.id, age)
```

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

### Chat action example

```python
@bot.on('/long')
async def long_handler(message):
    await bot.reply(message, 'I will type something for 5 seconds')
    await bot.api.send_chat_action(message.chat.id, bot.api.ChatAction.TYPING)
    await asyncio.sleep(5)
    await bot.reply(message, 'Here it is...')
```

### Send photo example

```python
@bot.on('/photo')
async def photo_handler(message):
    await bot.reply(message, 'I will send you my photo now')
    await bot.api.send_chat_action(
        message.chat.id, bot.api.ChatAction.UPLOAD_PHOTO)
    with open('me.png', 'rb') as photo:
        await bot.api.send_photo(message.chat.id, photo)
```

### Running tests

```bash
git clone git@github.com:dmrz/baymax.git
pip install -e .
pip install -r requirements-test.txt
pytest
```
