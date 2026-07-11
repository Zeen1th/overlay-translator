import json
from dataclasses import asdict, dataclass, fields


@dataclass
class Settings:
    hotkey: str = "alt+q"
    auto_hide_seconds: int = 5
    engine: str = "google"
    deepl_api_key: str = ""
    font_size: int = 18
    theme: str = "dark"


def load_settings(path: str) -> Settings:
    """Load settings; missing/partial/corrupt files degrade to defaults."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("settings root is not an object")
    except (OSError, ValueError):
        return Settings()
    known = {f.name for f in fields(Settings)}
    kwargs = {k: v for k, v in data.items() if k in known}
    return Settings(**{**asdict(Settings()), **kwargs})


def save_settings(settings: Settings, path: str) -> None:
    """Write settings as pretty JSON."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(asdict(settings), fh, indent=2, ensure_ascii=False)
