from overlay_translator.models import Rect


def test_rect_area():
    r = Rect(x=10, y=20, width=100, height=50)
    assert r.area == 5000


def test_rect_zero_area():
    r = Rect(x=0, y=0, width=0, height=30)
    assert r.area == 0
