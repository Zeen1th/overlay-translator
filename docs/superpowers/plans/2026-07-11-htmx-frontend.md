# OverlayTranslator HTMX Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the CustomTkinter window UI with a creamy-beige Flask + HTMX web UI rendered in a native pywebview window, keeping the native hotkey → select → OCR → translate → overlay → history pipeline (selector/overlay run as subprocesses so tkinter never fights pywebview for the main thread).

**Architecture:** A main process runs pywebview on the main thread, a Flask server + global-hotkey listener + system tray on daemon threads, and shared `Settings`/`HistoryStore` behind a lock. The translation pipeline spawns the existing tkinter selector/overlay as short-lived DPI-aware subprocesses. Flask serves server-rendered HTML fragments swapped by vendored HTMX; a hand-written CSS design system provides creamy-beige light + warm espresso dark themes.

**Tech Stack:** Python 3.11, Flask, pywebview (WebView2), pyperclip, HTMX (vendored), keyboard, mss, pytesseract, deep-translator/translators/requests, pystray, pytest.

## Global Constraints

- Python **3.11**; run pip as `python -m pip`, tests as `python -m pytest` from repo root (`pytest.ini` sets `pythonpath = src`).
- Windows 11. Package root `src/overlay_translator/`.
- English → Arabic only. Engines keyless: `google`/`bing`/`deepl` (default `google`).
- UI must work offline: **HTMX and CSS are vendored** in `static/`; no CDN references.
- `settings.json`/`history.json` live in the repo root; history cap 200; append only on success.
- Themes: `light` = creamy-beige, `dark` = warm espresso; toggled via `data-theme` on `<html>`. Accent terracotta `#c06a4d`.
- All tkinter runs ONLY inside the `proc_select`/`proc_overlay` subprocesses (each calls DPI-awareness at startup, launched with a hidden console). The main process never imports tkinter.
- Shared `Settings`/`HistoryStore` access is guarded by a `threading.Lock`.
- New deps: `flask`, `pywebview`, `pyperclip`. Removed: `customtkinter`.

---

## File Structure

```
src/overlay_translator/
├── models.py, capture.py, ocr.py, arabic.py            (unchanged)
├── translate.py, settings_store.py, history_store.py   (unchanged)
├── hotkey.py                                            (unchanged)
├── dpi.py                          (NEW: enable_dpi_awareness moved here)
├── pipeline.py                     (NEW: run_cycle — the translate flow)
├── proc_select.py                  (NEW: subprocess — run selector, print Rect)
├── proc_overlay.py                 (NEW: subprocess — show bubble from argv)
├── overlay.py                      (MODIFY: add on_close callback)
├── selector.py                     (unchanged; called with a throwaway root)
├── tray.py                         (unchanged)
├── app.py                          (REWRITE: thin -> webapp.run)
├── web/
│   ├── __init__.py                 (NEW: empty)
│   ├── state.py                    (NEW: AppState container)
│   └── server.py                   (NEW: Flask app factory + routes)
├── templates/
│   ├── shell.html, home.html, history.html, settings.html   (NEW)
├── static/
│   ├── app.css                     (NEW: creamy-beige design system)
│   └── htmx.min.js                 (NEW: vendored)
├── webapp.py                       (NEW: host — flask thread + tray + pywebview)
└── ui/                             (DELETE at Task 6)
main.py                             (unchanged)
```

---

## Task 1: Dependencies, move DPI helper, AppState

**Files:**
- Modify: `requirements.txt`
- Create: `src/overlay_translator/dpi.py`
- Modify: `src/overlay_translator/app.py` (temporarily re-export; fully rewritten in Task 6)
- Modify: `tests/test_dpi.py` (import from new location)
- Create: `src/overlay_translator/web/__init__.py` (empty)
- Create: `src/overlay_translator/web/state.py`
- Test: `tests/test_state.py`

**Interfaces:**
- Produces `dpi.enable_dpi_awareness(user32=None) -> bool` (moved verbatim from app.py).
- Produces `web.state.AppState`:
  - `__init__(self, settings, settings_path, history)` — stores them, a `threading.Lock` as `.lock`, builds `.engine` from settings, sets `.tesseract_ok` (checked via pytesseract), `.hotkey_manager=None`, `.window=None`, `.translate_now=None` (a callable set by the host).
  - `rebuild_engine(self) -> None` — `self.engine = translate.make_engine(self.settings.engine)`.
  - `save(self) -> None` — `settings_store.save_settings(self.settings, self.settings_path)`.

- [ ] **Step 1: Add/remove deps in `requirements.txt`**

Set the file to exactly:
```
keyboard==0.13.5
mss==9.0.1
pytesseract==0.3.13
Pillow==10.4.0
deep-translator==1.11.4
translators==5.9.2
requests==2.33.0
pystray==0.19.5
flask==3.1.3
pywebview==6.2.1
pyperclip==1.9.0
pytest==8.3.2
```

- [ ] **Step 2: Install**

Run: `python -m pip install -r requirements.txt`
Expected: "Successfully installed ..." / "Requirement already satisfied".

- [ ] **Step 3: Create `src/overlay_translator/dpi.py`** (move the helper)

```python
import ctypes

# Windows DPI awareness context: PER_MONITOR_AWARE_V2
_PER_MONITOR_AWARE_V2 = -4


def enable_dpi_awareness(user32=None) -> bool:
    """Make the process per-monitor DPI-aware (Windows) so tkinter reports and
    uses PHYSICAL pixels. Must run BEFORE any Tk window is created. Returns True
    on success; safely returns False on non-Windows or if the call fails."""
    if user32 is None:
        windll = getattr(ctypes, "windll", None)
        if windll is None:
            return False
        user32 = windll.user32
    try:
        return bool(
            user32.SetProcessDpiAwarenessContext(
                ctypes.c_void_p(_PER_MONITOR_AWARE_V2)
            )
        )
    except Exception:
        return False
```

- [ ] **Step 4: Point `tests/test_dpi.py` at the new module**

Change its import line `from overlay_translator.app import enable_dpi_awareness` to:
```python
from overlay_translator.dpi import enable_dpi_awareness
```

