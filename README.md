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
