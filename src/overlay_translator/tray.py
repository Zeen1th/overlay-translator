import pystray
from PIL import Image, ImageDraw


def _make_image() -> Image.Image:
    img = Image.new("RGB", (64, 64), "#c06a4d")
    d = ImageDraw.Draw(img)
    d.rectangle((6, 6, 58, 58), outline="white", width=3)
    d.text((24, 20), "A", fill="white")
    return img


def build_icon(on_show, on_quit) -> "pystray.Icon":
    """Tray icon whose menu calls on_show()/on_quit()."""
    menu = pystray.Menu(
        pystray.MenuItem("Show", lambda icon, item: on_show(), default=True),
        pystray.MenuItem("Quit", lambda icon, item: (on_quit(), icon.stop())),
    )
    return pystray.Icon("OverlayTranslator", _make_image(),
                        "OverlayTranslator", menu)
