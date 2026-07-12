import os
import threading

import pytesseract

from .. import ocr, translate
from ..settings_store import save_settings


class AppState:
    """Shared app state used by the Flask server and the hotkey pipeline."""

    def __init__(self, settings, settings_path, history):
        self.settings = settings
        self.settings_path = settings_path
        self.history = history
        self.lock = threading.Lock()
        self.cycle_lock = threading.Lock()
        self.hotkey_manager = None
        self.region_hotkey_manager = None
        self.auto_hotkey_manager = None
        self.repo_root = os.getcwd()
        self.window = None          # pywebview window, set by the host
        self.translate_now = None   # callable set by the host to run one cycle
        self.capture_region = None  # callable set by host to select + save region
        self.start_auto = None      # callable set by host to enable auto mode
        self.stop_auto = None       # callable set by host to disable auto mode
        self.toggle_auto = None     # callable set by host to toggle auto mode
        self.engine = translate.make_engine(settings.engine)
        self.tesseract_ok = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        ocr.configure_tesseract(None)
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def rebuild_engine(self) -> None:
        self.engine = translate.make_engine(self.settings.engine)

    def save(self) -> None:
        save_settings(self.settings, self.settings_path)
