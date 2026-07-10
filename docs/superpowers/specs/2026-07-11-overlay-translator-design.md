# OverlayTranslator — Design Spec

**Date:** 2026-07-11
**Status:** Approved (design), pending implementation plan

## 1. Summary

A lightweight Python desktop app for Windows that lets the user translate
on-screen English text into Arabic. The user presses a global hotkey
(**Alt+Q**), drags a box around English text anywhere on screen, and an
**Arabic translation bubble appears just above the selected box**.

- **OCR:** runs locally (no internet).
- **Translation:** DeepL API (cloud, free tier), English → Arabic.
- **Audience:** personal tool for a single Windows machine. Packaging into a
  distributable `.exe` is out of scope for v1 but the design should not
  preclude it.

## 2. Goals / Non-Goals

### Goals
- One global hotkey to trigger a screen-region selection.
- Accurate-enough local OCR of English text.
- Correct Arabic (right-to-left, properly shaped/joined) translation output.
- Translation bubble positioned just above the selected region.
- Dismiss bubble via `Esc` or a click.
- Graceful handling of empty OCR results and DeepL failures.

### Non-Goals (v1)
- Languages other than English → Arabic.
- Offline/local translation (DeepL is required).
- Distribution/installer, auto-update, multi-monitor edge polish.
- Editing/copying translated text, history, or persistent logs.

## 3. Interaction Flow

1. App runs in the background (console or tray — console for v1).
2. User presses **Alt+Q** from anywhere.
3. Screen dims slightly; cursor becomes a crosshair.
4. User drags a rectangle around English text.
5. On mouse release:
   - The selection overlay closes.
   - The selected region is screenshotted.
   - OCR extracts English text.
   - DeepL translates English → Arabic.
   - An Arabic bubble appears just above the top edge of the selected box.
6. Bubble is dismissed on `Esc` or any click.

### Edge behaviors
- **Zero-area / tiny selection** (accidental click): ignore, no bubble.
- **Empty OCR result:** bubble shows a short "No text found" message.
- **DeepL error / no network / bad key:** bubble shows a short error message.
- **Bubble near top of screen:** if there's no room above, render below the box.

## 4. Architecture

Six focused modules plus a thin entry point. Each has one responsibility, a
clear interface, and can be tested independently.

| Module         | Responsibility                                            | Primary library         |
|----------------|-----------------------------------------------------------|-------------------------|
| `hotkey`       | Listen globally for Alt+Q; invoke a callback              | `keyboard`              |
| `selector`     | Fullscreen dim + crosshair; return selected region coords | `tkinter`               |
| `capture`      | Screenshot a given region → image                         | `mss`                   |
| `ocr`          | Image → English text                                      | `pytesseract` (+Tesseract) |
| `translate`    | English text → Arabic                                     | `deepl`                 |
| `overlay`      | Render RTL Arabic bubble at a position; dismiss handling  | `tkinter`, `arabic-reshaper`, `python-bidi` |
| `main.py`      | Wire modules together; load config; own the app lifecycle | —                       |

### Data flow
```
hotkey ──▶ selector ──▶ capture ──▶ ocr ──▶ translate ──▶ overlay
        (region)      (image)     (en text) (ar text)
```

### Interfaces (sketch)
- `selector.select_region() -> Optional[Rect]`  (`None` if cancelled/too small)
- `capture.grab(rect: Rect) -> Image`
- `ocr.extract_text(image: Image) -> str`
- `translate.to_arabic(text: str) -> str`  (raises on API failure)
- `overlay.show(text: str, rect: Rect) -> None`

`Rect` = `(x, y, width, height)` in screen pixels.

## 5. Configuration

- Config file (e.g. `.env` or `config.toml`) holds:
  - `DEEPL_API_KEY` (required)
  - `HOTKEY` (default `alt+q`)
  - Optional appearance settings (font size, colors) with sane defaults.
- API key is never hardcoded; app errors clearly on startup if missing.

## 6. Startup checks

On launch, `main.py` verifies:
1. Tesseract is installed and reachable (else: clear message + link/instructions).
2. `DEEPL_API_KEY` is present (else: clear message).
Then registers the hotkey and idles.

## 7. Arabic rendering note

`tkinter` does not shape/join Arabic or handle RTL by itself. The `overlay`
module runs Arabic text through `arabic-reshaper` (letter joining) and
`python-bidi` (visual RTL ordering) before display, and right-aligns the bubble.

## 8. Error handling summary

| Condition                | Behavior                                    |
|--------------------------|---------------------------------------------|
| Selection too small      | Silently ignore                             |
| OCR finds no text        | Bubble: "No text found"                     |
| DeepL / network failure  | Bubble: short error message                 |
| Tesseract missing        | Startup error with install instructions     |
| API key missing          | Startup error                               |

## 9. Testing approach

- **Unit-testable pure pieces:** `ocr.extract_text` (fixture images),
  `translate.to_arabic` (mock DeepL client), Arabic reshaping helper.
- **Manual/integration:** hotkey → selection → bubble on a real screen.
- Keep `capture`, `selector`, `overlay` thin so the tkinter-bound parts have
  minimal logic.

## 10. Dependencies

- Runtime: `keyboard`, `mss`, `pytesseract`, `Pillow`, `deepl`,
  `arabic-reshaper`, `python-bidi`.
- External: **Tesseract OCR** (Windows installer), a **DeepL free API key**.
