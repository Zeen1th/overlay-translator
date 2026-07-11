import pytest
from unittest.mock import MagicMock
from overlay_translator.translate import (
    to_arabic,
    make_translator,
    GoogleEngine,
    DeepLApiEngine,
    TranslationError,
)
from overlay_translator.config import Config


def test_to_arabic_empty_returns_empty_without_calling_engine():
    translator = MagicMock()
    assert to_arabic("   ", translator) == ""
    translator.translate.assert_not_called()


def test_to_arabic_returns_translated_text():
    translator = MagicMock()
    translator.translate.return_value = "مرحبا"
    assert to_arabic("Hello", translator) == "مرحبا"
    translator.translate.assert_called_once_with("Hello")


def test_to_arabic_wraps_errors():
    translator = MagicMock()
    translator.translate.side_effect = RuntimeError("network down")
    with pytest.raises(TranslationError):
        to_arabic("Hello", translator)


def test_make_translator_google_is_default():
    engine = make_translator(Config())
    assert isinstance(engine, GoogleEngine)


def test_make_translator_deepl_api_when_selected():
    cfg = Config(translation_engine="deepl_api", deepl_api_key="abc123")
    engine = make_translator(cfg)
    assert isinstance(engine, DeepLApiEngine)


def test_make_translator_unknown_engine_raises():
    # Config validation normally prevents this, but the factory guards too.
    cfg = Config(translation_engine="bogus")
    with pytest.raises(TranslationError):
        make_translator(cfg)
