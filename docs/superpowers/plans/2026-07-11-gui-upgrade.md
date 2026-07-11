# OverlayTranslator GUI Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the console app into a tray-resident CustomTkinter app with Home/History/Settings tabs, a rebindable hotkey, a configurable auto-hide bubble timer, persistent translation history, and a choice of three keyless engines (Google/DeepL/Bing).

**Architecture:** Keep the existing OCR→translate→overlay pipeline. Add a UI layer: pure persistence stores (`settings_store`, `history_store`) that are unit-tested, a keyless multi-engine `translate` module, and CustomTkinter UI + `pystray` tray. The `CTk` window owns the main-thread event loop; the keyboard-hotkey thread and tray thread only push tuples onto a `queue.Queue` that the window drains via `after(50, poll)`. Selector/overlay become `Toplevel` children of the one root (no second `Tk()`), preserving main-thread-only tkinter.

**Tech Stack:** Python 3.11, `customtkinter`, `pystray`, `Pillow`, `translators`, `deep-translator`, `mss`, `pytesseract` (+Tesseract), `keyboard`, `arabic-reshaper`, `python-bidi`, `pytest`.

## Global Constraints

- Python **3.11**; run pip as `python -m pip`, tests as `python -m pytest` from repo root (`pytest.ini` sets `pythonpath = src`).
- Target OS **Windows 11**. Package root `src/overlay_translator/`.
- Translation is **English → Arabic only** (`from_language="en"`/`source_lang="EN"`, `to_language="ar"`/`target_lang="AR"`); no language pickers.
- **All engines are keyless** (no API keys). Engine keys: `"google"` (deep-translator), `"deepl"` (translators, may 429), `"bing"` (translators). Default `"google"`.
- `settings.json` and `history.json` live in the **repo root** (next to `main.py`). History capped at **200** entries, newest-first. Append to history only on **successful** translation.
- `auto_hide_seconds`: `0` = off (stay until dismissed); otherwise the bubble self-dismisses after that many seconds. Esc/click always dismiss early.
- Corrupt/partial JSON must degrade to defaults/empty and log to console — never crash.
- **All tkinter objects live under one `CTk` root on the main thread.** Selector/overlay are `Toplevel(parent)`. Background threads (keyboard, tray) only enqueue tuples; they never touch tkinter.
- Request-queue protocol (tuples): `("translate",)`, `("show",)`, `("quit",)`, `("hotkey_recorded", combo_str)`.

---

## File Structure

```
S:\!Dev\AI overlay Translator\
├── main.py                              (unchanged: bootstraps src, calls app.run)
├── requirements.txt                     (add customtkinter, pystray, translators)
├── settings.json                        (created at runtime; gitignored)
├── history.json                         (created at runtime; gitignored)
├── src/overlay_translator/
│   ├── models.py                        (unchanged)
│   ├── capture.py                       (unchanged)
│   ├── ocr.py                           (unchanged)
│   ├── arabic.py                        (unchanged)
│   ├── settings_store.py                (NEW: Settings + load/save)
│   ├── history_store.py                 (NEW: HistoryEntry + HistoryStore)
│   ├── translate.py                     (REWRITE: Google/DeepL/Bing keyless)
│   ├── selector.py                      (REFACTOR: Toplevel(parent))
│   ├── overlay.py                       (REFACTOR: Toplevel + auto-hide)
│   ├── hotkey.py                        (NEW: HotkeyManager)
│   ├── tray.py                          (NEW: run_tray)
│   ├── app.py                           (REWRITE: build stores + AppWindow + run)
│   └── ui/
│       ├── __init__.py                  (NEW: empty)
│       ├── app_window.py                (NEW: CTk root + tabview + poll loop)
│       ├── home_tab.py                  (NEW)
│       ├── history_tab.py               (NEW)
│       └── settings_tab.py              (NEW)
├── config.py path REMOVED               (delete src/overlay_translator/config.py)
└── tests/
    ├── test_settings_store.py           (NEW)
    ├── test_history_store.py            (NEW)
    ├── test_translate.py                (REWRITE)
    ├── test_config.py                   (REMOVE config tests; keep Rect tests → rename)
    ├── test_ocr.py                      (unchanged)
    └── test_arabic.py                   (unchanged)
```

---

## Task 1: Dependencies + gitignore + retire config.py

**Files:**
- Modify: `requirements.txt`
- Modify: `.gitignore`
- Delete: `src/overlay_translator/config.py`
- Modify: `tests/test_config.py` → keep only the two `Rect` tests (config is gone)

**Interfaces:**
- Consumes: nothing.
- Produces: installed deps; `Rect` tests still cover `models.Rect`. No `config` module exists after this task; later tasks must not import it.

- [ ] **Step 1: Add UI deps to `requirements.txt`**

Replace the file contents with:

```
keyboard==0.13.5
mss==9.0.1
pytesseract==0.3.13
Pillow==10.4.0
deep-translator==1.11.4
translators==5.9.2
arabic-reshaper==3.0.0
python-bidi==0.4.2
customtkinter==6.0.0
pystray==0.19.5
pytest==8.3.2
```

(Note: `deepl` and `python-dotenv` are intentionally dropped — no API key, no `.env`.)

- [ ] **Step 2: Install**

Run: `python -m pip install -r requirements.txt`
Expected: ends with "Successfully installed ..." / "Requirement already satisfied".

- [ ] **Step 3: Ignore the runtime JSON files**

Append to `.gitignore`:

```
settings.json
history.json
```

- [ ] **Step 4: Delete `config.py` and trim its tests**

Delete the file `src/overlay_translator/config.py`.

Replace `tests/test_config.py` entirely with (only the Rect tests remain):

```python
from overlay_translator.models import Rect


def test_rect_area():
    r = Rect(x=10, y=20, width=100, height=50)
    assert r.area == 5000


def test_rect_zero_area():
    r = Rect(x=0, y=0, width=0, height=30)
    assert r.area == 0
```

- [ ] **Step 5: Verify the suite still collects (config-dependent tests removed)**

