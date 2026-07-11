from unittest.mock import patch
from PIL import Image
from overlay_translator import ocr


def _blank_image():
    return Image.new("RGB", (10, 10), "white")


def test_extract_text_strips_whitespace():
    with patch("overlay_translator.ocr.pytesseract.image_to_string",
               return_value="  Hello world \n"):
        assert ocr.extract_text(_blank_image()) == "Hello world"


def test_extract_text_empty_result():
    with patch("overlay_translator.ocr.pytesseract.image_to_string",
               return_value="\n\n"):
        assert ocr.extract_text(_blank_image()) == ""


def test_extract_text_uses_english_lang():
    with patch("overlay_translator.ocr.pytesseract.image_to_string",
               return_value="hi") as m:
        ocr.extract_text(_blank_image())
        assert m.call_args.kwargs.get("lang") == "eng"
