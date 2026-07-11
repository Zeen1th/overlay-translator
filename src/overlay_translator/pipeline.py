from datetime import datetime

from . import capture, ocr, arabic, translate

NO_TEXT_MSG = "No text found"
ERROR_MSG = ("Translation failed — the engine may be rate-limited or offline. "
             "Try again, or switch engine in Settings.")


def _now():
    return datetime.now().isoformat(timespec="seconds")


def run_cycle(state, *, select_fn, overlay_fn,
              capture_fn=capture.grab, ocr_fn=ocr.extract_text, now_fn=_now):
    """Run one select -> capture -> OCR -> translate -> overlay -> history cycle.

    All external effects are injected (select_fn, overlay_fn, capture_fn,
    ocr_fn, now_fn) so this is fully unit-testable without a screen or network.
    """
    rect = select_fn()
    if rect is None:
        return
    try:
        image = capture_fn(rect)
        english = ocr_fn(image)
    except Exception:
        overlay_fn(ERROR_MSG, rect, state.settings)
        return
    if not english or not english.strip():
        overlay_fn(NO_TEXT_MSG, rect, state.settings)
        return
    try:
        ar = translate.to_arabic(english, state.engine)
    except translate.TranslationError as exc:
        overlay_fn(str(exc)[:200] or ERROR_MSG, rect, state.settings)
        return
    overlay_fn(arabic.shape_for_display(ar), rect, state.settings)
    with state.lock:
        state.history.add(english, ar, now_fn())
