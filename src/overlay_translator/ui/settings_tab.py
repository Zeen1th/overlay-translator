import threading

import customtkinter as ctk

ENGINES = ["google", "bing", "deepl"]


class SettingsTab:
    def __init__(self, parent, app):
        self._app = app
        s = app.settings

        ctk.CTkLabel(parent, text="Hotkey", font=("Segoe UI", 13, "bold")).pack(
            anchor="w", padx=12, pady=(14, 2))
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12)
        self._hotkey_label = ctk.CTkLabel(row, text=s.hotkey)
        self._hotkey_label.pack(side="left", padx=(0, 10))
        self._record_btn = ctk.CTkButton(row, text="Record shortcut",
                                          command=self._record)
        self._record_btn.pack(side="left")

        ctk.CTkLabel(parent, text="Auto-hide (seconds)",
                     font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=12,
                                                         pady=(16, 2))
        self._auto_value = ctk.CTkLabel(parent, text=self._auto_text())
        self._auto_value.pack(anchor="w", padx=12)
        self._slider = ctk.CTkSlider(parent, from_=2, to=15, number_of_steps=13,
                                     command=self._on_slider)
        self._slider.set(s.auto_hide_seconds if s.auto_hide_seconds else 5)
        self._slider.pack(fill="x", padx=12, pady=4)
        self._off = ctk.CTkCheckBox(parent, text="Off (stay until dismissed)",
                                    command=self._on_off_toggle)
        if s.auto_hide_seconds == 0:
            self._off.select()
        self._off.pack(anchor="w", padx=12, pady=4)

        ctk.CTkLabel(parent, text="Engine", font=("Segoe UI", 13, "bold")).pack(
            anchor="w", padx=12, pady=(16, 2))
        self._engine = ctk.CTkSegmentedButton(parent, values=ENGINES,
                                              command=self._on_engine)
        self._engine.set(s.engine)
        self._engine.pack(anchor="w", padx=12, pady=4)
        ctk.CTkLabel(
            parent,
            text="Google/Bing: keyless & reliable. DeepL: best quality but its "
                 "free endpoint can be rate-limited on some networks.",
            font=("Segoe UI", 11), text_color="#888888",
            wraplength=480, justify="left").pack(anchor="w", padx=12, pady=(2, 0))

        ctk.CTkLabel(parent, text="Bubble font size",
                     font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=12,
                                                         pady=(16, 2))
        self._font = ctk.CTkSlider(parent, from_=12, to=36, number_of_steps=24,
                                   command=self._on_font)
        self._font.set(s.font_size)
        self._font.pack(fill="x", padx=12, pady=4)

        self._theme = ctk.CTkSwitch(parent, text="Light theme",
                                    command=self._on_theme)
        if s.theme == "light":
            self._theme.select()
        self._theme.pack(anchor="w", padx=12, pady=(16, 8))

    # ---- helpers --------------------------------------------------------
    def _auto_text(self):
        v = self._app.settings.auto_hide_seconds
        return "Off" if v == 0 else f"{v} s"

    def refresh(self):
        self._hotkey_label.configure(text=self._app.settings.hotkey)
        self._auto_value.configure(text=self._auto_text())
        self._record_btn.configure(text="Record shortcut", state="normal")

    # ---- handlers -------------------------------------------------------
    def _record(self):
        self._record_btn.configure(text="Press keys…", state="disabled")

        def worker():
            import keyboard
            combo = keyboard.read_hotkey(suppress=False)
            self._app._queue.put(("hotkey_recorded", combo))

        threading.Thread(target=worker, daemon=True).start()

    def _on_slider(self, value):
        if self._off.get():
            return
        self._app.settings.auto_hide_seconds = int(round(value))
        self._auto_value.configure(text=self._auto_text())
        self._app.save_settings()

    def _on_off_toggle(self):
        if self._off.get():
            self._app.settings.auto_hide_seconds = 0
        else:
            self._app.settings.auto_hide_seconds = int(round(self._slider.get()))
        self._auto_value.configure(text=self._auto_text())
        self._app.save_settings()

    def _on_engine(self, value):
        self._app.settings.engine = value
        self._app.apply_settings()

    def _on_font(self, value):
        self._app.settings.font_size = int(round(value))
        self._app.save_settings()

    def _on_theme(self):
        self._app.settings.theme = "light" if self._theme.get() else "dark"
        self._app.apply_settings()
