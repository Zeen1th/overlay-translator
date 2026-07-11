import pytesseract
from PIL import Image


def configure_tesseract(path: str | None) -> None:
    """Point pytesseract at a specific tesseract.exe, if provided."""
    if path:
        pytesseract.pytesseract.tesseract_cmd = path


def extract_text(image: Image.Image) -> str:
    """Run local OCR on the image and return trimmed English text."""
    text = pytesseract.image_to_string(image, lang="eng")
    return text.strip()
