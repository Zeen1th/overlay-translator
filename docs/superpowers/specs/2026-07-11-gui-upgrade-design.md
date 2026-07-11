# OverlayTranslator — GUI Upgrade Design Spec

**Date:** 2026-07-11
**Status:** Approved (design), pending implementation plan
**Builds on:** the existing console app (OCR → keyless translate → overlay pipeline)

## 1. Summary

Turn the console utility into a polished **CustomTkinter desktop app** that
lives in the **system tray**. The app keeps the existing Alt+Q → select →
OCR → translate → overlay pipeline, and adds:

- A **windowed UI** with three tabs: **Home, History, Settings**.
- A **rebindable hotkey** (record-a-shortcut button in Settings).
- A **configurable auto-hide timer** for the translation bubble.
- A **persistent history** of translations (local `history.json`).
- A **choice of keyless translation engines**: Google, DeepL, Bing.

Translation direction stays **English → Arabic** (no language pickers — out
of scope).

## 2. Goals / Non-Goals

### Goals
- Tray-resident app: closing the window hides to tray; Quit (tray menu) exits.
- All tkinter work (main window, selector, overlay) runs on the **main thread**.
- Settings persisted to `settings.json`; history to `history.json` (cap 200).
- Auto-hide bubble after N seconds (configurable; Esc/click still dismiss early;
  "off" = stay until dismissed).
- Three keyless engines selectable at runtime, default Google.
- Modern dark look, light/dark theme toggle.

### Non-Goals
- Languages other than English → Arabic.
- Official DeepL API / API-key entry (all engines are keyless now).
- Cloud sync, accounts, export formats, packaging/installer.
- Editing history entries (only copy / delete / clear-all).

## 3. Translation engines

All keyless (no API key). Selected by `settings.engine`:

| Engine key | Library | Endpoint | Notes |
|-----------|---------|----------|-------|
| `google` (default) | `deep-translator` | Google free web | Reliable; current engine |
| `deepl` | `translators` | `www2.deepl.com/jsonrpc` | Best Arabic; **can rate-limit (429)** on shared IPs |
| `bing` | `translators` | Bing free web | Reliable, high quality |

Each engine is wrapped so it exposes one method: `translate(text) -> str`.
`to_arabic(text, engine)` returns `""` for empty input and wraps any failure
(including a DeepL 429) in `TranslationError`, which the pipeline catches and
shows as a friendly error bubble. The official DeepL-API engine from the
previous version is removed.

## 4. Persistence

### settings.json (in the app folder, next to main.py)
```json
{
  "hotkey": "alt+q",
  "auto_hide_seconds": 5,
  "engine": "google",
  "font_size": 18,
  "theme": "dark"
}
```
- `auto_hide_seconds`: `0` means "off / stay until dismissed"; otherwise 2–15.
- `theme`: `"dark"` or `"light"` (CustomTkinter appearance mode for the window).
- Missing file → written with defaults on first run. Missing/invalid keys →
  filled from defaults (never crash on a partial file).

### history.json (in the app folder)
```json
[
  {"source": "Hello", "translation": "مرحبا", "timestamp": "2026-07-11T14:03:22"}
]
```
- Newest-first. Appended only on **successful** translations (not on empty-OCR
  or errors). Capped at the **200** most recent entries. Corrupt file →
  treated as empty (logged to console), never crashes.

## 5. UI

Built with CustomTkinter. Main window is a `CTk` root with a `CTkTabview`
holding three tabs. Theme follows `settings.theme`.

- **Home tab:** status line ("Ready — press <hotkey>"), current engine, current
  hotkey, and a "Translate now" button that triggers a selection immediately.
- **History tab:** a scrollable frame, newest first. Each row shows
  `source → translation` and the timestamp, with a **Copy** button (copies the
  Arabic translation) and a **Delete** button. A **Clear all** button at the
  top. Refreshes after each new translation and after delete/clear.