- [ ] **Step 5: Keep `app.py` importable during the transition**

Replace `src/overlay_translator/app.py` contents with a temporary shim (fully rewritten in Task 6):
```python
from .dpi import enable_dpi_awareness  # noqa: F401  (re-export during transition)
```

- [ ] **Step 6: Run DPI tests**

Run: `python -m pytest tests/test_dpi.py -q`
Expected: PASS (3 passed).

- [ ] **Step 7: Create `web/__init__.py`** (empty, 0 bytes).

- [ ] **Step 8: Write failing tests for AppState**

Create `tests/test_state.py`:
```python
import threading
from overlay_translator.settings_store import Settings
from overlay_translator.history_store import HistoryStore
from overlay_translator.web.state import AppState
from overlay_translator import translate


def _state(tmp_path, engine="google"):
    hp = str(tmp_path / "h.json")
    return AppState(Settings(engine=engine), str(tmp_path / "s.json"),
                    HistoryStore(hp))


def test_appstate_builds_engine_and_lock(tmp_path):
    st = _state(tmp_path)
    assert isinstance(st.engine, translate.GoogleEngine)
    assert isinstance(st.lock, type(threading.Lock()))


def test_appstate_rebuild_engine_after_change(tmp_path):
    st = _state(tmp_path)
    st.settings.engine = "bing"
    st.rebuild_engine()
    assert isinstance(st.engine, translate.BingEngine)


def test_appstate_save_persists(tmp_path):
    st = _state(tmp_path)
    st.settings.font_size = 30
    st.save()
    from overlay_translator.settings_store import load_settings
    assert load_settings(st.settings_path).font_size == 30
```

- [ ] **Step 9: Run to verify fail**

Run: `python -m pytest tests/test_state.py -v`
Expected: FAIL (`ModuleNotFoundError: ...web.state`).

- [ ] **Step 10: Implement `web/state.py`**

```python
import threading

import pytesseract

from .. import ocr, translate
from ..settings_store import save_settings


class AppState:
    """Shared app state used by the Flask server and the hotkey pipeline."""

    def __init__(self, settings, settings_path, history):
        self.settings = settings
        self.settings_path = settings_path
        self.history = history
        self.lock = threading.Lock()
        self.hotkey_manager = None
        self.window = None          # pywebview window, set by the host
        self.translate_now = None   # callable set by the host to run one cycle
        self.engine = translate.make_engine(settings.engine)
        self.tesseract_ok = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        ocr.configure_tesseract(None)
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def rebuild_engine(self) -> None:
        self.engine = translate.make_engine(self.settings.engine)

    def save(self) -> None:
        save_settings(self.settings, self.settings_path)
```

- [ ] **Step 11: Run tests**

Run: `python -m pytest tests/test_state.py tests/test_dpi.py -q`
Expected: PASS (6 passed).

- [ ] **Step 12: Commit**

```bash
git add requirements.txt src/overlay_translator/dpi.py src/overlay_translator/app.py tests/test_dpi.py src/overlay_translator/web/__init__.py src/overlay_translator/web/state.py tests/test_state.py
git commit -m "chore: web deps, move DPI helper, add AppState"
```

---

## Task 2: pipeline.run_cycle

**Files:**
- Create: `src/overlay_translator/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes `AppState` (`.engine`, `.settings`, `.history`, `.lock`), `arabic.shape_for_display`, `translate.to_arabic`/`TranslationError`.
- Produces `run_cycle(state, *, select_fn, overlay_fn, capture_fn=capture.grab, ocr_fn=ocr.extract_text, now_fn=...) -> None`:
  - `select_fn() -> Optional[Rect]`; `None` → return (no bubble).
  - grab+ocr in try; on exception → `overlay_fn(ERROR_MSG, rect, settings)`; empty text → `overlay_fn(NO_TEXT_MSG, rect, settings)`.
  - `to_arabic` in try; `TranslationError` → `overlay_fn(str(exc)[:200] or ERROR_MSG, rect, settings)`.
  - success → `overlay_fn(shape_for_display(ar), rect, settings)` then `state.history.add(en, ar, now_fn())` under `state.lock`.
- Constants `NO_TEXT_MSG = "No text found"`, `ERROR_MSG = "Translation failed — the engine may be rate-limited or offline. Try again, or switch engine in Settings."`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_pipeline.py`:
```python
from datetime import datetime
from overlay_translator import pipeline
from overlay_translator.models import Rect
from overlay_translator.settings_store import Settings
from overlay_translator.history_store import HistoryStore
from overlay_translator.web.state import AppState
from overlay_translator import translate


class _Eng:
    def __init__(self, out=None, exc=None):
        self._out, self._exc = out, exc
    def translate(self, text):
        if self._exc:
            raise self._exc
        return self._out


def _state(tmp_path, engine_obj):
    st = AppState(Settings(), str(tmp_path / "s.json"),
                  HistoryStore(str(tmp_path / "h.json")))
    st.engine = engine_obj
    return st


def _fixed_now():
    return "2026-07-11T10:00:00"


def test_none_selection_does_nothing(tmp_path):
    st = _state(tmp_path, _Eng(out="x"))
    shown = []
    pipeline.run_cycle(st, select_fn=lambda: None,
                       overlay_fn=lambda *a: shown.append(a),
                       capture_fn=lambda r: "img", ocr_fn=lambda i: "Hello",
                       now_fn=_fixed_now)
    assert shown == []
    assert st.history.entries() == []


def test_empty_ocr_shows_no_text(tmp_path):
    st = _state(tmp_path, _Eng(out="x"))
    shown = []
    pipeline.run_cycle(st, select_fn=lambda: Rect(0, 0, 10, 10),
                       overlay_fn=lambda text, rect, settings: shown.append(text),
                       capture_fn=lambda r: "img", ocr_fn=lambda i: "  ",
                       now_fn=_fixed_now)
    assert shown == [pipeline.NO_TEXT_MSG]
    assert st.history.entries() == []


def test_translation_error_shows_message(tmp_path):
    st = _state(tmp_path, _Eng(exc=translate.TranslationError("429 boom")))
    shown = []
    pipeline.run_cycle(st, select_fn=lambda: Rect(0, 0, 10, 10),
                       overlay_fn=lambda text, rect, settings: shown.append(text),
                       capture_fn=lambda r: "img", ocr_fn=lambda i: "Hello",
                       now_fn=_fixed_now)
    assert "429 boom" in shown[0]
    assert st.history.entries() == []


def test_success_shows_bubble_and_records_history(tmp_path):
    st = _state(tmp_path, _Eng(out="مرحبا"))
    shown = []
    pipeline.run_cycle(st, select_fn=lambda: Rect(0, 0, 10, 10),
                       overlay_fn=lambda text, rect, settings: shown.append(text),
                       capture_fn=lambda r: "img", ocr_fn=lambda i: "Hello",
                       now_fn=_fixed_now)
    assert shown == ["مرحبا"]              # shape_for_display is passthrough
    e = st.history.entries()[0]
    assert (e.source, e.translation, e.timestamp) == ("Hello", "مرحبا", "2026-07-11T10:00:00")
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: FAIL (`ModuleNotFoundError: ...pipeline`).

- [ ] **Step 3: Implement `pipeline.py`**

```python
from datetime import datetime

