# OverlayTranslator

Press **Alt+Q**, drag a box over English text on screen, and see an Arabic
translation appear just above it. Local OCR (Tesseract) + DeepL API.

## Setup

1. Install Python 3.11 and Tesseract OCR
   (https://github.com/UB-Mannheim/tesseract/wiki).
2. `python -m pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your DeepL API key
   (free tier: https://www.deepl.com/pro-api).
4. `python main.py`

## Usage

- **Alt+Q** — start a selection; drag a box over English text.
- **Esc / click** — dismiss the translation bubble.
- **Ctrl+C** in the console — quit.

## Config (.env)

- `DEEPL_API_KEY` — required.
- `HOTKEY` — optional, default `alt+q`.

## Notes

- Translation needs internet; OCR runs locally.
- If Tesseract isn't on PATH, the app prints setup instructions on startup.
