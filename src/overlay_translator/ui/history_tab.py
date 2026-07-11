import customtkinter as ctk


class HistoryTab:
    def __init__(self, parent, app):
        self._app = app
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", pady=(6, 4))
        ctk.CTkLabel(top, text="History", font=("Segoe UI", 16, "bold")).pack(
            side="left", padx=6)
        ctk.CTkButton(top, text="Clear all", width=90,
                      command=self._clear).pack(side="right", padx=6)
        self._list = ctk.CTkScrollableFrame(parent)
        self._list.pack(fill="both", expand=True, padx=4, pady=4)
        self.refresh()

    def _clear(self):
        self._app.history.clear()
        self.refresh()

    def _copy(self, text):
        self._app.clipboard_clear()
        self._app.clipboard_append(text)

    def _delete(self, index):
        self._app.history.delete(index)
        self.refresh()

    def refresh(self):
        for child in self._list.winfo_children():
            child.destroy()
        entries = self._app.history.entries()
        if not entries:
            ctk.CTkLabel(self._list, text="No translations yet.").pack(pady=20)
            return
        for i, e in enumerate(entries):
            row = ctk.CTkFrame(self._list)
            row.pack(fill="x", pady=3, padx=2)
            text = f"{e.source}  →  {e.translation}"
            ctk.CTkLabel(row, text=text, anchor="w", justify="left",
                         wraplength=360).grid(row=0, column=0, sticky="w",
                                              padx=6, pady=(4, 0), columnspan=3)
            ctk.CTkLabel(row, text=e.timestamp, font=("Segoe UI", 10),
                         text_color="#888888").grid(row=1, column=0, sticky="w",
                                                    padx=6, pady=(0, 4))
            ctk.CTkButton(row, text="Copy", width=56,
                          command=lambda t=e.translation: self._copy(t)).grid(
                              row=1, column=1, padx=2)
            ctk.CTkButton(row, text="Delete", width=64, fg_color="#8a3030",
                          command=lambda idx=i: self._delete(idx)).grid(
                              row=1, column=2, padx=2)
            row.grid_columnconfigure(0, weight=1)
