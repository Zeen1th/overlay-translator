import arabic_reshaper
from bidi.algorithm import get_display


def shape_for_display(text: str) -> str:
    """Join Arabic letters and reorder to visual RTL for tkinter display."""
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)
