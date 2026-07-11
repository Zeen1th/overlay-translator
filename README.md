# OverlayTranslator

A tray app that translates on-screen English text to Arabic. Press **Alt+Q**,
drag a box over English text, and an Arabic bubble appears just above it.
Local OCR (Tesseract) + keyless translation (Google / Bing / DeepL — no keys,
no signup).

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
  pick the engine (Google/Bing/DeepL), set the bubble font size, and
  light/dark theme.

The app lives in the **system tray**: closing the window hides it there; the
hotkey keeps working; **Quit** from the tray menu exits.

## Usage

- **Alt+Q** (or your chosen hotkey) — drag a box over English text.
- **Esc** or **click the bubble** — dismiss early (else it auto-hides).

## Notes

- Translation needs internet; OCR runs locally.
- All three engines are **keyless** free web endpoints — no signup.
  **Google** and **Bing** are the most reliable. **DeepL** gives the best Arabic
  quality and uses its free web endpoint the same way Translumo/DeepLX do, but
  that endpoint is **rate-limited by IP (HTTP 429)** — it works on most home
  connections but can be temporarily blocked on shared/VPN/datacenter IPs. If
  DeepL fails, the app retries once and then suggests switching engine.
- Settings and history are stored in `settings.json` / `history.json` next to
  `main.py`.
