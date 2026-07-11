import ctypes
import os
import queue
import threading

from .settings_store import load_settings
from .history_store import HistoryStore
from . import tray
from .ui.app_window import AppWindow

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SETTINGS_PATH = os.path.join(_ROOT, "settings.json")
HISTORY_PATH = os.path.join(_ROOT, "history.json")

# Windows DPI awareness context: PER_MONITOR_AWARE_V2
_PER_MONITOR_AWARE_V2 = -4


def enable_dpi_awareness(user32=None) -> bool:
    """Make the process per-monitor DPI-aware (Windows) so tkinter reports and
    uses PHYSICAL pixels.

    Must run BEFORE any Tk/CustomTkinter window is created. Without this, on a
    scaled high-DPI display the fullscreen selection overlay only covers the
    logical (scaled-down) screen area and its mouse coordinates no longer match
    the physical pixels that `mss` captures. Returns True on success; safely
    returns False on non-Windows or if the call fails.
    """
    if user32 is None:
        windll = getattr(ctypes, "windll", None)
        if windll is None:  # not Windows
            return False
        user32 = windll.user32
    try:
        return bool(
            user32.SetProcessDpiAwarenessContext(
                ctypes.c_void_p(_PER_MONITOR_AWARE_V2)
            )
        )
    except Exception:
        return False


def run() -> None:
    enable_dpi_awareness()
    settings = load_settings(SETTINGS_PATH)
    history = HistoryStore(HISTORY_PATH)
    request_queue: "queue.Queue" = queue.Queue()

    app = AppWindow(settings, SETTINGS_PATH, history, request_queue)

    icon = tray.build_icon(request_queue)
    threading.Thread(target=icon.run, daemon=True).start()

    app.mainloop()
