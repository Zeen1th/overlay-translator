import json
from dataclasses import asdict, dataclass, fields


@dataclass
class Settings:
    hotkey: str = "alt+q"
    region_hotkey: str = "alt+w"
    auto_toggle_hotkey: str = "alt+e"
    auto_hide_seconds: int = 5
    engine: str = "google"
    font_size: int = 18
    theme: str = "dark"
    use_saved_region: bool = False
    auto_translate_enabled: bool = False
    start_with_windows: bool = False
    ocr_region: dict | None = None


def _normalize_region(value) -> dict | None:
    if not isinstance(value, dict):
        return None
    try:
        x = int(value["x"])
        y = int(value["y"])
        width = int(value["width"])
        height = int(value["height"])
    except (KeyError, TypeError, ValueError):
        return None
    if width <= 0 or height <= 0:
        return None
    return {"x": x, "y": y, "width": width, "height": height}


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
    settings = Settings(**{**asdict(Settings()), **kwargs})
    settings.use_saved_region = bool(settings.use_saved_region)
    settings.auto_translate_enabled = bool(settings.auto_translate_enabled)
    settings.start_with_windows = bool(settings.start_with_windows)
    settings.ocr_region = _normalize_region(settings.ocr_region)
    if settings.ocr_region is None:
        settings.use_saved_region = False
        settings.auto_translate_enabled = False
    return settings


def save_settings(settings: Settings, path: str) -> None:
    """Write settings as pretty JSON."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(asdict(settings), fh, indent=2, ensure_ascii=False)
