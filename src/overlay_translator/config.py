from dataclasses import dataclass
from typing import Mapping


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    deepl_api_key: str
    hotkey: str = "alt+q"
    font_family: str = "Segoe UI"
    font_size: int = 18
    bubble_bg: str = "#1e1e1e"
    bubble_fg: str = "#ffffff"


def load_config(env: Mapping[str, str]) -> Config:
    key = (env.get("DEEPL_API_KEY") or "").strip()
    if not key:
        raise ConfigError(
            "DEEPL_API_KEY is missing. Copy .env.example to .env and add your key."
        )
    hotkey = (env.get("HOTKEY") or "alt+q").strip()
    return Config(deepl_api_key=key, hotkey=hotkey)
