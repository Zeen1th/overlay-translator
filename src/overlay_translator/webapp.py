import json
import os
import socket
import subprocess
import sys
import threading
import time

import webview

from .settings_store import load_settings
from .history_store import HistoryStore
from .web.state import AppState
from .web.server import create_app
from . import pipeline, startup, tray
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
    result = subprocess.run(
        [sys.executable, "-m", "overlay_translator.proc_select"],
        capture_output=True, text=True, creationflags=_NO_WINDOW,
        env={**os.environ, "PYTHONPATH": os.path.join(_ROOT, "src")},
    )
    if result.returncode != 0 and result.stderr:
        print(f"[overlay-translator] selector failed: {result.stderr.strip()[:300]}")
    out = (result.stdout or "").strip()
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


def _saved_rect(settings):
    data = settings.ocr_region
    if not data:
        return None
    return Rect(
        x=int(data["x"]),
        y=int(data["y"]),
        width=int(data["width"]),
        height=int(data["height"]),
    )


def _wait_for_port(port, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(0.25)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.05)
    return False


def run() -> None:
    settings = load_settings(SETTINGS_PATH)
    settings.start_with_windows = startup.is_startup_enabled()
    history = HistoryStore(HISTORY_PATH)
    state = AppState(settings, SETTINGS_PATH, history)
    state.repo_root = _ROOT
    state.save()

    auto_stop = threading.Event()
    auto_thread = {"value": None}
    last_auto_source = {"value": None}

    def do_cycle(*, prefer_saved_region=False, suppress_feedback=False,
                 skip_if_same_source=None):
        if not state.cycle_lock.acquire(blocking=False):
            return None
        try:
            rect = _saved_rect(state.settings) if prefer_saved_region else None
            if rect is None:
                rect = _spawn_select()
            if rect is None:
                return None
            return pipeline.run_cycle_for_rect(
                state,
                rect,
                overlay_fn=_spawn_overlay,
                suppress_feedback=suppress_feedback,
                skip_if_source_equals=skip_if_same_source,
            )
        finally:
            state.cycle_lock.release()

    def capture_region():
        rect = _spawn_select()
        if rect is None:
            return False
        with state.lock:
            state.settings.ocr_region = {
                "x": rect.x,
                "y": rect.y,
                "width": rect.width,
                "height": rect.height,
            }
            state.settings.use_saved_region = True
            state.save()
        return True

    def stop_auto_translate():
        auto_stop.set()
        t = auto_thread["value"]
        if t is not None and t.is_alive():
            t.join(timeout=1.5)
        auto_thread["value"] = None
        with state.lock:
            state.settings.auto_translate_enabled = False
            state.save()
        last_auto_source["value"] = None
        return False

    def _auto_loop():
        while not auto_stop.wait(1.0):
            if not state.settings.auto_translate_enabled:
                continue
            if _saved_rect(state.settings) is None:
                continue
            source = do_cycle(
                prefer_saved_region=True,
                suppress_feedback=True,
                skip_if_same_source=last_auto_source["value"],
            )
            if source:
                last_auto_source["value"] = source
            else:
                last_auto_source["value"] = None

    def start_auto_translate():
        if _saved_rect(state.settings) is None:
            return False
        with state.lock:
            state.settings.use_saved_region = True
            state.settings.auto_translate_enabled = True
            state.save()
        auto_stop.clear()
        if auto_thread["value"] is None or not auto_thread["value"].is_alive():
            auto_thread["value"] = threading.Thread(target=_auto_loop, daemon=True)
            auto_thread["value"].start()
        return True

    def toggle_auto_translate():
        if state.settings.auto_translate_enabled:
            return stop_auto_translate()
        return start_auto_translate()

    state.translate_now = lambda: do_cycle()
    state.capture_region = capture_region
    state.start_auto = start_auto_translate
    state.stop_auto = stop_auto_translate
    state.toggle_auto = toggle_auto_translate
    state.hotkey_manager = HotkeyManager(lambda: threading.Thread(
        target=lambda: do_cycle(), daemon=True).start())
    state.region_hotkey_manager = HotkeyManager(lambda: threading.Thread(
        target=capture_region, daemon=True).start())
    state.auto_hotkey_manager = HotkeyManager(lambda: threading.Thread(
        target=toggle_auto_translate, daemon=True).start())
    state.hotkey_manager.register(settings.hotkey)
    state.region_hotkey_manager.register(settings.region_hotkey)
    state.auto_hotkey_manager.register(settings.auto_toggle_hotkey)
    if state.settings.auto_translate_enabled:
        start_auto_translate()

    port = _free_port()
    app = create_app(state)
    threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port,
                               threaded=True, use_reloader=False),
        daemon=True).start()
    _wait_for_port(port)

    def on_show():
        if state.window is not None:
            state.window.show()

    def on_quit():
        stop_auto_translate()
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
