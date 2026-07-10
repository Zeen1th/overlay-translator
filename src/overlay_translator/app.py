import os
import pytesseract
from dotenv import load_dotenv
import keyboard

from .config import Config, ConfigError, load_config
from . import capture, ocr, translate, arabic, overlay, selector

NO_TEXT_MSG = "No text found"
ERROR_MSG = "Translation failed — check your connection and DeepL key."


def check_tesseract() -> None:
    """Verify Tesseract is installed and reachable."""
    try:
        pytesseract.get_tesseract_version()
    except Exception as exc:
        raise ConfigError(
            "Tesseract OCR is not installed or not on PATH. Install it from "
            "https://github.com/UB-Mannheim/tesseract/wiki and re-run."
        ) from exc


def translate_selection(config: Config, translator) -> None:
    """Run one full select -> OCR -> translate -> show cycle."""
    rect = selector.select_region()
    if rect is None:
        return
    image = capture.grab(rect)
    english = ocr.extract_text(image)
    if not english:
        overlay.show(NO_TEXT_MSG, rect, config)
        return
    try:
        arabic_text = translate.to_arabic(english, translator)
    except translate.TranslationError:
        overlay.show(ERROR_MSG, rect, config)
        return
    overlay.show(arabic.shape_for_display(arabic_text), rect, config)


def run() -> None:
    load_dotenv()
    config = load_config(os.environ)
    check_tesseract()
    translator = translate.make_translator(config.deepl_api_key)

    keyboard.add_hotkey(
        config.hotkey, lambda: translate_selection(config, translator)
    )
    print(f"OverlayTranslator ready. Press {config.hotkey} to translate. "
          f"Ctrl+C to quit.")
    keyboard.wait()
