import mss
from PIL import Image
from .models import Rect


def grab(rect: Rect) -> Image.Image:
    """Screenshot the given screen region and return a PIL image."""
    region = {
        "left": rect.x,
        "top": rect.y,
        "width": rect.width,
        "height": rect.height,
    }
    with mss.mss() as sct:
        shot = sct.grab(region)
    return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
