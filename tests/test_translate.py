import pytest
from unittest.mock import MagicMock
from overlay_translator.translate import (
    to_arabic, make_engine, TranslationError,
    GoogleEngine, DeeplEngine, BingEngine,
)


def test_empty_returns_empty_without_calling_engine():
    engine = MagicMock()
    assert to_arabic("   ", engine) == ""
    engine.translate.assert_not_called()


def test_returns_translation():
    engine = MagicMock()
    engine.translate.return_value = "مرحبا"
    assert to_arabic("Hello", engine) == "مرحبا"
    engine.translate.assert_called_once_with("Hello")


def test_wraps_errors():
    engine = MagicMock()
    engine.translate.side_effect = RuntimeError("429")
    with pytest.raises(TranslationError):
        to_arabic("Hello", engine)


def test_make_engine_selects_type():
    assert isinstance(make_engine("google"), GoogleEngine)
    assert isinstance(make_engine("deepl"), DeeplEngine)
    assert isinstance(make_engine("bing"), BingEngine)


def test_make_engine_unknown_raises():
    with pytest.raises(TranslationError):
        make_engine("bogus")
