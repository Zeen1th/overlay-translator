from overlay_translator.models import Rect
import pytest
from overlay_translator.config import Config, ConfigError, load_config


def test_rect_area():
    r = Rect(x=10, y=20, width=100, height=50)
    assert r.area == 5000


def test_rect_zero_area():
    r = Rect(x=0, y=0, width=0, height=30)
    assert r.area == 0


def test_load_config_defaults_to_keyless_google():
    cfg = load_config({})
    assert cfg.translation_engine == "google"
    assert cfg.deepl_api_key == ""
    assert cfg.hotkey == "alt+q"
    assert cfg.font_size == 18


def test_load_config_custom_hotkey():
    cfg = load_config({"HOTKEY": "ctrl+space"})
    assert cfg.hotkey == "ctrl+space"


def test_load_config_google_needs_no_key():
    cfg = load_config({"TRANSLATION_ENGINE": "google"})
    assert cfg.translation_engine == "google"


def test_load_config_deepl_api_requires_key():
    with pytest.raises(ConfigError):
        load_config({"TRANSLATION_ENGINE": "deepl_api"})


def test_load_config_deepl_api_reads_key():
    cfg = load_config(
        {"TRANSLATION_ENGINE": "deepl_api", "DEEPL_API_KEY": "abc123"}
    )
    assert cfg.translation_engine == "deepl_api"
    assert cfg.deepl_api_key == "abc123"


def test_load_config_engine_is_case_insensitive():
    cfg = load_config({"TRANSLATION_ENGINE": "Google"})
    assert cfg.translation_engine == "google"


def test_load_config_invalid_engine_raises():
    with pytest.raises(ConfigError):
        load_config({"TRANSLATION_ENGINE": "bogus"})