from . import capture, ocr, arabic, translate

NO_TEXT_MSG = "No text found"
ERROR_MSG = ("Translation failed — the engine may be rate-limited or offline. "
             "Try again, or switch engine in Settings.")


def _now():
    return datetime.now().isoformat(timespec="seconds")


def run_cycle(state, *, select_fn, overlay_fn,
              capture_fn=capture.grab, ocr_fn=ocr.extract_text, now_fn=_now):
    """Run one select -> capture -> OCR -> translate -> overlay -> history cycle.

    All external effects are injected (select_fn, overlay_fn, capture_fn,
    ocr_fn, now_fn) so this is fully unit-testable without a screen or network.
    """
    rect = select_fn()
    if rect is None:
        return
    try:
        image = capture_fn(rect)
        english = ocr_fn(image)
    except Exception:
        overlay_fn(ERROR_MSG, rect, state.settings)
        return
    if not english:
        overlay_fn(NO_TEXT_MSG, rect, state.settings)
        return
    try:
        ar = translate.to_arabic(english, state.engine)
    except translate.TranslationError as exc:
        overlay_fn(str(exc)[:200] or ERROR_MSG, rect, state.settings)
        return
    overlay_fn(arabic.shape_for_display(ar), rect, state.settings)
    with state.lock:
        state.history.add(english, ar, now_fn())
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/overlay_translator/pipeline.py tests/test_pipeline.py
git commit -m "feat: add injectable translation pipeline.run_cycle"
```

---

## Task 3: Subprocess entries (selector + overlay)

**Files:**
- Modify: `src/overlay_translator/overlay.py` (add `on_close`)
- Create: `src/overlay_translator/proc_select.py`
- Create: `src/overlay_translator/proc_overlay.py`

**Interfaces:**
- `overlay.show(text, rect, settings, parent, on_close=None)` — calls `on_close()` when the bubble is dismissed/auto-hidden (in addition to destroying the window).
- `proc_select` (run as `python -m overlay_translator.proc_select`): prints one line of JSON to stdout — `{"x":..,"y":..,"width":..,"height":..}` or `null`.
- `proc_overlay` (run as `python -m overlay_translator.proc_overlay '<json>'`) where json is `{"text":str,"x":int,"y":int,"width":int,"height":int,"font_size":int,"auto_hide_seconds":int}`; shows the bubble until dismissed/auto-hidden, then exits.

- [ ] **Step 1: Add `on_close` to `overlay.show`**

In `src/overlay_translator/overlay.py`, change the signature and the `dismiss` function. The full file becomes:
```python
import tkinter as tk
from .models import Rect

MARGIN = 8
BUBBLE_BG = "#1e1e1e"
BUBBLE_FG = "#ffffff"
BORDER = "#4a4a4a"


def show(text: str, rect: Rect, settings, parent, on_close=None) -> None:
    """Show a dismissible Arabic bubble just above the selected region."""
    win = tk.Toplevel(parent)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=BORDER)

    label = tk.Label(
        win, text=text, justify="right", anchor="e",
        bg=BUBBLE_BG, fg=BUBBLE_FG, font=("Segoe UI", settings.font_size),
        wraplength=max(rect.width, 300), padx=12, pady=8,
    )
    label.pack(padx=1, pady=1)

    win.update_idletasks()
    bh = win.winfo_reqheight()
    x = rect.x
    y = rect.y - bh - MARGIN
    if y < 0:
        y = rect.y + rect.height + MARGIN
    win.geometry(f"+{x}+{y}")

    def dismiss(_event=None):
        if win.winfo_exists():
            win.destroy()
        if on_close is not None:
            on_close()

    win.bind("<Escape>", dismiss)
    win.bind("<Button-1>", dismiss)
    label.bind("<Button-1>", dismiss)
    win.focus_force()

    seconds = settings.auto_hide_seconds
    if seconds and seconds > 0:
        win.after(int(seconds * 1000), dismiss)
```

- [ ] **Step 2: Implement `proc_select.py`**

```python
"""Subprocess entry: show the region selector, print the Rect as JSON."""
import json
import sys
import tkinter as tk

from .dpi import enable_dpi_awareness
from . import selector


