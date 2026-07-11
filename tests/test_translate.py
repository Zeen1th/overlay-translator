import pytest
from unittest.mock import MagicMock
from overlay_translator.translate import to_arabic, TranslationError


def test_to_arabic_empty_returns_empty_without_api_call():
    translator = MagicMock()
    assert to_arabic("   ", translator) == ""
    translator.translate_text.assert_not_called()


def test_to_arabic_returns_translated_text():
    translator = MagicMock()
    translator.translate_text.return_value = MagicMock(text="مرحبا")
    assert to_arabic("Hello", translator) == "مرحبا"
    translator.translate_text.assert_called_once_with(
        "Hello", source_lang="EN", target_lang="AR"
    )


def test_to_arabic_wraps_errors():
    translator = MagicMock()
    translator.translate_text.side_effect = RuntimeError("network down")
    with pytest.raises(TranslationError):
        to_arabic("Hello", translator)
