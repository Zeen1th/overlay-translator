from datetime import datetime
from overlay_translator import pipeline
from overlay_translator.models import Rect
from overlay_translator.settings_store import Settings
from overlay_translator.history_store import HistoryStore
from overlay_translator.web.state import AppState
from overlay_translator import translate


class _Eng:
    def __init__(self, out=None, exc=None):
        self._out, self._exc = out, exc
    def translate(self, text):
        if self._exc:
            raise self._exc
        return self._out


def _state(tmp_path, engine_obj):
    st = AppState(Settings(), str(tmp_path / "s.json"),
                  HistoryStore(str(tmp_path / "h.json")))
    st.engine = engine_obj
    return st


def _fixed_now():
    return "2026-07-11T10:00:00"


def test_none_selection_does_nothing(tmp_path):
    st = _state(tmp_path, _Eng(out="x"))
    shown = []
    pipeline.run_cycle(st, select_fn=lambda: None,
                       overlay_fn=lambda *a: shown.append(a),
                       capture_fn=lambda r: "img", ocr_fn=lambda i: "Hello",
                       now_fn=_fixed_now)
    assert shown == []
    assert st.history.entries() == []


def test_empty_ocr_shows_no_text(tmp_path):
    st = _state(tmp_path, _Eng(out="x"))
    shown = []
    pipeline.run_cycle(st, select_fn=lambda: Rect(0, 0, 10, 10),
                       overlay_fn=lambda text, rect, settings: shown.append(text),
                       capture_fn=lambda r: "img", ocr_fn=lambda i: "  ",
                       now_fn=_fixed_now)
    assert shown == [pipeline.NO_TEXT_MSG]
    assert st.history.entries() == []


def test_translation_error_shows_message(tmp_path):
    st = _state(tmp_path, _Eng(exc=translate.TranslationError("429 boom")))
    shown = []
    pipeline.run_cycle(st, select_fn=lambda: Rect(0, 0, 10, 10),
                       overlay_fn=lambda text, rect, settings: shown.append(text),
                       capture_fn=lambda r: "img", ocr_fn=lambda i: "Hello",
                       now_fn=_fixed_now)
    assert "429 boom" in shown[0]
    assert st.history.entries() == []


def test_success_shows_bubble_and_records_history(tmp_path):
    st = _state(tmp_path, _Eng(out="مرحبا"))
    shown = []
    pipeline.run_cycle(st, select_fn=lambda: Rect(0, 0, 10, 10),
                       overlay_fn=lambda text, rect, settings: shown.append(text),
                       capture_fn=lambda r: "img", ocr_fn=lambda i: "Hello",
                       now_fn=_fixed_now)
    assert shown == ["مرحبا"]              # shape_for_display is passthrough
    e = st.history.entries()[0]
    assert (e.source, e.translation, e.timestamp) == ("Hello", "مرحبا", "2026-07-11T10:00:00")


def test_run_cycle_for_rect_skips_same_source(tmp_path):
    st = _state(tmp_path, _Eng(out="مرحبا"))
    shown = []
    result = pipeline.run_cycle_for_rect(
        st,
        Rect(0, 0, 10, 10),
        overlay_fn=lambda text, rect, settings: shown.append(text),
        capture_fn=lambda r: "img",
        ocr_fn=lambda i: "Hello",
        skip_if_source_equals="Hello",
    )
    assert result == "Hello"
    assert shown == []
    assert st.history.entries() == []
