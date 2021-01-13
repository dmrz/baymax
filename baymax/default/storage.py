from collections import UserDict
from typing import Any, Optional

from ..base import BaseStorage


class StorageInMemory(BaseStorage, UserDict):
    async def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        return self.data.get(key, default)

    async def delete(self, key: str) -> None:
        if key in self.data:
            del self.data[key]
