import queue
from datetime import datetime

import customtkinter as ctk
import pytesseract

from .. import capture, ocr, translate, arabic, overlay, selector
from ..hotkey import HotkeyManager
from .home_tab import HomeTab
from .history_tab import HistoryTab
from .settings_tab import SettingsTab

NO_TEXT_MSG = "No text found"
ERROR_MSG = "Translation failed — the engine may be rate-limited or offline. Try again, or switch engine in Settings."


class AppWindow(ctk.CTk):
    def __init__(self, settings, settings_path, history, request_queue):
        super().__init__()
        self.settings = settings
        self._settings_path = settings_path
        self.history = history
        self._queue = request_queue
        self._busy = False

        self.title("OverlayTranslator")
        self.geometry("560x520")
        ctk.set_appearance_mode(self.settings.theme)

        self.engine = translate.make_engine(self.settings.engine)
        self.hotkey_manager = HotkeyManager(
            lambda: self._queue.put(("translate",))
        )
        self.hotkey_manager.register(self.settings.hotkey)
        self.tesseract_ok = self._check_tesseract()

        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=12, pady=12)
        self.home_tab = HomeTab(tabview.add("Home"), self)
        self.history_tab = HistoryTab(tabview.add("History"), self)
        self.settings_tab = SettingsTab(tabview.add("Settings"), self)

        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        self.after(50, self._poll)

    # ---- startup helpers ------------------------------------------------
    def _check_tesseract(self) -> bool:
        ocr.configure_tesseract(None)
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    # ---- queue loop -----------------------------------------------------
    def _poll(self):
        try:
            while True:
                try:
                    msg = self._queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    self._handle(msg)
                except Exception as exc:  # never let one bad message kill the loop
                    print(f"[overlay-translator] error handling {msg!r}: {exc}")
        finally:
            self.after(50, self._poll)

    def _handle(self, msg):
        kind = msg[0]
        if kind == "translate":
            self.run_translation_cycle()
        elif kind == "show":
            self._show_window()
        elif kind == "quit":
            self._quit_app()
        elif kind == "hotkey_recorded":
            self.settings.hotkey = msg[1]
            self.hotkey_manager.register(msg[1])
            self.save_settings()
            self.home_tab.refresh()
            self.settings_tab.refresh()

    # ---- window lifecycle ----------------------------------------------
    def _hide_to_tray(self):
        self.withdraw()

    def _show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _quit_app(self):
        # The keyboard hotkey is unhooked automatically on process exit.
        self.destroy()

    # ---- settings -------------------------------------------------------
    def save_settings(self):
        from ..settings_store import save_settings
        save_settings(self.settings, self._settings_path)

    def apply_settings(self):
        ctk.set_appearance_mode(self.settings.theme)
        self.engine = translate.make_engine(self.settings.engine)
        self.hotkey_manager.register(self.settings.hotkey)
        self.save_settings()
        self.home_tab.refresh()

    # ---- the pipeline (main thread) ------------------------------------
    def run_translation_cycle(self):
        if self._busy:
            return
        self._busy = True
        try:
            rect = selector.select_region(self)
            if rect is None:
                return
            try:
                image = capture.grab(rect)
                english = ocr.extract_text(image)
            except Exception:
                overlay.show(ERROR_MSG, rect, self.settings, self)
                return
            if not english:
                overlay.show(NO_TEXT_MSG, rect, self.settings, self)
                return
            try:
                ar = translate.to_arabic(english, self.engine)
            except translate.TranslationError:
                overlay.show(ERROR_MSG, rect, self.settings, self)
                return
            overlay.show(arabic.shape_for_display(ar), rect, self.settings, self)
            self.history.add(english, ar,
                             datetime.now().isoformat(timespec="seconds"))
            self.history_tab.refresh()
        finally:
            self._busy = False
