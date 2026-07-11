import tkinter as tk
from .models import Rect
from .config import Config

MARGIN = 8


def show(text: str, rect: Rect, config: Config) -> None:
    """Show a dismissible Arabic bubble just above the selected region."""
    win = tk.Tk()
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=config.bubble_fg)  # thin border effect

    label = tk.Label(
        win,
        text=text,
        justify="right",
        anchor="e",
        bg=config.bubble_bg,
        fg=config.bubble_fg,
        font=(config.font_family, config.font_size),
        wraplength=max(rect.width, 300),
        padx=12,
        pady=8,
    )
    label.pack(padx=1, pady=1)

    win.update_idletasks()
    bh = win.winfo_reqheight()

    x = rect.x
    y = rect.y - bh - MARGIN
    if y < 0:  # no room above -> place below the box
        y = rect.y + rect.height + MARGIN
    win.geometry(f"+{x}+{y}")

    win.bind("<Escape>", lambda _e: win.destroy())
    win.bind("<Button-1>", lambda _e: win.destroy())
    win.focus_force()
    win.mainloop()
