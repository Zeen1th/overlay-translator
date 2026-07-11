# OverlayTranslator

Press **Alt+Q**, drag a box over English text on screen, and see an Arabic
translation appear just above it. Local OCR (Tesseract) + keyless translation
(Google's free web endpoint by default — no API key or signup needed).

## Setup

1. Install **Python 3.11** and **Tesseract OCR**. On Windows the easiest way is:
   ```
   winget install UB-Mannheim.TesseractOCR
   ```
   (or the installer at https://github.com/UB-Mannheim/tesseract/wiki). The app
   auto-detects the default install location, so no PATH setup is needed.
2. `python -m pip install -r requirements.txt`
3. `python main.py`

That's it — no key or account required with the default engine.

## Usage

- **Alt+Q** — start a selection; drag a box over English text.
- **Esc** or **click the bubble** — dismiss the translation.
- While a translation bubble is showing, Alt+Q is paused until you dismiss it.
- **Ctrl+C** in the console — quit.

## Config (.env, optional)

Copy `.env.example` to `.env` only if you want to change defaults.

- `TRANSLATION_ENGINE` — `google` (default, keyless) or `deepl_api`.
- `DEEPL_API_KEY` — required **only** if `TRANSLATION_ENGINE=deepl_api`
  (free key: https://www.deepl.com/pro-api). DeepL gives higher Arabic quality.
- `HOTKEY` — optional, default `alt+q`.
- `TESSERACT_CMD` — optional; only needed if Tesseract isn't found automatically.

## Notes

- Translation needs internet; OCR runs locally.
- The default `google` engine uses Google's free public endpoint — no key, but
  it's an unofficial endpoint that can rate-limit heavy use. For guaranteed
  stability and the best Arabic quality, switch to `deepl_api` with a free key.
- If Tesseract can't be found, the app prints setup instructions on startup.
