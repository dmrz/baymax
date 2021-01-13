from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Union


# This module is dedicated for abstractions only


@dataclass
class BaseHttpClient(metaclass=abc.ABCMeta):
    """
    Abstract base class for http client that
    is used for interacting with Telegram API.
    """

    base_url: str
    token: str

    def get_api_url(self, endpoint: str) -> str:
        return f"{self.base_url}{self.token}/{endpoint}"

    @abc.abstractproperty
    def form_data_type(self) -> Any:
        """
        Should return form data type that can
        be used for instatiating.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def request(
        self,
        endpoint: str,
        params: Optional[Mapping[str, str]] = None,
        data: Any = None,
        json: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        **kwargs: Any,
    ) -> Union[Dict[str, str], List[Any], str, int, float, bool]:
        """
        Should return response as some structured data.
        TODO: Figure out a "protocol" for error handling.
        Probably use something like Maybe type.
        """
        raise NotImplementedError


@dataclass
class BaseTelegramApi(metaclass=abc.ABCMeta):
    """
    Abstract telegram api.
    """

    http_client: BaseHttpClient


class BaseStorage(metaclass=abc.ABCMeta):
    """
    Abstract class for storage that is primarily used for FSM.
    """
    @abc.abstractmethod
    async def set(self, key: str, value: Any) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, key: str) -> None:
        raise NotImplementedError