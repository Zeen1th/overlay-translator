import customtkinter as ctk


class HomeTab:
    def __init__(self, parent, app):
        self._app = app
        self._status = ctk.CTkLabel(parent, text="", font=("Segoe UI", 20, "bold"))
        self._status.pack(pady=(28, 6))
        self._detail = ctk.CTkLabel(parent, text="", font=("Segoe UI", 13))
        self._detail.pack(pady=4)
        self._warn = ctk.CTkLabel(parent, text="", text_color="#e0a030",
                                  font=("Segoe UI", 12))
        self._warn.pack(pady=4)
        ctk.CTkButton(parent, text="Translate now",
                      command=app.run_translation_cycle).pack(pady=20)
        self.refresh()

    def refresh(self):
        hk = self._app.settings.hotkey
        self._status.configure(text=f"Ready — press {hk}")
        self._detail.configure(
            text=f"Engine: {self._app.settings.engine}    Hotkey: {hk}"
        )
        if self._app.tesseract_ok:
            self._warn.configure(text="")
        else:
            self._warn.configure(
                text="⚠ Tesseract not found — install it (winget install "
                     "UB-Mannheim.TesseractOCR) and restart."
            )
