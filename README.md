# OverlayTranslator

A tray app that translates on-screen English text to Arabic. Press **Alt+Q**,
drag a box over English text, and an Arabic bubble appears just above it.
Local OCR (Tesseract) + keyless translation (Google / DeepL / Bing — no keys).

## Setup

1. Install **Python 3.11** and **Tesseract OCR**:
   ```
   winget install UB-Mannheim.TesseractOCR
   ```
2. `python -m pip install -r requirements.txt`
3. `python main.py` (or double-click `run_overlay_translator.bat`)

No account or API key needed.

## The app

- **Home** — status, current hotkey/engine, and a "Translate now" button.
- **History** — past translations (source → Arabic + time); copy, delete, clear.
- **Settings** — record a new hotkey, set the auto-hide timer (or turn it off),
  pick the engine (Google/DeepL/Bing), bubble font size, and light/dark theme.

The app lives in the **system tray**: closing the window hides it there; the
hotkey keeps working; **Quit** from the tray menu exits.

## Usage

- **Alt+Q** (or your chosen hotkey) — drag a box over English text.
- **Esc** or **click the bubble** — dismiss early (else it auto-hides).

## Notes

- Translation needs internet; OCR runs locally.
- Engines are keyless free web endpoints. Google is the most reliable; **DeepL
  can rate-limit (429)** on some connections; Bing is a good reliable
  alternative. Switch engines anytime in Settings.
- Settings and history are stored in `settings.json` / `history.json` next to
  `main.py`.
