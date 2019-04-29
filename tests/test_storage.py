import pytest

from baymax.bot import StorageInMemory


pytestmark = pytest.mark.asyncio


async def test_storage_in_memory():
    storage = StorageInMemory()
    key = "new_key"

    value = await storage.get(key)
    assert value is None

    await storage.set(key, 1)
    value = await storage.get(key)
    assert value == 1

    await storage.delete(key)

    value = await storage.get(key, default=3)
    assert value == 3

    await storage.delete("unknown_key")
