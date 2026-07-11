import json
import os
import socket
import subprocess
import sys
import threading

import webview

from .settings_store import load_settings
from .history_store import HistoryStore
from .web.state import AppState
from .web.server import create_app
from . import pipeline, tray
from .hotkey import HotkeyManager
from .models import Rect

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SETTINGS_PATH = os.path.join(_ROOT, "settings.json")
HISTORY_PATH = os.path.join(_ROOT, "history.json")

# Hide the console window of spawned subprocesses on Windows.
_NO_WINDOW = 0x08000000  # subprocess.CREATE_NO_WINDOW


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _spawn_select():
    """Run the selector subprocess; return a Rect or None."""
    out = subprocess.run(
        [sys.executable, "-m", "overlay_translator.proc_select"],
        capture_output=True, text=True, creationflags=_NO_WINDOW,
        env={**os.environ, "PYTHONPATH": os.path.join(_ROOT, "src")},
    ).stdout.strip()
    if not out or out == "null":
        return None
    d = json.loads(out)
    return Rect(x=d["x"], y=d["y"], width=d["width"], height=d["height"])


def _spawn_overlay(text, rect, settings):
    payload = json.dumps({
        "text": text, "x": rect.x, "y": rect.y,
        "width": rect.width, "height": rect.height,
        "font_size": settings.font_size,
        "auto_hide_seconds": settings.auto_hide_seconds,
    })
    subprocess.Popen(
        [sys.executable, "-m", "overlay_translator.proc_overlay", payload],
        creationflags=_NO_WINDOW,
        env={**os.environ, "PYTHONPATH": os.path.join(_ROOT, "src")},
    )


def run() -> None:
    settings = load_settings(SETTINGS_PATH)
    history = HistoryStore(HISTORY_PATH)
    state = AppState(settings, SETTINGS_PATH, history)

    def do_cycle():
        pipeline.run_cycle(state, select_fn=_spawn_select, overlay_fn=_spawn_overlay)

    state.translate_now = do_cycle
    state.hotkey_manager = HotkeyManager(lambda: threading.Thread(
        target=do_cycle, daemon=True).start())
    state.hotkey_manager.register(settings.hotkey)

    port = _free_port()
    app = create_app(state)
    threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port,
                               threaded=True, use_reloader=False),
        daemon=True).start()

    def on_show():
        if state.window is not None:
            state.window.show()

    def on_quit():
        os._exit(0)

    icon = tray.build_icon(on_show, on_quit)
    threading.Thread(target=icon.run, daemon=True).start()

    state.window = webview.create_window(
        "OverlayTranslator", url=f"http://127.0.0.1:{port}/",
        width=620, height=580)

    def on_closing():
        # hide to tray instead of quitting
        state.window.hide()
        return False

    state.window.events.closing += on_closing
    webview.start()