def main() -> None:
    enable_dpi_awareness()
    root = tk.Tk()
    root.withdraw()
    rect = selector.select_region(root)
    root.destroy()
    if rect is None:
        sys.stdout.write("null")
    else:
        sys.stdout.write(json.dumps(
            {"x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height}
        ))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Implement `proc_overlay.py`**

```python
"""Subprocess entry: show the Arabic bubble from a JSON argument."""
import json
import sys
import tkinter as tk

from .dpi import enable_dpi_awareness
from .models import Rect
from .settings_store import Settings
from . import overlay


def main(argv) -> None:
    enable_dpi_awareness()
    data = json.loads(argv[1])
    rect = Rect(x=data["x"], y=data["y"],
                width=data["width"], height=data["height"])
    settings = Settings(font_size=data.get("font_size", 18),
                        auto_hide_seconds=data.get("auto_hide_seconds", 5))
    root = tk.Tk()
    root.withdraw()
    overlay.show(data["text"], rect, settings, root, on_close=root.quit)
    root.mainloop()
    root.destroy()


if __name__ == "__main__":
    main(sys.argv)
```

- [ ] **Step 4: Manual smoke — selector subprocess**

Run: `python -m overlay_translator.proc_select`
Expected: dim fullscreen overlay covering the WHOLE screen; drag a box → prints e.g. `{"x":100,"y":200,"width":300,"height":80}`; Esc or a tiny click prints `null`. (Run with `$env:PYTHONPATH="src"` in PowerShell, or after `pip install -e` — for this repo use `set PYTHONPATH=src` / PowerShell `$env:PYTHONPATH="src"`.)

- [ ] **Step 5: Manual smoke — overlay subprocess**

Run (PowerShell `$env:PYTHONPATH="src"`):
`python -m overlay_translator.proc_overlay '{\"text\":\"مرحبا بالعالم\",\"x\":400,\"y\":400,\"width\":300,\"height\":60,\"font_size\":20,\"auto_hide_seconds\":3}'`
Expected: a dark bubble with correctly-rendered Arabic appears above y=400 and auto-closes after ~3s (or on click/Esc); the process then exits.

- [ ] **Step 6: Commit**

```bash
git add src/overlay_translator/overlay.py src/overlay_translator/proc_select.py src/overlay_translator/proc_overlay.py
git commit -m "feat: subprocess entries for selector and overlay (+ overlay on_close)"
```

---

## Task 4: Flask app — GET routes, templates, static

**Files:**
- Create: `src/overlay_translator/web/server.py`
- Create: `src/overlay_translator/templates/{shell,home,history,settings}.html`
- Create: `src/overlay_translator/static/app.css`
- Create: `src/overlay_translator/static/htmx.min.js`
- Test: `tests/test_server_get.py`

**Interfaces:**
- Consumes `AppState`.
- Produces `server.create_app(state) -> flask.Flask` with GET routes `/`, `/home`, `/history`, `/settings` returning HTML; templates resolve from the package `templates/`, static from `static/`.

- [ ] **Step 1: Vendor HTMX**

Run: `python -c "import urllib.request; urllib.request.urlretrieve('https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js', 'src/overlay_translator/static/htmx.min.js')"`
Then verify it is non-empty: `python -c "import os; print(os.path.getsize('src/overlay_translator/static/htmx.min.js'))"` → prints a number > 20000.

- [ ] **Step 2: Write failing tests**

Create `tests/test_server_get.py`:
```python
from overlay_translator.settings_store import Settings
from overlay_translator.history_store import HistoryStore
from overlay_translator.web.state import AppState
from overlay_translator.web.server import create_app


def _client(tmp_path, **skw):
    st = AppState(Settings(**skw), str(tmp_path / "s.json"),
                  HistoryStore(str(tmp_path / "h.json")))
    return create_app(st), st


def test_shell_has_theme_and_htmx(tmp_path):
    app, st = _client(tmp_path, theme="dark")
    body = app.test_client().get("/").get_data(as_text=True)
    assert 'data-theme="dark"' in body
    assert "htmx.min.js" in body


def test_home_shows_hotkey_and_engine(tmp_path):
    app, st = _client(tmp_path, hotkey="alt+q", engine="bing")
    body = app.test_client().get("/home").get_data(as_text=True)
    assert "alt+q" in body
    assert "bing" in body


def test_history_lists_entries(tmp_path):
    app, st = _client(tmp_path)
    st.history.add("Hello", "مرحبا", "2026-07-11T10:00:00")
    body = app.test_client().get("/history").get_data(as_text=True)
    assert "Hello" in body
    assert "مرحبا" in body


def test_history_empty_message(tmp_path):
    app, st = _client(tmp_path)
    body = app.test_client().get("/history").get_data(as_text=True)
    assert "No translations yet" in body


def test_settings_shows_current_values(tmp_path):
    app, st = _client(tmp_path, engine="deepl", font_size=22)
    body = app.test_client().get("/settings").get_data(as_text=True)
    assert "deepl" in body
    assert "22" in body
```

- [ ] **Step 3: Run to verify fail**

Run: `python -m pytest tests/test_server_get.py -v`
Expected: FAIL (`ModuleNotFoundError: ...web.server`).

- [ ] **Step 4: Implement `web/server.py`** (GET routes; POST routes added in Task 5)

```python
import os

from flask import Flask, render_template

_PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATES = os.path.join(_PKG, "templates")
_STATIC = os.path.join(_PKG, "static")


def create_app(state):
    app = Flask(__name__, template_folder=_TEMPLATES, static_folder=_STATIC)
    app.config["STATE"] = state

    @app.get("/")
    def index():
        return render_template("shell.html", s=state.settings)

    @app.get("/home")
    def home():
        return render_template("home.html", s=state.settings,
                               tesseract_ok=state.tesseract_ok)

    @app.get("/history")
    def history():
        with state.lock:
            entries = state.history.entries()
        return render_template("history.html", entries=entries)

    @app.get("/settings")
    def settings():
        return render_template("settings.html", s=state.settings)

    return app
```

- [ ] **Step 5: Create `templates/shell.html`**

```html
<!doctype html>
<html lang="en" data-theme="{{ s.theme }}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OverlayTranslator</title>
  <link rel="stylesheet" href="/static/app.css">
  <script src="/static/htmx.min.js"></script>
</head>
<body>
  <div class="app">
    <nav class="nav">
      <div class="brand">Overlay<span>Translator</span></div>
      <a class="nav-item active" hx-get="/home" hx-target="#panel" hx-on:click="setActive(this)">Home</a>
      <a class="nav-item" hx-get="/history" hx-target="#panel" hx-on:click="setActive(this)">History</a>
      <a class="nav-item" hx-get="/settings" hx-target="#panel" hx-on:click="setActive(this)">Settings</a>
    </nav>
    <main id="panel" hx-get="/home" hx-trigger="load"></main>
  </div>
  <script>
    function setActive(el){
      document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
      el.classList.add('active');
    }
  </script>
</body>
</html>
```

- [ ] **Step 6: Create `templates/home.html`**

```html
<section class="panel-in">
  <div class="card status-card">
    <div class="status-title">Ready</div>
    <div class="status-sub">Press <kbd>{{ s.hotkey }}</kbd> and drag over English text</div>
    <div class="chips">
      <span class="chip">engine: {{ s.engine }}</span>
      <span class="chip">hotkey: {{ s.hotkey }}</span>
    </div>
    <button class="btn btn-accent" hx-post="/translate" hx-target="#panel" hx-swap="innerHTML">Translate now</button>
  </div>
  {% if not tesseract_ok %}
  <div class="card warn">⚠ Tesseract not found — install it (<code>winget install UB-Mannheim.TesseractOCR</code>) and restart.</div>
  {% endif %}
</section>
```

- [ ] **Step 7: Create `templates/history.html`**

```html
<section class="panel-in" hx-get="/history" hx-trigger="every 2s" hx-target="#panel" hx-swap="innerHTML">
  <div class="row-between">
    <h2>History</h2>
    <button class="btn btn-ghost" hx-post="/history/clear" hx-target="#panel">Clear all</button>
  </div>
  {% if not entries %}
    <div class="card muted-card">No translations yet.</div>
  {% else %}
    {% for e in entries %}
    <div class="card hist">
      <div class="hist-src">{{ e.source }}</div>
      <div class="hist-ar" dir="rtl">{{ e.translation }}</div>
      <div class="hist-foot">
        <span class="ts">{{ e.timestamp }}</span>
        <span class="hist-actions">
          <button class="btn btn-sm" hx-post="/history/copy/{{ loop.index0 }}" hx-swap="none">Copy</button>
          <button class="btn btn-sm btn-danger" hx-post="/history/delete/{{ loop.index0 }}" hx-target="#panel">Delete</button>
        </span>
      </div>
    </div>
    {% endfor %}
  {% endif %}
</section>
```

- [ ] **Step 8: Create `templates/settings.html`**

```html
<section class="panel-in">
  <h2>Settings</h2>

  <div class="card">
    <label class="lbl">Hotkey</label>
    <div class="row">
      <kbd>{{ s.hotkey }}</kbd>
      <button class="btn" hx-post="/settings/hotkey/record" hx-target="#panel">Record shortcut</button>
    </div>
  </div>

  <div class="card">
    <label class="lbl">Engine</label>
    <div class="seg">
      {% for eng in ["google", "bing", "deepl"] %}
      <button class="seg-item {{ 'on' if s.engine == eng else '' }}"
              hx-post="/settings/engine" hx-vals='{"engine": "{{ eng }}"}' hx-target="#panel">{{ eng }}</button>
      {% endfor %}
    </div>
    <div class="hint">Google/Bing: keyless & reliable. DeepL: best quality but can be rate-limited.</div>
  </div>

  <div class="card">
    <label class="lbl">Auto-hide: {{ 'Off' if s.auto_hide_seconds == 0 else s.auto_hide_seconds ~ ' s' }}</label>
    <input type="range" min="2" max="15" value="{{ s.auto_hide_seconds or 5 }}"
           hx-post="/settings/autohide" hx-trigger="change" name="seconds" hx-target="#panel">
    <label class="check">
      <input type="checkbox" {{ 'checked' if s.auto_hide_seconds == 0 else '' }}
             hx-post="/settings/autohide" hx-vals='{"seconds": "0"}' hx-trigger="change[target.checked]" hx-target="#panel">
      Off (stay until dismissed)
    </label>
  </div>

  <div class="card">
    <label class="lbl">Bubble font size: {{ s.font_size }}</label>
    <input type="range" min="12" max="36" value="{{ s.font_size }}"
           hx-post="/settings/font" hx-trigger="change" name="size" hx-target="#panel">
  </div>

  <div class="card">
    <label class="lbl">Theme</label>
    <div class="seg">
      <button class="seg-item {{ 'on' if s.theme == 'light' else '' }}"
              hx-post="/settings/theme" hx-vals='{"theme": "light"}' hx-target="#panel">light</button>
      <button class="seg-item {{ 'on' if s.theme == 'dark' else '' }}"
              hx-post="/settings/theme" hx-vals='{"theme": "dark"}' hx-target="#panel">dark</button>
    </div>
  </div>
</section>
```

- [ ] **Step 9: Create `static/app.css`** (creamy-beige design system)

```css
:root{
  --bg:#f4ecdf; --surface:#faf6ee; --border:#e7dac6;
  --text:#3b332a; --muted:#8a7d6b; --accent:#c06a4d; --accent-ink:#fff;
  --danger:#a6432f; --radius:14px; --shadow:0 6px 20px rgba(80,60,40,.08);
}
:root[data-theme="dark"]{
  --bg:#221c17; --surface:#2c2721; --border:#3d362e;
  --text:#efe6d8; --muted:#a89b86; --accent:#c06a4d; --accent-ink:#fff;
  --danger:#e0765c; --shadow:0 6px 20px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:ui-sans-serif,"Segoe UI",system-ui,sans-serif;font-size:14px}
.app{display:flex;min-height:100vh}
.nav{width:150px;flex-shrink:0;background:var(--surface);
  border-right:1px solid var(--border);padding:16px 10px;display:flex;flex-direction:column;gap:4px}
.brand{font-weight:700;font-size:15px;margin:4px 8px 14px}
.brand span{color:var(--accent)}
.nav-item{padding:9px 12px;border-radius:10px;cursor:pointer;color:var(--muted);
  transition:background .15s,color .15s;user-select:none}
.nav-item:hover{background:var(--bg)}
.nav-item.active{background:var(--accent);color:var(--accent-ink)}
#panel{flex:1;padding:22px;overflow:auto}
.panel-in{display:flex;flex-direction:column;gap:14px;max-width:520px}
.card{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:16px;box-shadow:var(--shadow)}
h2{margin:2px 0 6px;font-size:18px}
.status-card{text-align:center;padding:26px}
.status-title{font-size:22px;font-weight:700}
.status-sub{color:var(--muted);margin:6px 0 14px}
.chips{display:flex;gap:8px;justify-content:center;margin-bottom:16px;flex-wrap:wrap}
.chip{background:var(--bg);border:1px solid var(--border);border-radius:999px;padding:4px 12px;color:var(--muted);font-size:12px}
kbd{background:var(--bg);border:1px solid var(--border);border-bottom-width:2px;
  border-radius:6px;padding:2px 8px;font-family:ui-monospace,monospace;font-size:12px}
.btn{background:var(--bg);color:var(--text);border:1px solid var(--border);
  border-radius:10px;padding:9px 14px;cursor:pointer;font-size:13px;transition:filter .15s,background .15s}
.btn:hover{filter:brightness(.97)}
.btn-accent{background:var(--accent);color:var(--accent-ink);border-color:transparent;font-weight:600;padding:11px 20px}
.btn-ghost{background:transparent}
.btn-sm{padding:5px 10px;font-size:12px}
.btn-danger{color:var(--danger);border-color:var(--border)}
.warn{border-color:var(--accent);color:var(--text)}
.muted-card{color:var(--muted);text-align:center}
.row{display:flex;align-items:center;gap:12px}
.row-between{display:flex;align-items:center;justify-content:space-between}
.lbl{display:block;font-weight:600;margin-bottom:10px}
.hint{color:var(--muted);font-size:12px;margin-top:8px}
.seg{display:inline-flex;background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:3px;gap:3px}
.seg-item{border:0;background:transparent;color:var(--muted);padding:6px 14px;border-radius:8px;cursor:pointer;font-size:13px}
.seg-item.on{background:var(--accent);color:var(--accent-ink)}
input[type=range]{width:100%;accent-color:var(--accent)}
.check{display:flex;align-items:center;gap:8px;margin-top:10px;color:var(--muted)}
.hist .hist-src{color:var(--muted);font-size:13px}
.hist .hist-ar{font-size:18px;margin:4px 0 8px;text-align:right}
.hist-foot{display:flex;align-items:center;justify-content:space-between}
.ts{color:var(--muted);font-size:11px}
.hist-actions{display:flex;gap:6px}
```

- [ ] **Step 10: Run tests**

Run: `python -m pytest tests/test_server_get.py -v`
Expected: PASS (5 passed).

- [ ] **Step 11: Commit**

```bash
git add src/overlay_translator/web/server.py src/overlay_translator/templates src/overlay_translator/static tests/test_server_get.py
git commit -m "feat: Flask GET routes, HTMX templates, creamy-beige CSS"
```

---

## Task 5: Flask POST action routes

**Files:**
- Modify: `src/overlay_translator/web/server.py` (add POST routes)
- Test: `tests/test_server_post.py`

**Interfaces:**
- Consumes `AppState` (`.settings`, `.history`, `.lock`, `.save`, `.rebuild_engine`, `.hotkey_manager`, `.translate_now`), `pyperclip`.
- Adds POSTs: `/translate`, `/settings/engine`, `/settings/autohide`, `/settings/font`, `/settings/theme`, `/settings/hotkey/record`, `/history/delete/<int:i>`, `/history/clear`, `/history/copy/<int:i>`.
- `/translate` calls `state.translate_now()` if set (the host wires it to the real pipeline); returns the Home fragment. Injectable/stubbable in tests by setting `state.translate_now`.
- Clipboard is accessed through `server._clipboard_copy` (module-level, monkeypatchable) rather than importing pyperclip at call sites, so tests don't touch the real clipboard.

- [ ] **Step 1: Write failing tests**

Create `tests/test_server_post.py`:
```python
from overlay_translator.settings_store import Settings, load_settings
from overlay_translator.history_store import HistoryStore
from overlay_translator.web.state import AppState
from overlay_translator.web import server as server_mod
from overlay_translator.web.server import create_app
from overlay_translator import translate


def _ctx(tmp_path, **skw):
    st = AppState(Settings(**skw), str(tmp_path / "s.json"),
                  HistoryStore(str(tmp_path / "h.json")))
    return create_app(st).test_client(), st


def test_set_engine_updates_and_persists(tmp_path):
    c, st = _ctx(tmp_path, engine="google")
    body = c.post("/settings/engine", data={"engine": "bing"}).get_data(as_text=True)
    assert st.settings.engine == "bing"
    assert isinstance(st.engine, translate.BingEngine)
    assert load_settings(st.settings_path).engine == "bing"
    assert "bing" in body


def test_set_autohide_off(tmp_path):
    c, st = _ctx(tmp_path)
    c.post("/settings/autohide", data={"seconds": "0"})
    assert st.settings.auto_hide_seconds == 0


def test_set_font(tmp_path):
    c, st = _ctx(tmp_path)
    c.post("/settings/font", data={"size": "28"})
    assert st.settings.font_size == 28


def test_set_theme(tmp_path):
    c, st = _ctx(tmp_path, theme="light")
    body = c.post("/settings/theme", data={"theme": "dark"}).get_data(as_text=True)
    assert st.settings.theme == "dark"
    # out-of-band swap flips the <html> theme
    assert 'data-theme="dark"' in body


def test_delete_and_clear_history(tmp_path):
    c, st = _ctx(tmp_path)
    st.history.add("a", "A", "t"); st.history.add("b", "B", "t")
    c.post("/history/delete/0")
    assert [e.source for e in st.history.entries()] == ["a"]
    c.post("/history/clear")
    assert st.history.entries() == []


def test_copy_uses_clipboard(tmp_path, monkeypatch):
    c, st = _ctx(tmp_path)
    st.history.add("a", "مرحبا", "t")
    copied = {}
    monkeypatch.setattr(server_mod, "_clipboard_copy", lambda text: copied.setdefault("v", text))
    c.post("/history/copy/0")
    assert copied["v"] == "مرحبا"


def test_translate_invokes_host_hook(tmp_path):
    c, st = _ctx(tmp_path)
    called = {"n": 0}
    st.translate_now = lambda: called.__setitem__("n", called["n"] + 1)
    c.post("/translate")
    assert called["n"] == 1
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_server_post.py -v`
Expected: FAIL (POST routes 405/404).

- [ ] **Step 3: Add POST routes + clipboard hook to `web/server.py`**

Add near the top (module level):
```python
def _clipboard_copy(text):
    import pyperclip
    pyperclip.copy(text)
```
Insert these routes inside `create_app`, before `return app`:
```python
    from flask import request, render_template

    def _home_fragment():
        return render_template("home.html", s=state.settings,
                               tesseract_ok=state.tesseract_ok)

    def _settings_fragment():
        return render_template("settings.html", s=state.settings)

    def _history_fragment():
        with state.lock:
            entries = state.history.entries()
        return render_template("history.html", entries=entries)

    @app.post("/translate")
    def translate_now():
        if state.translate_now is not None:
            state.translate_now()
        return _home_fragment()

    @app.post("/settings/engine")
    def set_engine():
        state.settings.engine = request.form["engine"]
        state.rebuild_engine()
        state.save()
        return _settings_fragment()

    @app.post("/settings/autohide")
    def set_autohide():
        state.settings.auto_hide_seconds = int(request.form["seconds"])
        state.save()
        return _settings_fragment()

    @app.post("/settings/font")
    def set_font():
        state.settings.font_size = int(request.form["size"])
        state.save()
        return _settings_fragment()

    @app.post("/settings/theme")
    def set_theme():
        state.settings.theme = request.form["theme"]
        state.save()
        # out-of-band: flip the <html data-theme> live, plus the settings panel
        oob = f'<html lang="en" data-theme="{state.settings.theme}" hx-swap-oob="true"></html>'
        return _settings_fragment() + oob

    @app.post("/settings/hotkey/record")
    def record_hotkey():
        import keyboard
        combo = keyboard.read_hotkey(suppress=False)
        state.settings.hotkey = combo
        if state.hotkey_manager is not None:
            state.hotkey_manager.register(combo)
        state.save()
        return _settings_fragment()

    @app.post("/history/delete/<int:i>")
    def delete_history(i):
        with state.lock:
            state.history.delete(i)
        return _history_fragment()

    @app.post("/history/clear")
    def clear_history():
        with state.lock:
            state.history.clear()
        return _history_fragment()

    @app.post("/history/copy/<int:i>")
    def copy_history(i):
        with state.lock:
            entries = state.history.entries()
        if 0 <= i < len(entries):
            _clipboard_copy(entries[i].translation)
        return ("", 204)
```
Note: the `hx-swap-oob` on `<html>` requires HTMX to process out-of-band swaps; HTMX matches the tag by attribute. Keeping the panel as the primary target and the `<html>` as OOB flips the theme without a full reload.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_server_post.py -v`
Expected: PASS (7 passed).

- [ ] **Step 5: Full suite**

Run: `python -m pytest -q`
Expected: PASS (all green).

- [ ] **Step 6: Commit**

```bash
git add src/overlay_translator/web/server.py tests/test_server_post.py
git commit -m "feat: Flask POST routes (settings, history, translate, copy)"
```

---

## Task 6: Host — webapp.py (pywebview + threads), rewire app.py, delete ui/

**Files:**
- Create: `src/overlay_translator/webapp.py`
- Rewrite: `src/overlay_translator/app.py`
- Modify: `src/overlay_translator/tray.py` (callbacks operate on a pywebview window via the queue-free direct approach below)
- Delete: `src/overlay_translator/ui/` (whole package)

**Interfaces:**
- `webapp.run() -> None` — builds `Settings`+`HistoryStore`+`AppState`, starts Flask on a free port (daemon thread), registers the global hotkey (daemon), starts the tray (daemon), wires `state.translate_now` and the hotkey to `pipeline.run_cycle` with subprocess spawn functions, creates the pywebview window pointed at the Flask URL, and runs `webview.start()`.
- `app.run = webapp.run` (so `main.py`'s `from overlay_translator.app import run` keeps working).

- [ ] **Step 1: Rewrite `tray.py` to accept show/quit callbacks**

Replace `src/overlay_translator/tray.py` with:
```python
import pystray
from PIL import Image, ImageDraw


def _make_image() -> Image.Image:
    img = Image.new("RGB", (64, 64), "#c06a4d")
    d = ImageDraw.Draw(img)
    d.rectangle((6, 6, 58, 58), outline="white", width=3)
    d.text((24, 20), "A", fill="white")
    return img


def build_icon(on_show, on_quit) -> "pystray.Icon":
    """Tray icon whose menu calls on_show()/on_quit()."""
    menu = pystray.Menu(
        pystray.MenuItem("Show", lambda icon, item: on_show(), default=True),
        pystray.MenuItem("Quit", lambda icon, item: (on_quit(), icon.stop())),
    )
    return pystray.Icon("OverlayTranslator", _make_image(),
                        "OverlayTranslator", menu)
```

- [ ] **Step 2: Implement `webapp.py`**

```python
import json
import os
import socket
import subprocess
import sys
import threading

import webview

from .settings_store import load_settings
from .history_store import HistoryStore
from .web.state import AppState
from .web.server import create_app
from . import pipeline, tray
from .hotkey import HotkeyManager
from .models import Rect

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SETTINGS_PATH = os.path.join(_ROOT, "settings.json")
HISTORY_PATH = os.path.join(_ROOT, "history.json")

# Hide the console window of spawned subprocesses on Windows.
_NO_WINDOW = 0x08000000  # subprocess.CREATE_NO_WINDOW


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _spawn_select():
    """Run the selector subprocess; return a Rect or None."""
    out = subprocess.run(
        [sys.executable, "-m", "overlay_translator.proc_select"],
        capture_output=True, text=True, creationflags=_NO_WINDOW,
        env={**os.environ, "PYTHONPATH": os.path.join(_ROOT, "src")},
    ).stdout.strip()
    if not out or out == "null":
        return None
    d = json.loads(out)
    return Rect(x=d["x"], y=d["y"], width=d["width"], height=d["height"])


def _spawn_overlay(text, rect, settings):
    payload = json.dumps({
        "text": text, "x": rect.x, "y": rect.y,
        "width": rect.width, "height": rect.height,
        "font_size": settings.font_size,
        "auto_hide_seconds": settings.auto_hide_seconds,
    })
    subprocess.Popen(
        [sys.executable, "-m", "overlay_translator.proc_overlay", payload],
        creationflags=_NO_WINDOW,
        env={**os.environ, "PYTHONPATH": os.path.join(_ROOT, "src")},
    )


def run() -> None:
    settings = load_settings(SETTINGS_PATH)
    history = HistoryStore(HISTORY_PATH)
    state = AppState(settings, SETTINGS_PATH, history)

    def do_cycle():
        pipeline.run_cycle(state, select_fn=_spawn_select, overlay_fn=_spawn_overlay)

    state.translate_now = do_cycle
    state.hotkey_manager = HotkeyManager(lambda: threading.Thread(
        target=do_cycle, daemon=True).start())
    state.hotkey_manager.register(settings.hotkey)

    port = _free_port()
    app = create_app(state)
    threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port,
                               threaded=True, use_reloader=False),
        daemon=True).start()

    def on_show():
        if state.window is not None:
            state.window.show()

    def on_quit():
        os._exit(0)

    icon = tray.build_icon(on_show, on_quit)
    threading.Thread(target=icon.run, daemon=True).start()

    state.window = webview.create_window(
        "OverlayTranslator", url=f"http://127.0.0.1:{port}/",
        width=620, height=580)

    def on_closing():
        # hide to tray instead of quitting
        state.window.hide()
        return False

    state.window.events.closing += on_closing
    webview.start()
