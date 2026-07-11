from overlay_translator.arabic import shape_for_display


def test_empty_returns_empty():
    assert shape_for_display("") == ""


def test_arabic_passthrough_unchanged():
    # Windows Tk shapes and bidi-orders Arabic itself; pre-processing it with
    # arabic_reshaper + python-bidi double-processes and reverses the text, so
    # shape_for_display must hand the raw logical text through untouched.
    src = "مرحبا بالعالم كيف حالك"
    assert shape_for_display(src) == src


def test_mixed_content_passthrough_unchanged():
    # The real-world failure case: Arabic mixed with quotes/Latin/punctuation.
    src = 'مرحبا "world" - أحمد'
    assert shape_for_display(src) == src
