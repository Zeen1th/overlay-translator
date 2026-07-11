import tkinter as tk
from .models import Rect

MARGIN = 8
BUBBLE_BG = "#1e1e1e"
BUBBLE_FG = "#ffffff"
BORDER = "#4a4a4a"


def show(text: str, rect: Rect, settings, parent, on_close=None) -> None:
    """Show a dismissible Arabic bubble just above the selected region."""
    win = tk.Toplevel(parent)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=BORDER)

    label = tk.Label(
        win, text=text, justify="right", anchor="e",
        bg=BUBBLE_BG, fg=BUBBLE_FG, font=("Segoe UI", settings.font_size),
        wraplength=max(rect.width, 300), padx=12, pady=8,
    )
    label.pack(padx=1, pady=1)

    win.update_idletasks()
    bh = win.winfo_reqheight()
    x = rect.x
    y = rect.y - bh - MARGIN
    if y < 0:
        y = rect.y + rect.height + MARGIN
    win.geometry(f"+{x}+{y}")

    def dismiss(_event=None):
        if win.winfo_exists():
            win.destroy()
        if on_close is not None:
            on_close()

    win.bind("<Escape>", dismiss)
    win.bind("<Button-1>", dismiss)
    label.bind("<Button-1>", dismiss)
    win.focus_force()

    seconds = settings.auto_hide_seconds
    if seconds and seconds > 0:
        win.after(int(seconds * 1000), dismiss)
