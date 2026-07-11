import tkinter as tk
from typing import Optional
from .models import Rect

MIN_AREA = 25


def select_region() -> Optional[Rect]:
    """Show a fullscreen dim overlay; let the user drag a selection box."""
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.25)
    root.attributes("-topmost", True)
    root.configure(bg="black", cursor="crosshair")

    canvas = tk.Canvas(root, highlightthickness=0, bg="black")
    canvas.pack(fill="both", expand=True)

    state = {"x0": 0, "y0": 0, "rect_id": None, "result": None}

    def on_press(event):
        state["x0"], state["y0"] = event.x_root, event.y_root
        state["rect_id"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="#00ff00", width=2
        )

    def on_drag(event):
        if state["rect_id"] is not None:
            x0 = state["x0"] - root.winfo_rootx()
            y0 = state["y0"] - root.winfo_rooty()
            canvas.coords(state["rect_id"], x0, y0, event.x, event.y)

    def on_release(event):
        x = min(state["x0"], event.x_root)
        y = min(state["y0"], event.y_root)
        w = abs(event.x_root - state["x0"])
        h = abs(event.y_root - state["y0"])
        rect = Rect(x=x, y=y, width=w, height=h)
        state["result"] = rect if rect.area >= MIN_AREA else None
        root.destroy()

    def on_escape(_event):
        state["result"] = None
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_escape)

    root.mainloop()
    return state["result"]