```

- [ ] **Step 3: Rewrite `app.py`**

```python
from .webapp import run  # noqa: F401
from .dpi import enable_dpi_awareness  # noqa: F401  (kept for tests/imports)
```

- [ ] **Step 4: Delete the old CustomTkinter UI package**

```bash
git rm -r src/overlay_translator/ui
```

- [ ] **Step 5: Import sanity (no tkinter/customtkinter in the main process import path)**

Run: `PYTHONPATH=src python -c "from overlay_translator import webapp, app; from overlay_translator.web.server import create_app; print('imports ok')"`
Expected: `imports ok` (no ModuleNotFoundError for customtkinter, since the main process no longer imports it).

- [ ] **Step 6: Full test suite**

Run: `python -m pytest -q`
Expected: PASS (all green — no test imports `ui/`).

- [ ] **Step 7: Live end-to-end (human)**

1. `python main.py` — a native window opens showing the creamy-beige UI (Home tab). A tray icon appears.
2. Toggle **Settings → theme → dark**: the window switches to warm espresso instantly.
3. Press **Alt+Q**: the dim selector covers the FULL screen; drag over English text → an Arabic bubble appears and auto-hides; open **History** → the row is there (it appears within ~2s via live refresh).
4. **Settings → Record shortcut** → press a new combo → hotkey updates; test it.
5. Switch engine to **bing**, translate again.
6. Close the window → it hides to tray; tray **Show** reopens it; tray **Quit** exits.

- [ ] **Step 8: Commit**

```bash
git add src/overlay_translator/webapp.py src/overlay_translator/app.py src/overlay_translator/tray.py
git commit -m "feat: pywebview host + tray/hotkey wiring; remove CustomTkinter UI"
```

---

## Task 7: README + launcher dependency check

**Files:**
- Modify: `README.md`
- Modify: `run_overlay_translator.bat`

- [ ] **Step 1: Update the launcher's dependency-check import line**

In `run_overlay_translator.bat`, change the check line to match the new deps:
```
python -c "import flask, webview, pyperclip, pystray, deep_translator, translators, requests, mss, keyboard, pytesseract, PIL" >nul 2>nul
```

- [ ] **Step 2: Update `README.md`** (replace the "## The app" section body)

Replace the app-description bullet block with:
```markdown
## The app

