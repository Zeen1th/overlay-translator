# OverlayTranslator — HTMX Frontend Design Spec

**Date:** 2026-07-11
**Status:** Approved (design), pending implementation plan
**Replaces:** the CustomTkinter window UI (Home/History/Settings tabs)

## 1. Summary

Replace the CustomTkinter desktop UI with a **local Flask + HTMX web UI rendered
in a native pywebview window** (WebView2 on Windows), styled with a warm
**creamy-beige** design system (light) plus a **warm espresso** dark mode.

The native translation pipeline is preserved: global hotkey → drag-select →
screen capture → local OCR → keyless translation → floating Arabic bubble →
persistent history. The screen selector and the result bubble stay as the
existing tkinter code but run as **short-lived subprocesses**, because pywebview
and tkinter cannot both own the main GUI thread.

## 2. Goals / Non-Goals

### Goals
- A visibly better UI: creamy-beige light + warm espresso dark, toggle in Settings.
- Feature parity with the current app: Home (status + Translate now), History
  (list, copy, delete, clear, live refresh), Settings (record hotkey, auto-hide
  timer, engine, bubble font size, theme).
- Runs as a tray app in a native pywebview window; closing the window hides to
  tray; Quit exits.
- UI works offline (HTMX + CSS vendored locally; no CDN).
- Reuse existing logic modules unchanged where possible.

### Non-Goals
- Languages other than English → Arabic.
- Remote/hosted server, auth, multi-user.
- Rewriting the selector/overlay rendering (reused as-is via subprocess).
- Packaging/installer.

## 3. Architecture

### Processes & threads
**Main process:**
- **Main thread:** the pywebview window (`webview.start()`), pointed at the
  local Flask URL.
- **Daemon thread — Flask:** serves the HTMX UI + endpoints on
  `127.0.0.1:<free-port>` (port chosen at startup by binding to port 0).
- **Daemon thread — hotkey:** global hotkey listener; on trigger runs one
  pipeline cycle.
- **Daemon thread — tray:** pystray icon with Show / Quit.
- **Shared state:** one `Settings`, one `HistoryStore`, guarded by a
  `threading.Lock` for cross-thread reads/writes (Flask vs hotkey pipeline).

**Subprocesses (spawned per use, tkinter, DPI-aware):**
- `python -m overlay_translator.proc_select` → shows the dim fullscreen
  selector, prints the selected `Rect` as JSON to stdout (or `null`).
- `python -m overlay_translator.proc_overlay <json>` → shows the Arabic bubble
  for the given text/rect/font/auto-hide, then exits.
- Both call `enable_dpi_awareness()` at startup and are launched with a hidden
  console (`pythonw.exe` or `CREATE_NO_WINDOW`).

### Pipeline (hotkey thread or POST /translate)
1. Spawn `proc_select`; read the `Rect` (return silently if `null`).
2. `capture.grab(rect)` → `ocr.extract_text` → empty → bubble "No text found".
3. `translate.to_arabic(text, engine)` → on `TranslationError` → bubble with the
   engine's message (e.g. the DeepL rate-limit note).
4. Spawn `proc_overlay` with `arabic.shape_for_display(ar)` (passthrough),
   rect, font size, auto-hide seconds.
5. `history.add(en, ar, timestamp)` under the lock.

### Module reuse
- **Unchanged:** `models`, `capture`, `ocr`, `arabic`, `translate`,
  `settings_store`, `history_store`, `hotkey` (HotkeyManager), `app` DPI helper.
- **Adapted for standalone use:** `selector.select_region()` and
  `overlay.show()` gain thin `__main__`-style process wrappers
  (`proc_select.py`, `proc_overlay.py`) that create their own tkinter root.
- **New:** `server.py` (Flask app factory + routes), `webapp.py` (builds the
  Flask app, launches Flask thread + tray thread, runs pywebview), `pipeline.py`
  (the select→translate→overlay→history cycle used by both the hotkey and
  `/translate`), `templates/`, `static/`.
- **Removed:** `ui/` package (CustomTkinter window + tabs), `ui/app_window.py`;
  `app.py` becomes the entry that calls `webapp.run()`. CustomTkinter dependency
  dropped.

## 4. Web UI (Flask routes)

All responses are server-rendered HTML (full page for `/`, fragments otherwise).

