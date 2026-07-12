import threading
from overlay_translator.settings_store import Settings
from overlay_translator.history_store import HistoryStore
from overlay_translator.web.state import AppState
from overlay_translator import translate


def _state(tmp_path, engine="google"):
    hp = str(tmp_path / "h.json")
    return AppState(Settings(engine=engine), str(tmp_path / "s.json"),
                    HistoryStore(hp))


def test_appstate_builds_engine_and_lock(tmp_path):
    st = _state(tmp_path)
    assert isinstance(st.engine, translate.GoogleEngine)
    assert isinstance(st.lock, type(threading.Lock()))
    assert isinstance(st.cycle_lock, type(threading.Lock()))


def test_appstate_rebuild_engine_after_change(tmp_path):
    st = _state(tmp_path)
    st.settings.engine = "bing"
    st.rebuild_engine()
    assert isinstance(st.engine, translate.BingEngine)


def test_appstate_save_persists(tmp_path):
    st = _state(tmp_path)
    st.settings.font_size = 30
    st.save()
    from overlay_translator.settings_store import load_settings
    assert load_settings(st.settings_path).font_size == 30
