from overlay_translator.settings_store import Settings
from overlay_translator.history_store import HistoryStore
from overlay_translator.web.state import AppState
from overlay_translator.web.server import create_app


def _client(tmp_path, **skw):
    st = AppState(Settings(**skw), str(tmp_path / "s.json"),
                  HistoryStore(str(tmp_path / "h.json")))
    return create_app(st), st


def test_shell_has_theme_and_htmx(tmp_path):
    app, st = _client(tmp_path, theme="dark")
    body = app.test_client().get("/").get_data(as_text=True)
    assert 'data-theme="dark"' in body
    assert "htmx.min.js" in body


def test_home_shows_hotkey_and_engine(tmp_path):
    app, st = _client(tmp_path, hotkey="alt+q", engine="bing")
    body = app.test_client().get("/home").get_data(as_text=True)
    assert "alt+q" in body
    assert "bing" in body


def test_history_lists_entries(tmp_path):
    app, st = _client(tmp_path)
    st.history.add("Hello", "مرحبا", "2026-07-11T10:00:00")
    body = app.test_client().get("/history").get_data(as_text=True)
    assert "Hello" in body
    assert "مرحبا" in body


def test_history_empty_message(tmp_path):
    app, st = _client(tmp_path)
    body = app.test_client().get("/history").get_data(as_text=True)
    assert "No translations yet" in body


def test_settings_shows_current_values(tmp_path):
    app, st = _client(tmp_path, engine="deepl", font_size=22)
    body = app.test_client().get("/settings").get_data(as_text=True)
    assert "deepl" in body
    assert "22" in body