Run: `python -m pytest -q`
Expected: PASS. `test_translate.py` still imports the OLD translate API at this point — if it errors on collection, that's expected and fixed in Task 4; to keep this task green, temporarily run only the stable files:
Run: `python -m pytest tests/test_config.py tests/test_ocr.py tests/test_arabic.py -q`
Expected: PASS (all green).

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .gitignore tests/test_config.py
git rm src/overlay_translator/config.py
git commit -m "chore: add UI deps, retire config.py (keyless, no .env)"
```

---

## Task 2: settings_store

**Files:**
- Create: `src/overlay_translator/settings_store.py`
- Test: `tests/test_settings_store.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `@dataclass Settings` with fields `hotkey: str="alt+q"`, `auto_hide_seconds: int=5`, `engine: str="google"`, `font_size: int=18`, `theme: str="dark"`.
  - `load_settings(path: str) -> Settings` — missing file → defaults; corrupt/partial → each missing field filled from defaults (never raises).
  - `save_settings(settings: Settings, path: str) -> None` — writes pretty JSON.

- [ ] **Step 1: Write failing tests**

Create `tests/test_settings_store.py`:

```python
import json
from overlay_translator.settings_store import Settings, load_settings, save_settings


def test_defaults_when_file_missing(tmp_path):
    s = load_settings(str(tmp_path / "nope.json"))
    assert s == Settings()
    assert s.hotkey == "alt+q"
    assert s.auto_hide_seconds == 5
    assert s.engine == "google"


def test_round_trip(tmp_path):
    p = str(tmp_path / "settings.json")
    save_settings(Settings(hotkey="ctrl+space", auto_hide_seconds=0, engine="bing",
                           font_size=24, theme="light"), p)
    s = load_settings(p)
    assert s.hotkey == "ctrl+space"
    assert s.auto_hide_seconds == 0
    assert s.engine == "bing"
    assert s.font_size == 24
    assert s.theme == "light"


def test_partial_file_fills_missing_from_defaults(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({"engine": "deepl"}), encoding="utf-8")
    s = load_settings(str(p))
    assert s.engine == "deepl"       # from file
    assert s.hotkey == "alt+q"       # default
    assert s.font_size == 18         # default


def test_corrupt_file_returns_defaults(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text("{ not json", encoding="utf-8")
    s = load_settings(str(p))
    assert s == Settings()
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_settings_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'overlay_translator.settings_store'`

- [ ] **Step 3: Implement `settings_store.py`**

```python
import json
from dataclasses import asdict, dataclass, fields


@dataclass
class Settings:
    hotkey: str = "alt+q"
    auto_hide_seconds: int = 5
    engine: str = "google"
    font_size: int = 18
    theme: str = "dark"


def load_settings(path: str) -> Settings:
    """Load settings; missing/partial/corrupt files degrade to defaults."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("settings root is not an object")
    except (OSError, ValueError):
        return Settings()
    known = {f.name for f in fields(Settings)}
    kwargs = {k: v for k, v in data.items() if k in known}
    return Settings(**{**asdict(Settings()), **kwargs})


def save_settings(settings: Settings, path: str) -> None:
    """Write settings as pretty JSON."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(asdict(settings), fh, indent=2, ensure_ascii=False)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_settings_store.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/overlay_translator/settings_store.py tests/test_settings_store.py
git commit -m "feat: add settings_store with defaults and corrupt-file tolerance"
```

---

## Task 3: history_store

**Files:**
- Create: `src/overlay_translator/history_store.py`
- Test: `tests/test_history_store.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `@dataclass HistoryEntry` with `source: str`, `translation: str`, `timestamp: str`.
  - `MAX_ENTRIES = 200`.
  - `class HistoryStore`:
    - `__init__(self, path: str)` — loads existing entries (corrupt → empty).
    - `entries(self) -> list[HistoryEntry]` — newest-first (as stored).
    - `add(self, source, translation, timestamp) -> None` — prepend, trim to 200, save.
    - `delete(self, index: int) -> None` — remove entry at index, save.
    - `clear(self) -> None` — empty and save.

- [ ] **Step 1: Write failing tests**

Create `tests/test_history_store.py`:

```python
import json
from overlay_translator.history_store import HistoryStore, HistoryEntry, MAX_ENTRIES


def test_add_is_newest_first_and_persists(tmp_path):
    p = str(tmp_path / "history.json")
    store = HistoryStore(p)
    store.add("Hello", "مرحبا", "2026-07-11T10:00:00")
    store.add("Bye", "وداعا", "2026-07-11T10:01:00")
    entries = store.entries()
    assert entries[0].source == "Bye"        # newest first
    assert entries[1].source == "Hello"
    # persisted: a fresh store on the same path sees the same data
    assert HistoryStore(p).entries()[0].translation == "وداعا"


def test_cap_at_max_entries(tmp_path):
    store = HistoryStore(str(tmp_path / "h.json"))
    for i in range(MAX_ENTRIES + 25):
        store.add(f"s{i}", f"t{i}", "2026-07-11T10:00:00")
    assert len(store.entries()) == MAX_ENTRIES
    assert store.entries()[0].source == f"s{MAX_ENTRIES + 24}"  # newest kept


def test_delete_by_index(tmp_path):
    store = HistoryStore(str(tmp_path / "h.json"))
    store.add("a", "A", "t")
    store.add("b", "B", "t")   # entries: [b, a]
    store.delete(0)            # remove b
    assert [e.source for e in store.entries()] == ["a"]


def test_clear(tmp_path):
    store = HistoryStore(str(tmp_path / "h.json"))
    store.add("a", "A", "t")
    store.clear()
    assert store.entries() == []


def test_corrupt_file_starts_empty(tmp_path):
    p = tmp_path / "h.json"
    p.write_text("not json", encoding="utf-8")
    assert HistoryStore(str(p)).entries() == []
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_history_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'overlay_translator.history_store'`

- [ ] **Step 3: Implement `history_store.py`**

```python
import json
from dataclasses import asdict, dataclass

MAX_ENTRIES = 200


@dataclass
class HistoryEntry:
    source: str
    translation: str
    timestamp: str


