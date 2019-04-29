import pytest
from hypothesis import settings

pytest_plugins = ["aiohttp.pytest_plugin", "pytester"]

settings.register_profile(
    "local", max_examples=3, database=None, deadline=None
)

settings.register_profile("complex", max_examples=1000)

