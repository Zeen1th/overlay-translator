"""Subprocess entry: show the Arabic bubble from a JSON argument."""
import json
import sys
import tkinter as tk

from .dpi import enable_dpi_awareness
from .models import Rect
from .settings_store import Settings
from . import overlay


def main(argv) -> None:
    enable_dpi_awareness()
    data = json.loads(argv[1])
    rect = Rect(x=data["x"], y=data["y"],
                width=data["width"], height=data["height"])
    settings = Settings(font_size=data.get("font_size", 18),
                        auto_hide_seconds=data.get("auto_hide_seconds", 5))
    root = tk.Tk()
    root.withdraw()
    overlay.show(data["text"], rect, settings, root, on_close=root.quit)
    root.mainloop()
    root.destroy()


if __name__ == "__main__":
    main(sys.argv)