class HistoryStore:
    """Newest-first translation history persisted to a JSON file."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._entries: list[HistoryEntry] = self._load()

    def _load(self) -> list[HistoryEntry]:
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return [
                HistoryEntry(
                    source=item["source"],
                    translation=item["translation"],
                    timestamp=item["timestamp"],
                )
                for item in data
            ]
        except (OSError, ValueError, KeyError, TypeError):
            print("[history] could not read history file; starting empty.")
            return []

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump([asdict(e) for e in self._entries], fh,
                      indent=2, ensure_ascii=False)

    def entries(self) -> list[HistoryEntry]:
        return list(self._entries)

    def add(self, source: str, translation: str, timestamp: str) -> None:
        self._entries.insert(0, HistoryEntry(source, translation, timestamp))
        del self._entries[MAX_ENTRIES:]
        self._save()

    def delete(self, index: int) -> None:
        if 0 <= index < len(self._entries):
            del self._entries[index]
            self._save()

    def clear(self) -> None:
        self._entries = []
        self._save()
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_history_store.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add src/overlay_translator/history_store.py tests/test_history_store.py
git commit -m "feat: add history_store with 200-cap and corrupt-file tolerance"
```

---

## Task 4: translate — three keyless engines

**Files:**
- Rewrite: `src/overlay_translator/translate.py`
- Rewrite: `tests/test_translate.py`

**Interfaces:**
- Consumes: nothing (engines are self-contained).
- Produces:
  - `TranslationError(Exception)`.
  - `GoogleEngine`, `DeeplEngine`, `BingEngine` — each with `translate(self, text: str) -> str`.
  - `make_engine(name: str) -> object` — `"google"|"deepl"|"bing"`; unknown → `TranslationError`.
  - `to_arabic(text: str, engine) -> str` — empty/whitespace → `""` without calling engine; else `engine.translate(text)`; wrap any exception in `TranslationError`.

- [ ] **Step 1: Write failing tests**

Replace `tests/test_translate.py` with:

```python
import pytest
from unittest.mock import MagicMock
from overlay_translator.translate import (
    to_arabic, make_engine, TranslationError,
    GoogleEngine, DeeplEngine, BingEngine,
)


def test_empty_returns_empty_without_calling_engine():
    engine = MagicMock()
    assert to_arabic("   ", engine) == ""
    engine.translate.assert_not_called()


def test_returns_translation():
    engine = MagicMock()
    engine.translate.return_value = "مرحبا"
    assert to_arabic("Hello", engine) == "مرحبا"
    engine.translate.assert_called_once_with("Hello")


def test_wraps_errors():
    engine = MagicMock()
    engine.translate.side_effect = RuntimeError("429")
    with pytest.raises(TranslationError):
        to_arabic("Hello", engine)


def test_make_engine_selects_type():
    assert isinstance(make_engine("google"), GoogleEngine)
    assert isinstance(make_engine("deepl"), DeeplEngine)
    assert isinstance(make_engine("bing"), BingEngine)


def test_make_engine_unknown_raises():
    with pytest.raises(TranslationError):
        make_engine("bogus")
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_translate.py -v`
Expected: FAIL (import error for the new names).

- [ ] **Step 3: Implement `translate.py`**

```python
"""Keyless English->Arabic translation engines.

