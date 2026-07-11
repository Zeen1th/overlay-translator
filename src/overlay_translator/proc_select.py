"""Subprocess entry: show the region selector, print the Rect as JSON."""
import json
import sys
import tkinter as tk

from .dpi import enable_dpi_awareness
from . import selector


def main() -> None:
    enable_dpi_awareness()
    root = tk.Tk()
    root.withdraw()
    rect = selector.select_region(root)
    root.destroy()
    if rect is None:
        sys.stdout.write("null")
    else:
        sys.stdout.write(json.dumps(
            {"x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height}
        ))


if __name__ == "__main__":
    main()
