import abc
from collections import UserDict
from typing import Any, Optional


class BaseStorage(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def set(self, key: str, value: Any) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, key: str) -> None:
        raise NotImplementedError


class StorageInMemory(BaseStorage, UserDict):
    async def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        return self.data.get(key, default)

    async def delete(self, key: str) -> None:
        if key in self.data:
            del self.data[key]
