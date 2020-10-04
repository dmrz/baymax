import argparse
import asyncio
import uuid
from collections import defaultdict
from typing import Dict, List, Text

import aiohttp

from baymax.bot import Bot
from baymax.markups import (
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


def get_args():
    parser = argparse.ArgumentParser(description="Baymax arguments.")
    parser.add_argument(
        "-t",
        "--token",
        metavar="token",
        type=str,
        help="Telegram bot token",
        required=True,
    )
    parser.add_argument(
        "-to",
        "--timeout",
        metavar="timeout",
        type=int,
        help="Telegram bot timeout",
        default=30,
    )
    return parser.parse_args()


args = get_args()
bot = Bot(args.token, args.timeout)


@bot.on("hello")
async def hello_handler(update):
    await bot.reply("hello")


@bot.on("hi")
async def hi_handler(update):
    await bot.reply("hi, I will write you back soon")

    async def reply_soon():
        if update["message"]["from"]["id"] == "PUTgIDHERE":
            await asyncio.sleep(10)
        first_name = update["message"]["from"]["first_name"]
        await bot.reply(f"hihi, {first_name}")

    asyncio.create_task(reply_soon())


@bot.on("/start")
async def start_handler(update):
    await bot.reply("Welcome!")


@bot.on("/rate")
async def rate_handler(update):
    await bot.reply(
        "Rate me",
        reply_markup=ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton("⭐️"),
                    KeyboardButton("⭐️⭐️"),
                    KeyboardButton("⭐️⭐️⭐️"),
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


@bot.on("/like")
async def like_handler(update):
    await bot.reply(
        "How do you like this message?",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⭐️", callback_data="1"),
                    InlineKeyboardButton("⭐️⭐️", callback_data="2"),
                    InlineKeyboardButton("⭐️⭐️⭐️", callback_data="3"),
                ]
            ]
        ),
    )


@bot.on("/open")
async def open_handler(update):
    await bot.reply(
        "Choices",
        reply_markup=ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton("1"),
                    KeyboardButton("2"),
                    KeyboardButton("3"),
                ],
                [
                    KeyboardButton("4"),
                    KeyboardButton("5"),
                    KeyboardButton("6"),
                ],
                [
                    KeyboardButton("7"),
                    KeyboardButton("8"),
                    KeyboardButton("9"),
                ],
            ],
            resize_keyboard=True,
        ),
    )


@bot.on("/close")
async def close_handler(update):
    await bot.reply("Closing", reply_markup=ReplyKeyboardRemove())


@bot.on("/force")
async def force_handler(update):
    await bot.reply("Force Reply Test", reply_markup=ForceReply())


@bot.middleware
async def message_logging_middleware(raw_update):
    bot.logger.info("New update received: %s", raw_update["update_id"])


@bot.callback_query
async def callback_query_handler(update):
    bot.logger.info("New callback query received: %s", update["callback_query"])
    await bot.answer_callback_query("Thanks!")


@bot.fsm("/age", target="wait_for_age_input")
async def age_handler(update):
    await bot.reply("How old are you?")


@bot.fsm_transition(
    source="wait_for_age_input", conditions=[str.isdigit], terminate=True
)
async def age_input_handler(update):
    await bot.reply("Thank you!")
    age = int(update["message"]["text"])
    bot.logger.info("User %d is %d years old", update["message"]["from"]["id"], age)


@bot.on("/me")
async def me_handler(update):
    me = await bot.api.get_me()
    first_name = me["result"]["first_name"]
    await bot.reply(f"I am {first_name}!")


@bot.on("/where")
async def where_handler(update):
    async with aiohttp.ClientSession() as client:
        async with client.get("http://ip-api.com/json") as resp:
            location_data = await resp.json()
    await bot.reply("I am here:")
    await bot.api.send_location(
        update["message"]["chat"]["id"],
        location_data["lat"],
        location_data["lon"],
    )


@bot.on("/markdown")
async def markdown_handler(update):
    msg = """
    *Hello World*
    ```python
    def main():
        print('Hello World')
    ```
    """
    await bot.reply_markdown(msg)


@bot.on("/html")
async def html_handler(update):
    msg = """
    <b>Hello World</b>
    <a href="http://google.com">Visit Google!</a>
    """
    await bot.reply_html(msg)


@bot.on("/long")
async def long_handler(update):
    await bot.reply("I will type something for 5 seconds")
    await bot.api.send_chat_action(
        update["message"]["chat"]["id"], bot.api.ChatAction.TYPING
    )
    await asyncio.sleep(5)
    await bot.reply("Here it is...")


@bot.on("/photo")
async def photo_handler(update):
    await bot.reply("I will send you my photo now")
    await bot.api.send_chat_action(
        update["message"]["chat"]["id"], bot.api.ChatAction.UPLOAD_PHOTO
    )
    with open("me.png", "rb") as photo:
        await bot.api.send_photo(update["message"]["chat"]["id"], photo)


QUERY_HISTORY: Dict[int, List[Text]] = defaultdict(list)


@bot.inline_query
async def my_inline_handler(update):
    """
    Very low level example of inline handler query
    """
    inline_query = update["inline_query"]
    bot.logger.info("Got inline query request: %s", inline_query)
    inline_query_id: str = inline_query["id"]
    query: str = inline_query["query"].strip()
    if query:
        user_id = inline_query["from"]["id"]
        QUERY_HISTORY[user_id].append(query)
        results = [
            {
                "type": "article",
                "id": str(uuid.uuid4()),
                "title": f"You queried {q}",
                "input_message_content": {"message_text": f"You selected: {q}"},
            }
            for q in QUERY_HISTORY[user_id]
        ]

    else:
        # Default results
        results = [
            {
                "type": "article",
                "id": str(uuid.uuid4()),
                "title": "I am all ears",
                "input_message_content": {"message_text": "Some very interesting text"},
            }
        ]
    await bot.api.answer_inline_query(
        **{
            "inline_query_id": inline_query_id,
            "results": results,
        }
    )


bot.run()
