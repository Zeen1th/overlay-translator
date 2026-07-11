import pystray
from PIL import Image, ImageDraw


def _make_image() -> Image.Image:
    """A simple 64x64 icon: a blue rounded square with a white 'A'."""
    img = Image.new("RGB", (64, 64), "#1f6feb")
    d = ImageDraw.Draw(img)
    d.rectangle((6, 6, 58, 58), outline="white", width=3)
    d.text((22, 18), "A", fill="white")
    return img


def build_icon(request_queue) -> "pystray.Icon":
    """Build a tray icon whose menu pushes ('show',)/('quit',) to the queue."""
    def on_show(icon, item):
        request_queue.put(("show",))

    def on_quit(icon, item):
        request_queue.put(("quit",))
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Show", on_show, default=True),
        pystray.MenuItem("Quit", on_quit),
    )
    return pystray.Icon("OverlayTranslator", _make_image(),
                        "OverlayTranslator", menu)
