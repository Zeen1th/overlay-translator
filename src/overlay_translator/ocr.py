import os

import pytesseract
from PIL import Image

# Default install location used by the UB-Mannheim Tesseract Windows build
# (what `winget install UB-Mannheim.TesseractOCR` uses). We fall back to this
# when Tesseract isn't on PATH, so users don't have to configure anything.
_DEFAULT_WINDOWS_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def configure_tesseract(path: str | None) -> None:
    """Point pytesseract at a tesseract.exe.

    Uses the explicit ``path`` if given; otherwise, if the default Windows
    install location exists, use that. If neither applies, leave pytesseract
    to find ``tesseract`` on PATH.
    """
    if path:
        pytesseract.pytesseract.tesseract_cmd = path
    elif os.path.isfile(_DEFAULT_WINDOWS_TESSERACT):
        pytesseract.pytesseract.tesseract_cmd = _DEFAULT_WINDOWS_TESSERACT


def extract_text(image: Image.Image) -> str:
    """Run local OCR on the image and return trimmed English text."""
    text = pytesseract.image_to_string(image, lang="eng")
    return text.strip()