- **Settings tab:**
  - **Record hotkey** button: captures the next key combo via the `keyboard`
    library and saves it; re-registers the global hotkey live.
  - **Auto-hide** slider (2–15s) plus an **Off** checkbox.
  - **Engine** segmented control: Google / DeepL / Bing.
  - **Font size** slider for the bubble.
  - **Theme** switch: dark / light.
  - Changes save immediately to `settings.json` and take effect without restart.

## 6. Architecture & threading

The window owns the **main-thread** event loop (`app.mainloop()`). Two other
threads only *signal* the main thread through a `queue.Queue`, which the window
drains via `app.after(50, poll)`:

- **keyboard thread** (global hotkey): puts a `("translate",)` request.
- **tray thread** (`pystray` icon.run): puts `("show",)` or `("quit",)`.

The poll handler runs the actual work on the main thread:
- `("translate",)` → run one selection→OCR→translate→overlay cycle, then append
  to history and refresh the History tab.
- `("show",)` → `app.deiconify()` / raise the window.
- `("quit",)` → stop the tray, unhook the hotkey, destroy the window.

**Selector & overlay become `Toplevel` windows** of the main `CTk` root
(instead of separate `tk.Tk()` roots) to avoid multiple-root problems. Each is
shown modally-ish with `wait_window` (selector) or an auto-hide timer
(overlay). This keeps every tkinter object under one root on one thread — the
crash-safety property from the earlier threading fix is preserved.

Closing the window (X / `WM_DELETE_WINDOW`) calls `app.withdraw()` (hide to
tray), it does **not** quit. Quit happens only from the tray menu.

### Module layout
```
src/overlay_translator/
  models.py            (unchanged: Rect)
  ocr.py               (unchanged)
  capture.py           (unchanged)
  arabic.py            (unchanged)
  translate.py         (engines: Google/DeepL/Bing; make_engine(name))
  settings_store.py    (Settings dataclass + load/save settings.json)
  history_store.py     (HistoryEntry + load/add/delete/clear history.json)
  selector.py          (refactor: select_region(parent) -> Toplevel)
  overlay.py           (refactor: show(text, rect, settings, parent) + auto-hide)
  tray.py              (pystray icon + menu -> queue signals)
  hotkey.py            (register/re-register global hotkey -> queue signal)
  app.py               (wires stores + UI + threads; runs mainloop)
  ui/
    app_window.py      (CTk root + CTkTabview + poll loop)
    home_tab.py
    history_tab.py
    settings_tab.py
main.py                (unchanged entry: bootstraps src, calls app.run)
```

## 7. Error handling

| Condition | Behavior |
|---|---|
| Selection too small / Esc | No bubble, no history entry |
| OCR finds no text | Bubble "No text found"; no history entry |
| Engine failure (incl. DeepL 429) | Bubble with friendly error; no history entry |
| Corrupt settings.json / history.json | Treat as defaults/empty; log to console; continue |
| Hotkey string invalid when (re)registering | Keep previous hotkey; show a message in Settings |

## 8. Testing

- **Unit-tested (pure logic):**
  - `settings_store`: defaults, round-trip save/load, partial/corrupt file → defaults.
  - `history_store`: add (newest-first), 200-cap trimming, delete by index, clear,
    round-trip, corrupt file → empty.
  - `translate`: `make_engine(name)` returns the right wrapper; unknown name raises;
    `to_arabic` empty-guard and error-wrapping (engines mocked — no network).
- **Manual/integration (GUI/system-bound):** tray show/quit, window tabs, record-
  hotkey, live Alt+Q cycle, auto-hide timing, history row copy/delete/clear.
- Keep GUI files thin; put logic in the stores so it stays unit-testable.

## 9. Dependencies (added)

- `customtkinter` (modern UI), `pystray` + `Pillow` (tray icon; Pillow already
  present), `translators` (keyless DeepL/Bing). Existing: `deep-translator`,
  `mss`, `pytesseract`, `keyboard`, `arabic-reshaper`, `python-bidi`,
  `python-dotenv` (kept for compatibility, no longer required).