All three engines use free public web endpoints — no API key. Selected by
name via make_engine(). Every engine exposes translate(text) -> str.
"""


class TranslationError(Exception):
    """Raised when a translation call fails (network, rate-limit, etc.)."""


class GoogleEngine:
    """Keyless Google Translate via deep-translator."""

    def __init__(self) -> None:
        from deep_translator import GoogleTranslator
        self._t = GoogleTranslator(source="en", target="ar")

    def translate(self, text: str) -> str:
        return self._t.translate(text)


class DeeplEngine:
    """Keyless DeepL via the `translators` free web endpoint (can rate-limit)."""

    def translate(self, text: str) -> str:
        import translators as ts
        return ts.translate_text(
            text, translator="deepl", from_language="en", to_language="ar"
        )


class BingEngine:
    """Keyless Bing (Microsoft) via the `translators` free web endpoint."""

    def translate(self, text: str) -> str:
        import translators as ts
        return ts.translate_text(
            text, translator="bing", from_language="en", to_language="ar"
        )


_ENGINES = {"google": GoogleEngine, "deepl": DeeplEngine, "bing": BingEngine}


def make_engine(name: str) -> object:
    """Build the engine named by `name` ('google'|'deepl'|'bing')."""
    try:
        return _ENGINES[name]()
    except KeyError:
        raise TranslationError(f"Unknown translation engine: {name!r}")


def to_arabic(text: str, engine) -> str:
    """Translate English text to Arabic. Empty input returns empty string."""
    if not text or not text.strip():
        return ""
    try:
        return engine.translate(text)
    except Exception as exc:
        raise TranslationError(str(exc)) from exc
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_translate.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Manual real-engine smoke (network; Google reliable)**

Run: `PYTHONPATH=src python -c "from overlay_translator.translate import make_engine, to_arabic; print(to_arabic('Good morning', make_engine('google')))"`
Expected: prints Arabic (e.g. `صباح الخير` / `صباح الخير!`). (DeepL may 429 — that's expected and handled; do not treat a DeepL 429 here as a failure.)

- [ ] **Step 6: Commit**

```bash
git add src/overlay_translator/translate.py tests/test_translate.py
git commit -m "feat: keyless Google/DeepL/Bing engines via make_engine"
```

---

## Task 5: overlay — Toplevel child + auto-hide timer

**Files:**
- Rewrite: `src/overlay_translator/overlay.py`

**Interfaces:**
- Consumes: `Rect` (models), `Settings` (settings_store — reads `.font_size`, `.auto_hide_seconds`).
- Produces: `show(text: str, rect: Rect, settings, parent) -> None` — creates a borderless top-most `tk.Toplevel(parent)` bubble just above `rect` (flips below if no room), right-aligned Arabic, dark colors. Dismiss on Esc/click. If `settings.auto_hide_seconds > 0`, auto-destroy after that many seconds. Returns immediately (no mainloop — the parent's loop pumps events).

- [ ] **Step 1: Implement `overlay.py`**

```python
import tkinter as tk
from .models import Rect

MARGIN = 8
BUBBLE_BG = "#1e1e1e"
BUBBLE_FG = "#ffffff"
BORDER = "#4a4a4a"


def show(text: str, rect: Rect, settings, parent) -> None:
    """Show a dismissible Arabic bubble just above the selected region."""
    win = tk.Toplevel(parent)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=BORDER)  # 1px border effect via padding

    label = tk.Label(
        win,
        text=text,
        justify="right",
        anchor="e",
        bg=BUBBLE_BG,
        fg=BUBBLE_FG,
        font=("Segoe UI", settings.font_size),
        wraplength=max(rect.width, 300),
        padx=12,
        pady=8,
    )
    label.pack(padx=1, pady=1)

    win.update_idletasks()
    bh = win.winfo_reqheight()

    x = rect.x
    y = rect.y - bh - MARGIN
    if y < 0:  # no room above -> place below the box
        y = rect.y + rect.height + MARGIN
    win.geometry(f"+{x}+{y}")

    def dismiss(_event=None):
        if win.winfo_exists():
            win.destroy()

    win.bind("<Escape>", dismiss)
    win.bind("<Button-1>", dismiss)
    label.bind("<Button-1>", dismiss)
    win.focus_force()

    seconds = settings.auto_hide_seconds
    if seconds and seconds > 0:
        win.after(int(seconds * 1000), dismiss)
```

- [ ] **Step 2: Manual smoke test (uses a throwaway CTk root)**

Run (PowerShell `$env:PYTHONPATH="src"`):

```bash
python -c "import customtkinter as ctk; from overlay_translator import overlay; from overlay_translator.models import Rect; from overlay_translator.settings_store import Settings; from overlay_translator.arabic import shape_for_display; root=ctk.CTk(); root.geometry('200x100'); overlay.show(shape_for_display('مرحبا بالعالم'), Rect(400,400,300,60), Settings(auto_hide_seconds=3), root); root.after(4000, root.destroy); root.mainloop(); print('closed')"
```

Expected: a dark bubble with joined right-aligned Arabic appears above y=400 and **auto-closes after ~3s**; the script prints `closed`. (Clicking it or pressing Esc closes it sooner.)

- [ ] **Step 3: Commit**

```bash
git add src/overlay_translator/overlay.py
git commit -m "refactor: overlay is a Toplevel child with auto-hide timer"
```

---

## Task 6: selector — Toplevel child returning a Rect

**Files:**
- Rewrite: `src/overlay_translator/selector.py`

**Interfaces:**
- Consumes: `Rect` (models), a tkinter parent (the `CTk` root).
- Produces: `select_region(parent) -> Optional[Rect]` — fullscreen dim `Toplevel(parent)` with crosshair; drag returns a screen-coordinate `Rect`; area < 25px² or Esc → `None`. Blocks via `parent.wait_window(win)` and returns the result.

- [ ] **Step 1: Implement `selector.py`**

```python
import tkinter as tk
from typing import Optional
from .models import Rect

MIN_AREA = 25


def select_region(parent) -> Optional[Rect]:
    """Show a fullscreen dim overlay; let the user drag a selection box."""
    win = tk.Toplevel(parent)
    win.attributes("-fullscreen", True)
    win.attributes("-alpha", 0.25)
    win.attributes("-topmost", True)
    win.configure(bg="black", cursor="crosshair")

    canvas = tk.Canvas(win, highlightthickness=0, bg="black")
    canvas.pack(fill="both", expand=True)

    state = {"x0": 0, "y0": 0, "rect_id": None, "result": None}

    def on_press(event):
        state["x0"], state["y0"] = event.x_root, event.y_root
        state["rect_id"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="#00ff00", width=2
        )

    def on_drag(event):
        if state["rect_id"] is not None:
            x0 = state["x0"] - win.winfo_rootx()
            y0 = state["y0"] - win.winfo_rooty()
            canvas.coords(state["rect_id"], x0, y0, event.x, event.y)

    def on_release(event):
        x = min(state["x0"], event.x_root)
        y = min(state["y0"], event.y_root)
        w = abs(event.x_root - state["x0"])
        h = abs(event.y_root - state["y0"])
        rect = Rect(x=x, y=y, width=w, height=h)
        state["result"] = rect if rect.area >= MIN_AREA else None
        win.destroy()

    def on_escape(_event):
        state["result"] = None
        win.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    win.bind("<Escape>", on_escape)

    win.grab_set()
    win.focus_force()
    parent.wait_window(win)
    return state["result"]
```

- [ ] **Step 2: Manual smoke test**

Run (PowerShell `$env:PYTHONPATH="src"`):

```bash
python -c "import customtkinter as ctk; from overlay_translator.selector import select_region; root=ctk.CTk(); root.geometry('200x100'); root.after(300, lambda: print('selected:', select_region(root)) or root.destroy()); root.mainloop()"
```

Expected: screen dims, crosshair cursor; dragging draws a green box; on release it prints `selected: Rect(...)`. Esc or a tiny click prints `selected: None`. Window then closes.

- [ ] **Step 3: Commit**

```bash
git add src/overlay_translator/selector.py
git commit -m "refactor: selector is a Toplevel child returning a Rect"
```

---

## Task 7: hotkey — HotkeyManager

**Files:**
- Create: `src/overlay_translator/hotkey.py`
- Test: `tests/test_hotkey.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `class HotkeyManager`:
    - `__init__(self, on_trigger)` — stores the callback fired on hotkey press.
    - `register(self, hotkey_str) -> bool` — removes any prior hotkey, registers `hotkey_str` via `keyboard.add_hotkey`; returns `True` on success, `False` if the string is invalid (keeps no active hotkey on failure).
    - `current(self) -> str | None` — the currently registered hotkey string.
  - The `keyboard` calls are isolated behind a small indirection so the test can substitute a fake backend.

- [ ] **Step 1: Write failing tests (backend injected, no real keyboard)**

Create `tests/test_hotkey.py`:

```python
import pytest
from overlay_translator.hotkey import HotkeyManager


class FakeBackend:
    def __init__(self, fail_on=None):
        self.added = []
        self.removed = []
        self._fail_on = fail_on
        self._handles = 0

    def add_hotkey(self, combo, callback):
        if combo == self._fail_on:
            raise ValueError("invalid hotkey")
        self.added.append(combo)
        self._handles += 1
        return f"handle-{self._handles}"

    def remove_hotkey(self, handle):
        self.removed.append(handle)


def test_register_success_sets_current():
    be = FakeBackend()
    mgr = HotkeyManager(lambda: None, backend=be)
    assert mgr.register("alt+q") is True
    assert mgr.current() == "alt+q"
    assert be.added == ["alt+q"]


def test_register_replaces_previous():
    be = FakeBackend()
    mgr = HotkeyManager(lambda: None, backend=be)
    mgr.register("alt+q")
    mgr.register("ctrl+space")
    assert mgr.current() == "ctrl+space"
    assert be.removed == ["handle-1"]      # old one removed
    assert be.added == ["alt+q", "ctrl+space"]


def test_register_invalid_returns_false_and_keeps_previous():
    be = FakeBackend(fail_on="bogus++")
    mgr = HotkeyManager(lambda: None, backend=be)
    mgr.register("alt+q")
    assert mgr.register("bogus++") is False
    assert mgr.current() == "alt+q"        # unchanged
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest tests/test_hotkey.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'overlay_translator.hotkey'`

- [ ] **Step 3: Implement `hotkey.py`**

```python
class _KeyboardBackend:
    """Thin wrapper over the real `keyboard` library (swappable in tests)."""

    def add_hotkey(self, combo, callback):
        import keyboard
        return keyboard.add_hotkey(combo, callback)

    def remove_hotkey(self, handle):
        import keyboard
        keyboard.remove_hotkey(handle)


class HotkeyManager:
    """Registers a single global hotkey, re-registerable at runtime."""

    def __init__(self, on_trigger, backend=None) -> None:
        self._on_trigger = on_trigger
        self._backend = backend or _KeyboardBackend()
        self._handle = None
        self._current = None

    def current(self):
        return self._current

    def register(self, hotkey_str: str) -> bool:
        """Register hotkey_str, replacing any previous one. False if invalid."""
        try:
            handle = self._backend.add_hotkey(hotkey_str, self._on_trigger)
        except (ValueError, Exception):
            return False
        if self._handle is not None:
            self._backend.remove_hotkey(self._handle)
        self._handle = handle
        self._current = hotkey_str
        return True
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_hotkey.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/overlay_translator/hotkey.py tests/test_hotkey.py
git commit -m "feat: HotkeyManager with runtime re-registration"
```

---

## Task 8: tray — system tray icon

**Files:**
- Create: `src/overlay_translator/tray.py`

**Interfaces:**
- Consumes: a `queue.Queue` (to push `("show",)` / `("quit",)`).
- Produces:
  - `build_icon(request_queue) -> pystray.Icon` — an icon with menu items "Show" → enqueues `("show",)` and "Quit" → enqueues `("quit",)` then stops the icon.
  - `_make_image() -> PIL.Image.Image` — a simple generated 64x64 icon (no external asset).
  - Runner note: the caller starts `icon.run()` on a **daemon thread**.

- [ ] **Step 1: Implement `tray.py`**

```python
import pystray
from PIL import Image, ImageDraw


def _make_image() -> Image.Image:
    """A simple 64x64 icon: a blue rounded square with a white 'A'."""
    img = Image.new("RGB", (64, 64), "#1f6feb")
    d = ImageDraw.Draw(img)
    d.rectangle((6, 6, 58, 58), outline="white", width=3)
    d.text((22, 18), "A", fill="white")
    return img


def build_icon(request_queue) -> "pystray.Icon":
    """Build a tray icon whose menu pushes ('show',)/('quit',) to the queue."""
    def on_show(icon, item):
        request_queue.put(("show",))

    def on_quit(icon, item):
        request_queue.put(("quit",))
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Show", on_show, default=True),
        pystray.MenuItem("Quit", on_quit),
    )
    return pystray.Icon("OverlayTranslator", _make_image(),
                        "OverlayTranslator", menu)
```

- [ ] **Step 2: Manual smoke test (tray icon appears, Quit stops it)**

Run (PowerShell `$env:PYTHONPATH="src"`):

```bash
python -c "import threading, queue, time; from overlay_translator import tray; q=queue.Queue(); ic=tray.build_icon(q); t=threading.Thread(target=ic.run, daemon=True); t.start(); time.sleep(3); print('icon running:', ic.visible); ic.stop(); print('stopped')"
```

Expected: a tray icon appears near the clock for ~3s; prints `icon running: True` then `stopped`. (Right-clicking it during the 3s shows Show/Quit — optional to try.)

- [ ] **Step 3: Commit**

```bash
git add src/overlay_translator/tray.py
git commit -m "feat: system tray icon with Show/Quit menu"
```

---

## Task 9: ui/app_window — CTk root, tabview, poll loop, translate cycle

**Files:**
- Create: `src/overlay_translator/ui/__init__.py` (empty)
- Create: `src/overlay_translator/ui/app_window.py`

**Interfaces:**
- Consumes: `settings_store.Settings`, `history_store.HistoryStore`, `hotkey.HotkeyManager`, `translate`, `selector`, `overlay`, `capture`, `ocr`, `arabic`; the three tab classes (Task 10-12); a `queue.Queue`.
- Produces:
  - `class AppWindow(customtkinter.CTk)`:
    - `__init__(self, settings, settings_path, history, request_queue)` — builds the window, tabview, tabs; applies theme; starts poll loop; sets close-to-tray.
    - `engine` attribute (built from `settings.engine`).
    - `hotkey_manager` attribute.
    - `run_translation_cycle(self) -> None` — the select→OCR→translate→overlay→history flow on the main thread.
    - `apply_settings(self) -> None` — re-reads self.settings: sets theme, rebuilds engine, re-registers hotkey; saves settings.json; refreshes Home.
    - `save_settings(self) -> None` — persist current settings to `settings_path`.
    - `tesseract_ok` (bool) attribute for Home to display.
    - Handles queue tuples: translate/show/quit/hotkey_recorded.
- Produces constants: `NO_TEXT_MSG = "No text found"`, `ERROR_MSG = "Translation failed — check your internet connection."`.

- [ ] **Step 1: Implement `ui/__init__.py`**

Create `src/overlay_translator/ui/__init__.py` empty (0 bytes).

- [ ] **Step 2: Implement `ui/app_window.py`**

```python
import queue
from datetime import datetime

import customtkinter as ctk
import pytesseract

from .. import capture, ocr, translate, arabic, overlay, selector
from ..hotkey import HotkeyManager
from .home_tab import HomeTab
from .history_tab import HistoryTab
from .settings_tab import SettingsTab

NO_TEXT_MSG = "No text found"
ERROR_MSG = "Translation failed — check your internet connection."


class AppWindow(ctk.CTk):
    def __init__(self, settings, settings_path, history, request_queue):
        super().__init__()
        self.settings = settings
        self._settings_path = settings_path
        self.history = history
        self._queue = request_queue

        self.title("OverlayTranslator")
        self.geometry("560x520")
        ctk.set_appearance_mode(self.settings.theme)

        self.engine = translate.make_engine(self.settings.engine)
        self.hotkey_manager = HotkeyManager(
            lambda: self._queue.put(("translate",))
        )
        self.hotkey_manager.register(self.settings.hotkey)
        self.tesseract_ok = self._check_tesseract()

        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=12, pady=12)
        self.home_tab = HomeTab(tabview.add("Home"), self)
        self.history_tab = HistoryTab(tabview.add("History"), self)
        self.settings_tab = SettingsTab(tabview.add("Settings"), self)

        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        self.after(50, self._poll)

    # ---- startup helpers ------------------------------------------------
    def _check_tesseract(self) -> bool:
        ocr.configure_tesseract(None)
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    # ---- queue loop -----------------------------------------------------
    def _poll(self):
        try:
            while True:
                msg = self._queue.get_nowait()
                self._handle(msg)
        except queue.Empty:
            pass
        self.after(50, self._poll)

    def _handle(self, msg):
        kind = msg[0]
        if kind == "translate":
            self.run_translation_cycle()
        elif kind == "show":
            self._show_window()
        elif kind == "quit":
            self._quit_app()
        elif kind == "hotkey_recorded":
            self.settings.hotkey = msg[1]
            self.hotkey_manager.register(msg[1])
            self.save_settings()
            self.home_tab.refresh()
            self.settings_tab.refresh()

    # ---- window lifecycle ----------------------------------------------
    def _hide_to_tray(self):
        self.withdraw()

    def _show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _quit_app(self):
        try:
            self.hotkey_manager  # unhook happens on process exit
        finally:
            self.destroy()

    # ---- settings -------------------------------------------------------
    def save_settings(self):
        from ..settings_store import save_settings
        save_settings(self.settings, self._settings_path)

    def apply_settings(self):
        ctk.set_appearance_mode(self.settings.theme)
        self.engine = translate.make_engine(self.settings.engine)
        self.hotkey_manager.register(self.settings.hotkey)
        self.save_settings()
        self.home_tab.refresh()

    # ---- the pipeline (main thread) ------------------------------------
    def run_translation_cycle(self):
        rect = selector.select_region(self)
        if rect is None:
            return
        try:
            image = capture.grab(rect)
            english = ocr.extract_text(image)
        except Exception:
            overlay.show(ERROR_MSG, rect, self.settings, self)
            return
        if not english:
            overlay.show(NO_TEXT_MSG, rect, self.settings, self)
            return
        try:
            ar = translate.to_arabic(english, self.engine)
        except translate.TranslationError:
            overlay.show(ERROR_MSG, rect, self.settings, self)
            return
        overlay.show(arabic.shape_for_display(ar), rect, self.settings, self)
        self.history.add(english, ar,
                         datetime.now().isoformat(timespec="seconds"))
        self.history_tab.refresh()
```

- [ ] **Step 3: Deferred verification**

`app_window` can't run standalone until the three tab modules exist (Tasks 10-12). Verify only that the tab imports are the sole missing pieces:

Run: `PYTHONPATH=src python -c "import ast; ast.parse(open('src/overlay_translator/ui/app_window.py').read()); print('parse ok')"`
Expected: `parse ok`. (Full import is exercised in Task 12.)

- [ ] **Step 4: Commit**

```bash
git add src/overlay_translator/ui/__init__.py src/overlay_translator/ui/app_window.py
git commit -m "feat: AppWindow controller (tabview, poll loop, translate cycle)"
```

---

## Task 10: ui/home_tab

**Files:**
- Create: `src/overlay_translator/ui/home_tab.py`

**Interfaces:**
- Consumes: the parent tab frame and the `AppWindow` controller (`app`). Reads `app.settings.hotkey`, `app.settings.engine`, `app.tesseract_ok`; calls `app.run_translation_cycle()`.
- Produces: `class HomeTab` with `__init__(self, parent, app)` and `refresh(self) -> None`.

- [ ] **Step 1: Implement `home_tab.py`**

```python
import customtkinter as ctk


class HomeTab:
    def __init__(self, parent, app):
        self._app = app
        self._status = ctk.CTkLabel(parent, text="", font=("Segoe UI", 20, "bold"))
        self._status.pack(pady=(28, 6))
        self._detail = ctk.CTkLabel(parent, text="", font=("Segoe UI", 13))
        self._detail.pack(pady=4)
        self._warn = ctk.CTkLabel(parent, text="", text_color="#e0a030",
                                  font=("Segoe UI", 12))
        self._warn.pack(pady=4)
        ctk.CTkButton(parent, text="Translate now",
                      command=app.run_translation_cycle).pack(pady=20)
        self.refresh()

    def refresh(self):
        hk = self._app.settings.hotkey
        self._status.configure(text=f"Ready — press {hk}")
        self._detail.configure(
            text=f"Engine: {self._app.settings.engine}    Hotkey: {hk}"
        )
        if self._app.tesseract_ok:
            self._warn.configure(text="")
        else:
            self._warn.configure(
                text="⚠ Tesseract not found — install it (winget install "
                     "UB-Mannheim.TesseractOCR) and restart."
            )
```

- [ ] **Step 2: Parse check**

Run: `PYTHONPATH=src python -c "import ast; ast.parse(open('src/overlay_translator/ui/home_tab.py').read()); print('parse ok')"`
Expected: `parse ok`.

- [ ] **Step 3: Commit**

```bash
git add src/overlay_translator/ui/home_tab.py
git commit -m "feat: Home tab (status, engine/hotkey, translate-now)"
```

---

## Task 11: ui/history_tab

**Files:**
- Create: `src/overlay_translator/ui/history_tab.py`

**Interfaces:**
- Consumes: parent tab frame + `AppWindow` controller. Reads `app.history.entries()`; calls `app.history.delete(i)`, `app.history.clear()`. Uses `self._app.clipboard_clear()/clipboard_append()` (the CTk root) to copy.
- Produces: `class HistoryTab` with `__init__(self, parent, app)` and `refresh(self) -> None`.

- [ ] **Step 1: Implement `history_tab.py`**

```python
import customtkinter as ctk


class HistoryTab:
    def __init__(self, parent, app):
        self._app = app
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", pady=(6, 4))
        ctk.CTkLabel(top, text="History", font=("Segoe UI", 16, "bold")).pack(
            side="left", padx=6)
        ctk.CTkButton(top, text="Clear all", width=90,
                      command=self._clear).pack(side="right", padx=6)
        self._list = ctk.CTkScrollableFrame(parent)
        self._list.pack(fill="both", expand=True, padx=4, pady=4)
        self.refresh()

    def _clear(self):
        self._app.history.clear()
        self.refresh()

    def _copy(self, text):
        self._app.clipboard_clear()
        self._app.clipboard_append(text)

    def _delete(self, index):
        self._app.history.delete(index)
        self.refresh()

    def refresh(self):
        for child in self._list.winfo_children():
            child.destroy()
        entries = self._app.history.entries()
        if not entries:
            ctk.CTkLabel(self._list, text="No translations yet.").pack(pady=20)
            return
        for i, e in enumerate(entries):
            row = ctk.CTkFrame(self._list)
            row.pack(fill="x", pady=3, padx=2)
            text = f"{e.source}  →  {e.translation}"
            ctk.CTkLabel(row, text=text, anchor="w", justify="left",
                         wraplength=360).grid(row=0, column=0, sticky="w",
                                              padx=6, pady=(4, 0), columnspan=3)
            ctk.CTkLabel(row, text=e.timestamp, font=("Segoe UI", 10),
                         text_color="#888888").grid(row=1, column=0, sticky="w",
                                                    padx=6, pady=(0, 4))
            ctk.CTkButton(row, text="Copy", width=56,
                          command=lambda t=e.translation: self._copy(t)).grid(
                              row=1, column=1, padx=2)
            ctk.CTkButton(row, text="Delete", width=64, fg_color="#8a3030",
                          command=lambda idx=i: self._delete(idx)).grid(
                              row=1, column=2, padx=2)
            row.grid_columnconfigure(0, weight=1)
```

- [ ] **Step 2: Parse check**

Run: `PYTHONPATH=src python -c "import ast; ast.parse(open('src/overlay_translator/ui/history_tab.py').read()); print('parse ok')"`
Expected: `parse ok`.

- [ ] **Step 3: Commit**

```bash
git add src/overlay_translator/ui/history_tab.py
git commit -m "feat: History tab (rows with copy/delete, clear-all)"
```

---

## Task 12: ui/settings_tab + app.py rewrite + end-to-end

**Files:**
- Create: `src/overlay_translator/ui/settings_tab.py`
- Rewrite: `src/overlay_translator/app.py`

**Interfaces:**
- `SettingsTab.__init__(self, parent, app)` + `refresh(self)`; edits `app.settings.*` and calls `app.apply_settings()`; the Record button spawns a thread that reads a hotkey and enqueues `("hotkey_recorded", combo)`.
- `app.run() -> None` — builds settings/history/queue, constructs `AppWindow`, starts the tray on a daemon thread, runs `mainloop()`.

- [ ] **Step 1: Implement `settings_tab.py`**

```python
import threading

import customtkinter as ctk

ENGINES = ["google", "deepl", "bing"]


class SettingsTab:
    def __init__(self, parent, app):
        self._app = app
        s = app.settings

        ctk.CTkLabel(parent, text="Hotkey", font=("Segoe UI", 13, "bold")).pack(
            anchor="w", padx=12, pady=(14, 2))
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12)
        self._hotkey_label = ctk.CTkLabel(row, text=s.hotkey)
        self._hotkey_label.pack(side="left", padx=(0, 10))
        self._record_btn = ctk.CTkButton(row, text="Record shortcut",
                                          command=self._record)
        self._record_btn.pack(side="left")

        ctk.CTkLabel(parent, text="Auto-hide (seconds)",
                     font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=12,
                                                         pady=(16, 2))
        self._auto_value = ctk.CTkLabel(parent, text=self._auto_text())
        self._auto_value.pack(anchor="w", padx=12)
        self._slider = ctk.CTkSlider(parent, from_=2, to=15, number_of_steps=13,
                                     command=self._on_slider)
        self._slider.set(s.auto_hide_seconds if s.auto_hide_seconds else 5)
        self._slider.pack(fill="x", padx=12, pady=4)
        self._off = ctk.CTkCheckBox(parent, text="Off (stay until dismissed)",
                                    command=self._on_off_toggle)
        if s.auto_hide_seconds == 0:
            self._off.select()
        self._off.pack(anchor="w", padx=12, pady=4)

        ctk.CTkLabel(parent, text="Engine", font=("Segoe UI", 13, "bold")).pack(
            anchor="w", padx=12, pady=(16, 2))
        self._engine = ctk.CTkSegmentedButton(parent, values=ENGINES,
                                              command=self._on_engine)
        self._engine.set(s.engine)
        self._engine.pack(anchor="w", padx=12, pady=4)

        ctk.CTkLabel(parent, text="Bubble font size",
                     font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=12,
                                                         pady=(16, 2))
        self._font = ctk.CTkSlider(parent, from_=12, to=36, number_of_steps=24,
                                   command=self._on_font)
        self._font.set(s.font_size)
        self._font.pack(fill="x", padx=12, pady=4)

        self._theme = ctk.CTkSwitch(parent, text="Light theme",
                                    command=self._on_theme)
        if s.theme == "light":
            self._theme.select()
        self._theme.pack(anchor="w", padx=12, pady=(16, 8))

    # ---- helpers --------------------------------------------------------
    def _auto_text(self):
        v = self._app.settings.auto_hide_seconds
        return "Off" if v == 0 else f"{v} s"

    def refresh(self):
        self._hotkey_label.configure(text=self._app.settings.hotkey)
        self._auto_value.configure(text=self._auto_text())

    # ---- handlers -------------------------------------------------------
    def _record(self):
        self._record_btn.configure(text="Press keys…", state="disabled")

        def worker():
            import keyboard
            combo = keyboard.read_hotkey(suppress=False)
            self._app._queue.put(("hotkey_recorded", combo))
            # re-enable on the main thread
            self._app.after(0, lambda: self._record_btn.configure(
                text="Record shortcut", state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_slider(self, value):
        if self._off.get():
            return
        self._app.settings.auto_hide_seconds = int(round(value))
        self._auto_value.configure(text=self._auto_text())
        self._app.save_settings()

    def _on_off_toggle(self):
        if self._off.get():
            self._app.settings.auto_hide_seconds = 0
        else:
            self._app.settings.auto_hide_seconds = int(round(self._slider.get()))
        self._auto_value.configure(text=self._auto_text())
        self._app.save_settings()

    def _on_engine(self, value):
        self._app.settings.engine = value
        self._app.apply_settings()

    def _on_font(self, value):
        self._app.settings.font_size = int(round(value))
        self._app.save_settings()

    def _on_theme(self):
        self._app.settings.theme = "light" if self._theme.get() else "dark"
        self._app.apply_settings()
```

- [ ] **Step 2: Rewrite `app.py`**

```python
import os
import queue
import threading

from .settings_store import load_settings
from .history_store import HistoryStore
from . import tray
from .ui.app_window import AppWindow

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SETTINGS_PATH = os.path.join(_ROOT, "settings.json")
HISTORY_PATH = os.path.join(_ROOT, "history.json")


def run() -> None:
    settings = load_settings(SETTINGS_PATH)
    history = HistoryStore(HISTORY_PATH)
    request_queue: "queue.Queue" = queue.Queue()

    app = AppWindow(settings, SETTINGS_PATH, history, request_queue)

    icon = tray.build_icon(request_queue)
    threading.Thread(target=icon.run, daemon=True).start()

    app.mainloop()
```

- [ ] **Step 3: Full import + construction check (no mainloop)**

Run:
```bash
PYTHONPATH=src python -c "from overlay_translator.ui.app_window import AppWindow; from overlay_translator import app, tray, settings_store, history_store; print('all imports ok')"
```
Expected: `all imports ok`.

- [ ] **Step 4: Headless window build check (create + destroy without mainloop)**

Run:
```bash
PYTHONPATH=src python -c "import queue; from overlay_translator.settings_store import Settings; from overlay_translator.history_store import HistoryStore; from overlay_translator.ui.app_window import AppWindow; import tempfile, os; d=tempfile.mkdtemp(); w=AppWindow(Settings(), os.path.join(d,'s.json'), HistoryStore(os.path.join(d,'h.json')), queue.Queue()); w.update(); print('window built; tesseract_ok=', w.tesseract_ok); w.destroy(); print('destroyed ok')"
```
Expected: prints `window built; tesseract_ok= True` (Tesseract is installed) and `destroyed ok`, with no traceback. This exercises every tab's construction.

- [ ] **Step 5: Full test suite green**

Run: `python -m pytest -q`
Expected: PASS (all tests across settings/history/translate/hotkey/ocr/arabic/config-Rect).

- [ ] **Step 6: Live end-to-end (human)**

1. `python main.py` — the window opens (dark) with Home/History/Settings tabs and a tray icon appears.
2. Press **Alt+Q**, drag over English text → an Arabic bubble appears and auto-hides after 5s; a row appears in History.
3. In **Settings**: click **Record shortcut**, press e.g. Ctrl+Space → hotkey updates; test the new hotkey. Move the auto-hide slider / toggle Off. Switch engine to Bing and translate again. Toggle Light theme.
4. Close the window → it hides to tray; tray **Show** reopens it; tray **Quit** exits.

- [ ] **Step 7: Commit**

```bash
git add src/overlay_translator/ui/settings_tab.py src/overlay_translator/app.py
git commit -m "feat: Settings tab + app.run wiring (tray + window); end-to-end"
```

---

## Task 13: README update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Rewrite `README.md`**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README for the GUI/tray app"
```

---

## Self-Review Notes

- **Spec coverage:** tray app + hide-to-tray (T8/T9/T12), three tabs (T9-T12), rebindable hotkey + Record (T7/T12), auto-hide timer 0=off (T5/T12), persistent history cap 200 (T3), keyless Google/DeepL/Bing (T4), settings.json/history.json in root + gitignore (T1/T2/T3/T12), Toplevel selector/overlay on one main-thread root (T5/T6/T9), corrupt-file tolerance (T2/T3), engine-failure/no-text/too-small handling (T9), theme + font size (T5/T12), config.py retired + deps (T1), README (T13). All spec sections mapped.
- **Placeholders:** none — every code/command step is concrete.
- **Type consistency:** `Settings` fields identical across T2/T5/T9/T12; `HistoryStore.add/delete/clear/entries` names consistent T3→T9/T11; `make_engine`/`to_arabic`/`TranslationError` consistent T4→T9; `HotkeyManager.register/current` consistent T7→T9/T12; queue tuples (`translate`/`show`/`quit`/`hotkey_recorded`) consistent T8/T9/T12; `select_region(parent)` and `overlay.show(text, rect, settings, parent)` consistent T5/T6→T9.
- **Known caveat carried from spec:** keyless DeepL may 429 (documented in README T13; handled as `TranslationError` → error bubble in T9).
