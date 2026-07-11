def shape_for_display(text: str) -> str:
    """Return Arabic text unchanged for display in tkinter.

    On Windows, tkinter (Tk 8.6.12) already renders Arabic correctly — it joins
    letters and applies right-to-left bidi ordering via the OS text stack,
    including for mixed content (Arabic + Latin + punctuation).

    Pre-shaping with arabic_reshaper + python-bidi therefore *double-processes*
    the text: it happens to look OK for a simple pure-Arabic string, but reverses
    and garbles real-world output that contains quotes, dashes, numbers, or Latin
    words. So we hand the raw logical text straight to Tk and let the OS shape it.

    Kept as a function (rather than inlining) so the display path has one clear
    place to adjust if a platform ever needs manual shaping again.
    """
    return text
