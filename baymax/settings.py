from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, fields, field, Field
from logging import Logger
from typing import Any, Dict, Tuple

import trafaret as t
from dotenv import load_dotenv

from .logger import get_logger

# NOTE: cli arguments have higher priority than env vars
# NOTE: class parameters have higher priority than env vars and cli args


ENV_VAR_PREFIX = "BAYMAX_BOT_"
ENV_VAR_TYPE_MAP: Dict[str, t.Trafaret] = {
    "int": t.ToInt,
    "float": t.ToFloat,
    "bool": t.ToBool,
    "str": t.String,
}
get_env_var_name = lambda field: f"{ENV_VAR_PREFIX}{field.upper()}"


def get_env_var_settings_trafaret(fields: Tuple[Field]) -> t.Trafaret:
    """
    Returns env vars trafaret for given fields. If field type
    is not in map - t.String will be used as a fallback.
    """
    return t.Dict(
        {
            t.Key(get_env_var_name(field.name), optional=True)
            >> field.name: ENV_VAR_TYPE_MAP.get(field.type, t.String)
            for field in fields
            if field.init
        }
    ).ignore_extra("*")


@dataclass
class Settings:
    """
    General settings class.
    """

    token: str
    base_api_url: str = "https://api.telegram.org/bot"
    timeout: int = 30

    # "static" settings
    logger: Logger = field(default=get_logger("baymax"), init=False)

    @classmethod
    def get_cli_args_parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Baymax arguments.")
        parser.add_argument(
            "-t",
            "--token",
            metavar="token",
            type=str,
            help="Telegram bot token",
            # required=True,
        )
        parser.add_argument(
            "-to",
            "--timeout",
            metavar="timeout",
            type=int,
            help="Telegram bot timeout",
            # default=30,
        )

        return parser

    @classmethod
    def get_from_cli(cls) -> Dict[str, Any]:
        cli_args = Settings.get_cli_args_parser().parse_args()
        return {
            field: field_value
            for field in [f.name for f in fields(cls) if f.init]
            if (field_value := getattr(cli_args, field, None)) is not None
        }

    @classmethod
    def get_from_env(cls) -> Dict[str, str]:
        load_dotenv()
        return get_env_var_settings_trafaret(fields(cls))(os.environ)

    @classmethod
    def load(cls, **kwargs: Any) -> "Settings":
        return cls(**{**cls.get_from_env(), **cls.get_from_cli(), **kwargs})