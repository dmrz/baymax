from dataclasses import fields, is_dataclass
from typing import Any, Dict, Tuple, Type, get_type_hints

from ..bot import Bot
from ..settings import Settings

from ..base import BaseTelegramApi, BaseStorage
from .api import TelegramApi
from .storage import StorageInMemory


IoCContainer = Dict[Tuple[str, Type[Any]], Any]


def default_bot_factory(**settings_override: Dict[str, Any]) -> Bot:
    container: IoCContainer = {}
    container[("settings", Settings)] = Settings.load(**settings_override)
    container[("api", BaseTelegramApi)] = injected(TelegramApi, container)
    container[("storage", BaseStorage)] = injected(StorageInMemory, container)
    return injected(Bot, container)


def injected(datacls: Type[Any], container: IoCContainer, **kwargs: Any) -> Any:
    """
    This is a very basic DI implementation.

    Takes data class, processes it's fields, tries to resolve
    dependencies from given container and returns instance of
    that class with dependencies injected.
    """
    if not is_dataclass(datacls):
        return datacls(**kwargs)
    fields_tuple = fields(datacls)
    type_hints = get_type_hints(datacls)
    # Collecting a map field name -> field type, we use
    # type hints here since dataclasses.fields sometimes
    # returns types as strings instead of actual types/classes,
    # we need to find out the reason of that.
    field_type_map = {
        field.name: type_hints[field.name]
        if isinstance(field.type, str)
        else field.type
        for field in fields_tuple
        if field.init
    }
    # Trying to resolve dependencies from container
    dependencies = {
        field_name: field_dependency
        for field_name, field_type in field_type_map.items()
        if (field_dependency := container.get((field_name, field_type), None))
        is not None
    }

    return datacls(**dependencies, **kwargs)
