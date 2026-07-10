from overlay_translator.models import Rect
import pytest
from overlay_translator.config import Config, ConfigError, load_config


def test_rect_area():
    r = Rect(x=10, y=20, width=100, height=50)
    assert r.area == 5000


def test_rect_zero_area():
    r = Rect(x=0, y=0, width=0, height=30)
    assert r.area == 0


def test_load_config_reads_key_and_defaults():
    cfg = load_config({"DEEPL_API_KEY": "abc123"})
    assert cfg.deepl_api_key == "abc123"
    assert cfg.hotkey == "alt+q"
    assert cfg.font_size == 18


def test_load_config_custom_hotkey():
    cfg = load_config({"DEEPL_API_KEY": "abc123", "HOTKEY": "ctrl+space"})
    assert cfg.hotkey == "ctrl+space"


def test_load_config_missing_key_raises():
    with pytest.raises(ConfigError):
        load_config({})


def test_load_config_empty_key_raises():
    with pytest.raises(ConfigError):
        load_config({"DEEPL_API_KEY": "   "})
