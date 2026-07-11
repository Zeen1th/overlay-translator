import os
import queue
import pytesseract
from dotenv import load_dotenv
import keyboard

from .config import Config, ConfigError, load_config
from . import capture, ocr, translate, arabic, overlay, selector

NO_TEXT_MSG = "No text found"
ERROR_MSG = "Translation failed — check your internet connection."


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
    try:
        image = capture.grab(rect)
        english = ocr.extract_text(image)
    except Exception:
        overlay.show(ERROR_MSG, rect, config)
        return
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
    ocr.configure_tesseract(config.tesseract_cmd or None)
    check_tesseract()
    translator = translate.make_translator(config)

    requests: "queue.Queue[None]" = queue.Queue()
    keyboard.add_hotkey(config.hotkey, lambda: requests.put(None))
    print(f"OverlayTranslator ready. Press {config.hotkey} to translate. "
          f"Ctrl+C to quit.")

    while True:
        try:
            # Poll with a timeout so Ctrl+C (KeyboardInterrupt) can break the
            # loop on Windows, where a blocking get() is not interruptible.
            requests.get(timeout=0.5)
        except queue.Empty:
            continue
        # Coalesce any extra presses queued while we were busy, so a burst of
        # Alt+Q presses triggers the pipeline once, not many times.
        while not requests.empty():
            try:
                requests.get_nowait()
            except queue.Empty:
                break
        translate_selection(config, translator)
