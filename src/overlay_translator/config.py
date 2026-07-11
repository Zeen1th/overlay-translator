from dataclasses import dataclass
from typing import Mapping

VALID_ENGINES = ("google", "deepl_api")


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    translation_engine: str = "google"
    deepl_api_key: str = ""
    tesseract_cmd: str = ""
    hotkey: str = "alt+q"
    font_family: str = "Segoe UI"
    font_size: int = 18
    bubble_bg: str = "#1e1e1e"
    bubble_fg: str = "#ffffff"


def load_config(env: Mapping[str, str]) -> Config:
    """Build a Config from an environment mapping.

    Translation defaults to the keyless "google" engine, so no API key is
    required. A key is only needed when TRANSLATION_ENGINE is "deepl_api".
    """
    engine = (env.get("TRANSLATION_ENGINE") or "google").strip().lower()
    if engine not in VALID_ENGINES:
        raise ConfigError(
            f"TRANSLATION_ENGINE must be one of {VALID_ENGINES}, got {engine!r}."
        )

    key = (env.get("DEEPL_API_KEY") or "").strip()
    if engine == "deepl_api" and not key:
        raise ConfigError(
            "TRANSLATION_ENGINE=deepl_api needs a DEEPL_API_KEY. Add your key "
            "to .env, or switch to the keyless TRANSLATION_ENGINE=google."
        )

    hotkey = (env.get("HOTKEY") or "").strip() or "alt+q"
    tesseract_cmd = (env.get("TESSERACT_CMD") or "").strip()
    return Config(
        translation_engine=engine,
        deepl_api_key=key,
        hotkey=hotkey,
        tesseract_cmd=tesseract_cmd,
    )
