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


def run() -> None:
    settings = load_settings(SETTINGS_PATH)
    history = HistoryStore(HISTORY_PATH)
    request_queue: "queue.Queue" = queue.Queue()

    app = AppWindow(settings, SETTINGS_PATH, history, request_queue)

    icon = tray.build_icon(request_queue)
    threading.Thread(target=icon.run, daemon=True).start()

    app.mainloop()