| Method & path | Purpose |
|---|---|
| `GET /` | Shell: `<html data-theme>`, left nav (Home/History/Settings), loads Home into `#panel`. |
| `GET /home` | Status ("Ready — press <hotkey>"), engine + hotkey, **Translate now** (`hx-post="/translate"`), Tesseract-missing warning. |
| `GET /history` | Rows (newest first): `en → ar` + timestamp, Copy / Delete; Clear-all. Root element `hx-trigger="load, every 2s"` so hotkey translations appear live. |
| `GET /settings` | Controls (below). |
| `POST /translate` | Run one pipeline cycle; returns the Home fragment (status). |
| `POST /settings/engine` | Body `engine=google|bing|deepl`; update + save; return Settings fragment. |
| `POST /settings/autohide` | Body `seconds` (0=off, else 2–15); update + save. |
| `POST /settings/font` | Body `size` (12–36); update + save. |
| `POST /settings/theme` | Body `theme=light|dark`; update + save; returns fragment that also swaps `data-theme` (via `hx-swap-oob` on `<html>` or an out-of-band script). |
| `POST /settings/hotkey/record` | Blocks on `keyboard.read_hotkey`, registers it, saves; returns Settings fragment with the new hotkey. |
| `POST /history/delete/<int:i>` | Delete row i; return History fragment. |
| `POST /history/clear` | Clear; return History fragment. |
| `POST /history/copy/<int:i>` | Copy row i's Arabic to the clipboard via `pyperclip`; return a small "Copied" indicator. |

No custom JS beyond vendored `htmx.min.js`. Copy uses a server endpoint +
`pyperclip` because JS clipboard access is unreliable inside WebView2.

## 5. Styling (design system)

Vendored `static/app.css` using CSS custom properties; `data-theme` on `<html>`
switches light/dark. Starter palette (refined during build):

**Light — creamy-beige**
- `--bg:#f4ecdf` · `--surface:#faf6ee` · `--border:#e7dac6`
- `--text:#3b332a` · `--muted:#8a7d6b` · `--accent:#c06a4d` (terracotta)

**Dark — warm espresso**
- `--bg:#221c17` · `--surface:#2c2721` · `--border:#3d362e`
- `--text:#efe6d8` · `--muted:#a89b86` · `--accent:#c06a4d`

- Type: system grotesk stack (`ui-sans-serif, "Segoe UI", system-ui`); no web
  fonts. Rounded cards (12–16px), soft shadows, gentle hover transitions.
- Arabic in history is `dir="rtl"` and right-aligned.
- Responsive to the window's default size (~560×560), single column.

## 6. Error handling

| Condition | Behavior |
|---|---|
| Selection cancelled / too small | No bubble, no history entry. |
| OCR empty | Bubble "No text found". |
| Translation fails (e.g. DeepL 429) | Bubble shows the engine's message; no history entry. |
| Subprocess fails to launch/crashes | Log to console; the pipeline aborts gracefully (no crash of the main app). |
| Corrupt settings/history JSON | Degrade to defaults/empty (existing behavior). |
| Free port / Flask bind fails | Fatal startup error printed to console. |
| WebView2 runtime missing | pywebview raises on start; print a clear message pointing to the WebView2 runtime install. |

## 7. Testing

- **Unit (Flask test client):** build the app with injected `Settings` +
  `HistoryStore`; assert `/home` shows the hotkey/engine, `/history` renders rows
  and reflects deletes/clear, each `/settings/*` POST mutates the store and the
  returned fragment shows the new value, `/history/copy` calls a stubbed
  clipboard. The pipeline is stubbed (no real capture/OCR/network) so
  `/translate` is tested against a fake pipeline function.
- **Reused unit tests:** `settings_store`, `history_store`, `translate`,
  `arabic`, `hotkey`, `dpi`, `ocr` stay green.
- **Manual/integration:** pywebview window renders; Alt+Q end-to-end; tray
  Show/Quit; theme toggle; live history refresh; subprocess selector/overlay.

## 8. Dependencies

- **Add:** `flask`, `pywebview`, `pyperclip`.
- **Keep:** `keyboard`, `mss`, `pytesseract`, `Pillow`, `deep-translator`,
  `translators`, `requests`, `pystray`, `pytest`.
- **Remove:** `customtkinter`.
