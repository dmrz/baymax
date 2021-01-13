from typing import Any, Dict

from ..bot import Bot
from ..settings import BotSettings

from .api import TelegramApi
from .client import AIOHttpClient
from .storage import StorageInMemory


DEFAULT_BASE_URL = "https://api.telegram.org/bot"


def default_bot_factory(**settings_override: Dict[str, Any]) -> Bot:
    default_bot_settings = BotSettings.load(**settings_override)
    default_http_client = AIOHttpClient(DEFAULT_BASE_URL, default_bot_settings.token)
    default_api = TelegramApi(http_client=default_http_client)
    default_storage = StorageInMemory()
    return Bot(default_api, default_storage, default_bot_settings)
