import json
from overlay_translator.settings_store import Settings, load_settings, save_settings


def test_defaults_when_file_missing(tmp_path):
    s = load_settings(str(tmp_path / "nope.json"))
    assert s == Settings()
    assert s.hotkey == "alt+q"
    assert s.auto_hide_seconds == 5
    assert s.engine == "google"


def test_round_trip(tmp_path):
    p = str(tmp_path / "settings.json")
    save_settings(Settings(hotkey="ctrl+space", auto_hide_seconds=0, engine="bing",
                           font_size=24, theme="light"), p)
    s = load_settings(p)
    assert s.hotkey == "ctrl+space"
    assert s.auto_hide_seconds == 0
    assert s.engine == "bing"
    assert s.font_size == 24
    assert s.theme == "light"


def test_partial_file_fills_missing_from_defaults(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({"engine": "deepl"}), encoding="utf-8")
    s = load_settings(str(p))
    assert s.engine == "deepl"       # from file
    assert s.hotkey == "alt+q"       # default
    assert s.font_size == 18         # default


def test_corrupt_file_returns_defaults(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text("{ not json", encoding="utf-8")
    s = load_settings(str(p))
    assert s == Settings()
