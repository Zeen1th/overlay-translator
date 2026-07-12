import json
from overlay_translator.settings_store import Settings, load_settings, save_settings


def test_defaults_when_file_missing(tmp_path):
    s = load_settings(str(tmp_path / "nope.json"))
    assert s == Settings()
    assert s.hotkey == "alt+q"
    assert s.region_hotkey == "alt+w"
    assert s.auto_toggle_hotkey == "alt+e"
    assert s.auto_hide_seconds == 5
    assert s.engine == "google"
    assert s.use_saved_region is False
    assert s.auto_translate_enabled is False
    assert s.start_with_windows is False
    assert s.ocr_region is None


def test_round_trip(tmp_path):
    p = str(tmp_path / "settings.json")
    save_settings(Settings(
        hotkey="ctrl+space",
        region_hotkey="alt+r",
        auto_toggle_hotkey="ctrl+alt+t",
        auto_hide_seconds=0,
        engine="bing",
        font_size=24,
        theme="light",
        use_saved_region=True,
        auto_translate_enabled=True,
        start_with_windows=True,
        ocr_region={"x": 10, "y": 20, "width": 300, "height": 100},
    ), p)
    s = load_settings(p)
    assert s.hotkey == "ctrl+space"
    assert s.region_hotkey == "alt+r"
    assert s.auto_toggle_hotkey == "ctrl+alt+t"
    assert s.auto_hide_seconds == 0
    assert s.engine == "bing"
    assert s.font_size == 24
    assert s.theme == "light"
    assert s.use_saved_region is True
    assert s.auto_translate_enabled is True
    assert s.start_with_windows is True
    assert s.ocr_region == {"x": 10, "y": 20, "width": 300, "height": 100}


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


def test_invalid_region_disables_saved_region_and_auto(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text(
        json.dumps({
            "use_saved_region": True,
            "auto_translate_enabled": True,
            "ocr_region": {"x": 1, "y": 2, "width": 0, "height": 70},
        }),
        encoding="utf-8",
    )
    s = load_settings(str(p))
    assert s.ocr_region is None
    assert s.use_saved_region is False
    assert s.auto_translate_enabled is False