A native window (creamy-beige light / warm espresso dark) with three sections:

- **Home** — status, current hotkey/engine, and a "Translate now" button.
- **History** — past translations (source → Arabic + time); copy, delete, clear; updates live.
- **Settings** — record a new hotkey, auto-hide timer, engine (Google/Bing/DeepL),
  bubble font size, and light/dark theme.

The UI is built with HTMX + Flask rendered in a pywebview window. The app lives in
the system tray: closing the window hides it there; the hotkey keeps working;
**Quit** from the tray menu exits.
```

- [ ] **Step 3: Commit**

```bash
git add README.md run_overlay_translator.bat
git commit -m "docs: README + launcher for the HTMX/pywebview UI"
```

---

## Self-Review Notes

- **Spec coverage:** pywebview host (T6), Flask+HTMX GET (T4) + POST (T5), creamy-beige+espresso CSS/theme toggle (T4/T5), subprocess selector/overlay with DPI (T3), pipeline reuse (T2), AppState+lock (T1), tray Show/Quit + hide-to-tray (T6), record hotkey (T5), live history refresh via 2s poll (T4), clipboard copy via pyperclip hook (T5), offline vendored HTMX+CSS (T4), deps add/remove (T1/T6/T7), README (T7). All spec sections mapped.
- **Placeholders:** none — routes, templates, CSS, and subprocess entries are complete.
- **Type consistency:** `AppState` attributes (`settings`, `history`, `lock`, `engine`, `tesseract_ok`, `hotkey_manager`, `window`, `translate_now`, `rebuild_engine`, `save`) used identically across T1/T2/T5/T6; `pipeline.run_cycle(state, *, select_fn, overlay_fn, capture_fn, ocr_fn, now_fn)` consistent T2→T6; `overlay.show(..., on_close=None)` consistent T3→(proc_overlay); `tray.build_icon(on_show, on_quit)` consistent T6; `create_app(state)` consistent T4/T5/T6; subprocess module names `overlay_translator.proc_select`/`proc_overlay` consistent T3/T6; `_clipboard_copy` monkeypatch seam consistent T5.
- **Carried risk:** pywebview `events.closing` cancel-to-hide and cross-thread `window.show()` are verified in Task 6's manual E2E (they can't be unit-tested). If `closing` cancellation isn't supported on the installed backend, fall back to hiding on the tray's control and letting X quit — noted for the implementer to confirm during T6.
```
