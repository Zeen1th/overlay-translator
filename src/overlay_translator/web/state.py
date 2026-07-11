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
        self.hotkey_manager = None
        self.window = None          # pywebview window, set by the host
        self.translate_now = None   # callable set by the host to run one cycle
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
