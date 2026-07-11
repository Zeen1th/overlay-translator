from overlay_translator.arabic import shape_for_display


def test_empty_returns_empty():
    assert shape_for_display("") == ""


def test_shaping_returns_reordered_string():
    src = "مرحبا"
    out = shape_for_display(src)
    # Output is a non-empty string, reordered for visual RTL display,
    # so it differs from the raw logical-order input.
    assert isinstance(out, str)
    assert out != ""
    assert out != src


def test_shaping_preserves_ascii_passthrough():
    # Plain ASCII has nothing to reshape; characters are preserved.
    out = shape_for_display("abc")
    assert set(out) == set("abc")
