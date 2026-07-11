from overlay_translator.settings_store import Settings, load_settings
from overlay_translator.history_store import HistoryStore
from overlay_translator.web.state import AppState
from overlay_translator.web import server as server_mod
from overlay_translator.web.server import create_app
from overlay_translator import translate


def _ctx(tmp_path, **skw):
    st = AppState(Settings(**skw), str(tmp_path / "s.json"),
                  HistoryStore(str(tmp_path / "h.json")))
    return create_app(st).test_client(), st


def test_set_engine_updates_and_persists(tmp_path):
    c, st = _ctx(tmp_path, engine="google")
    body = c.post("/settings/engine", data={"engine": "bing"}).get_data(as_text=True)
    assert st.settings.engine == "bing"
    assert isinstance(st.engine, translate.BingEngine)
    assert load_settings(st.settings_path).engine == "bing"
    assert "bing" in body


def test_set_autohide_off(tmp_path):
    c, st = _ctx(tmp_path)
    c.post("/settings/autohide", data={"seconds": "0"})
    assert st.settings.auto_hide_seconds == 0


def test_set_font(tmp_path):
    c, st = _ctx(tmp_path)
    c.post("/settings/font", data={"size": "28"})
    assert st.settings.font_size == 28


def test_set_theme(tmp_path):
    c, st = _ctx(tmp_path, theme="light")
    body = c.post("/settings/theme", data={"theme": "dark"}).get_data(as_text=True)
    assert st.settings.theme == "dark"
    # out-of-band swap flips the <html> theme
    assert 'data-theme="dark"' in body


def test_delete_and_clear_history(tmp_path):
    c, st = _ctx(tmp_path)
    st.history.add("a", "A", "t"); st.history.add("b", "B", "t")
    target_id = st.history.entries()[0].id  # "b" is newest-first
    c.post(f"/history/delete/{target_id}")
    assert [e.source for e in st.history.entries()] == ["a"]
    c.post("/history/clear")
    assert st.history.entries() == []


def test_copy_uses_clipboard(tmp_path, monkeypatch):
    c, st = _ctx(tmp_path)
    st.history.add("a", "مرحبا", "t")
    copied = {}
    monkeypatch.setattr(server_mod, "_clipboard_copy", lambda text: copied.setdefault("v", text))
    entry_id = st.history.entries()[0].id
    c.post(f"/history/copy/{entry_id}")
    assert copied["v"] == "مرحبا"


def test_translate_invokes_host_hook(tmp_path):
    c, st = _ctx(tmp_path)
    called = {"n": 0}
    st.translate_now = lambda: called.__setitem__("n", called["n"] + 1)
    c.post("/translate")
    assert called["n"] == 1
