# OverlayTranslator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Windows Python app where pressing Alt+Q lets the user drag a box over English text and see an Arabic translation bubble appear just above it.

**Architecture:** Six focused modules (`config`, `ocr`, `translate`, `arabic`, `capture`, `selector`, `overlay`) wired by an `app` orchestrator and a thin `main.py` entry point. Pure-logic modules (config/ocr/translate/arabic) are unit-tested with mocks; GUI/system modules (selector/overlay/capture/hotkey) are verified manually. OCR is local (Tesseract); translation is the DeepL cloud API.

**Tech Stack:** Python 3.11, `keyboard`, `mss`, `pytesseract` (+ Tesseract OCR), `Pillow`, `deepl`, `arabic-reshaper`, `python-bidi`, `python-dotenv`, `pytest`.

## Global Constraints

- Python **3.11**; run pip as `python -m pip`.
- Target OS: **Windows 11**.
- Language direction is **English → Arabic only** (DeepL `source_lang="EN"`, `target_lang="AR"`).
- **DeepL API key** is read from a `.env` file (`DEEPL_API_KEY`); never hardcoded.
- Default hotkey is **`alt+q`**, overridable via config.
- Translation requires internet + DeepL; OCR runs locally with no internet.
- Package import root: `src/overlay_translator/`. Run tests from repo root with `python -m pytest`.
- Every module has one responsibility; keep GUI logic thin.

---

## File Structure

```
S:\!Dev\AI overlay Translator\
├── main.py                          # entry point: app.run()
├── requirements.txt
├── .env.example                     # DEEPL_API_KEY=your-key-here
├── pytest.ini
├── src/overlay_translator/
│   ├── __init__.py
│   ├── models.py                    # Rect dataclass
│   ├── config.py                    # Config dataclass + load_config()
│   ├── ocr.py                       # extract_text(image) -> str
│   ├── translate.py                 # to_arabic(text, translator) -> str
│   ├── arabic.py                    # shape_for_display(text) -> str
│   ├── capture.py                   # grab(rect) -> PIL.Image
│   ├── selector.py                  # select_region() -> Optional[Rect]
│   ├── overlay.py                   # show(text, rect) -> None
│   └── app.py                       # startup checks + wiring + hotkey
└── tests/
    ├── __init__.py
    ├── test_config.py
    ├── test_ocr.py
    ├── test_translate.py
    └── test_arabic.py
```

---

## Task 1: Project scaffold, dependencies, and `Rect` model

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `pytest.ini`
- Create: `src/overlay_translator/__init__.py` (empty)
- Create: `tests/__init__.py` (empty)
- Create: `src/overlay_translator/models.py`
- Test: `tests/test_config.py` (placeholder import test for now — replaced in Task 2)

**Interfaces:**
- Consumes: nothing.
- Produces: `Rect` dataclass with fields `x: int`, `y: int`, `width: int`, `height: int`, and property `area -> int`. Consumed by `capture`, `selector`, `overlay`.

- [ ] **Step 1: Create `requirements.txt`**

```
keyboard==0.13.5
mss==9.0.1
pytesseract==0.3.13
Pillow==10.4.0
deepl==1.18.0
arabic-reshaper==3.0.0
python-bidi==0.4.2
python-dotenv==1.0.1
pytest==8.3.2
```

- [ ] **Step 2: Install dependencies**

Run: `python -m pip install -r requirements.txt`
Expected: ends with "Successfully installed ..." (or "Requirement already satisfied").

- [ ] **Step 3: Create `.env.example`**

```
DEEPL_API_KEY=your-deepl-api-key-here
HOTKEY=alt+q
```

- [ ] **Step 4: Create `pytest.ini`**

```ini
[pytest]
pythonpath = src
testpaths = tests
```

- [ ] **Step 5: Create empty package/test init files**

Create `src/overlay_translator/__init__.py` with a single comment line:

```python
# OverlayTranslator package
```

Create `tests/__init__.py` empty (0 bytes).

- [ ] **Step 6: Write the failing test for `Rect`**

Create `tests/test_config.py`:

```python
from overlay_translator.models import Rect


def test_rect_area():
    r = Rect(x=10, y=20, width=100, height=50)
    assert r.area == 5000


def test_rect_zero_area():
    r = Rect(x=0, y=0, width=0, height=30)
    assert r.area == 0
```

- [ ] **Step 7: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'overlay_translator.models'`

- [ ] **Step 8: Implement `Rect`**

Create `src/overlay_translator/models.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    """A screen region in pixels: top-left (x, y) with width and height."""

    x: int
    y: int
    width: int
    height: int

    @property
    def area(self) -> int:
        return self.width * self.height
```

- [ ] **Step 9: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS (2 passed)

- [ ] **Step 10: Commit**

```bash
git add requirements.txt .env.example pytest.ini src/overlay_translator/__init__.py tests/__init__.py src/overlay_translator/models.py tests/test_config.py
git commit -m "feat: scaffold project, deps, and Rect model"
```

---

## Task 2: Config loading

**Files:**
- Create: `src/overlay_translator/config.py`
- Modify: `tests/test_config.py` (append config tests)

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `Config` dataclass: `deepl_api_key: str`, `hotkey: str`, `font_family: str`, `font_size: int`, `bubble_bg: str`, `bubble_fg: str`.
  - `load_config(env: Mapping[str, str]) -> Config`. Raises `ConfigError` (subclass of `Exception`) if `DEEPL_API_KEY` is missing or empty. `HOTKEY` defaults to `"alt+q"`. Appearance defaults: font_family `"Segoe UI"`, font_size `18`, bubble_bg `"#1e1e1e"`, bubble_fg `"#ffffff"`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_config.py`:

```python
import pytest
from overlay_translator.config import Config, ConfigError, load_config


def test_load_config_reads_key_and_defaults():
    cfg = load_config({"DEEPL_API_KEY": "abc123"})
    assert cfg.deepl_api_key == "abc123"
    assert cfg.hotkey == "alt+q"
    assert cfg.font_size == 18


def test_load_config_custom_hotkey():
    cfg = load_config({"DEEPL_API_KEY": "abc123", "HOTKEY": "ctrl+space"})
    assert cfg.hotkey == "ctrl+space"


def test_load_config_missing_key_raises():
    with pytest.raises(ConfigError):
        load_config({})


def test_load_config_empty_key_raises():
    with pytest.raises(ConfigError):
        load_config({"DEEPL_API_KEY": "   "})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'overlay_translator.config'`

- [ ] **Step 3: Implement `config.py`**

```python
from dataclasses import dataclass
from typing import Mapping


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    deepl_api_key: str
    hotkey: str = "alt+q"
    font_family: str = "Segoe UI"
    font_size: int = 18
    bubble_bg: str = "#1e1e1e"
    bubble_fg: str = "#ffffff"


def load_config(env: Mapping[str, str]) -> Config:
    key = (env.get("DEEPL_API_KEY") or "").strip()
    if not key:
        raise ConfigError(
            "DEEPL_API_KEY is missing. Copy .env.example to .env and add your key."
        )
    hotkey = (env.get("HOTKEY") or "alt+q").strip()
    return Config(deepl_api_key=key, hotkey=hotkey)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS (6 passed — 2 from Task 1 + 4 here)

- [ ] **Step 5: Commit**

```bash
git add src/overlay_translator/config.py tests/test_config.py
git commit -m "feat: add config loading with DeepL key validation"
```

---

## Task 3: OCR module

**Files:**
- Create: `src/overlay_translator/ocr.py`
- Test: `tests/test_ocr.py`

**Interfaces:**
- Consumes: a `PIL.Image.Image`.
- Produces: `extract_text(image) -> str`. Calls `pytesseract.image_to_string(image, lang="eng")`, returns the result stripped of leading/trailing whitespace. Also exposes `configure_tesseract(path: str | None) -> None` which sets `pytesseract.pytesseract.tesseract_cmd` when a path is given.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ocr.py`:

```python
from unittest.mock import patch
from PIL import Image
from overlay_translator import ocr


def _blank_image():
    return Image.new("RGB", (10, 10), "white")


def test_extract_text_strips_whitespace():
    with patch("overlay_translator.ocr.pytesseract.image_to_string",
               return_value="  Hello world \n"):
        assert ocr.extract_text(_blank_image()) == "Hello world"


def test_extract_text_empty_result():
    with patch("overlay_translator.ocr.pytesseract.image_to_string",
               return_value="\n\n"):
        assert ocr.extract_text(_blank_image()) == ""


def test_extract_text_uses_english_lang():
    with patch("overlay_translator.ocr.pytesseract.image_to_string",
               return_value="hi") as m:
        ocr.extract_text(_blank_image())
        assert m.call_args.kwargs.get("lang") == "eng"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ocr.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'overlay_translator.ocr'`

- [ ] **Step 3: Implement `ocr.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ocr.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/overlay_translator/ocr.py tests/test_ocr.py
git commit -m "feat: add local OCR text extraction"
```

---

## Task 4: DeepL translation module

**Files:**
- Create: `src/overlay_translator/translate.py`
- Test: `tests/test_translate.py`

**Interfaces:**
- Consumes: `deepl.Translator` instance (dependency-injected for testability).
- Produces:
  - `make_translator(api_key: str) -> deepl.Translator`.
  - `to_arabic(text: str, translator) -> str`. Returns `""` for empty/whitespace input without calling the API. Otherwise calls `translator.translate_text(text, source_lang="EN", target_lang="AR")` and returns `result.text`. Wraps any exception from the translator in `TranslationError` (subclass of `Exception`).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_translate.py`:

```python
import pytest
from unittest.mock import MagicMock
from overlay_translator.translate import to_arabic, TranslationError


def test_to_arabic_empty_returns_empty_without_api_call():
    translator = MagicMock()
    assert to_arabic("   ", translator) == ""
    translator.translate_text.assert_not_called()


def test_to_arabic_returns_translated_text():
    translator = MagicMock()
    translator.translate_text.return_value = MagicMock(text="مرحبا")
    assert to_arabic("Hello", translator) == "مرحبا"
    translator.translate_text.assert_called_once_with(
        "Hello", source_lang="EN", target_lang="AR"
    )


def test_to_arabic_wraps_errors():
    translator = MagicMock()
    translator.translate_text.side_effect = RuntimeError("network down")
    with pytest.raises(TranslationError):
        to_arabic("Hello", translator)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_translate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'overlay_translator.translate'`

- [ ] **Step 3: Implement `translate.py`**

```python
import deepl


class TranslationError(Exception):
    """Raised when the DeepL translation call fails."""


def make_translator(api_key: str) -> deepl.Translator:
    return deepl.Translator(api_key)


def to_arabic(text: str, translator) -> str:
    """Translate English text to Arabic. Empty input returns empty string."""
    if not text or not text.strip():
        return ""
    try:
        result = translator.translate_text(
            text, source_lang="EN", target_lang="AR"
        )
    except Exception as exc:  # deepl raises several exception types
        raise TranslationError(str(exc)) from exc
    return result.text
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_translate.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/overlay_translator/translate.py tests/test_translate.py
git commit -m "feat: add DeepL English-to-Arabic translation"
```

---

## Task 5: Arabic display shaping

**Files:**
- Create: `src/overlay_translator/arabic.py`
- Test: `tests/test_arabic.py`

**Interfaces:**
- Consumes: raw Arabic string from `translate`.
- Produces: `shape_for_display(text: str) -> str`. Runs `arabic_reshaper.reshape` then `bidi.algorithm.get_display` so `tkinter` renders joined, right-to-left Arabic correctly. Empty input returns `""`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_arabic.py`:

```python
from overlay_translator.arabic import shape_for_display


def test_empty_returns_empty():
    assert shape_for_display("") == ""


def test_shaping_returns_reordered_string():
    src = "مرحبا"
    out = shape_for_display(src)
    # Output is a non-empty string, reordered for visual RTL display,
    # so it differs from the raw logical-order input.
    assert isinstance(out, str)
    assert out != ""
    assert out != src


def test_shaping_preserves_ascii_passthrough():
    # Plain ASCII has nothing to reshape; characters are preserved.
    out = shape_for_display("abc")
    assert set(out) == set("abc")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_arabic.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'overlay_translator.arabic'`

- [ ] **Step 3: Implement `arabic.py`**

```python
import arabic_reshaper
from bidi.algorithm import get_display


def shape_for_display(text: str) -> str:
    """Join Arabic letters and reorder to visual RTL for tkinter display."""
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_arabic.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/overlay_translator/arabic.py tests/test_arabic.py
git commit -m "feat: add Arabic reshaping for RTL display"
```

---

## Task 6: Screen capture

**Files:**
- Create: `src/overlay_translator/capture.py`

**Interfaces:**
- Consumes: `Rect`.
- Produces: `grab(rect: Rect) -> PIL.Image.Image`. Uses `mss` to screenshot the region and converts to a PIL image.

- [ ] **Step 1: Implement `capture.py`**

```python
import mss
from PIL import Image
from .models import Rect


def grab(rect: Rect) -> Image.Image:
    """Screenshot the given screen region and return a PIL image."""
    region = {
        "left": rect.x,
        "top": rect.y,
        "width": rect.width,
        "height": rect.height,
    }
    with mss.mss() as sct:
        shot = sct.grab(region)
    return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
```

- [ ] **Step 2: Manual smoke test**

Run this one-off from the repo root:

```bash
python -c "from overlay_translator.capture import grab; from overlay_translator.models import Rect; img=grab(Rect(0,0,200,100)); print(img.size); img.save('scratch_capture.png')"
```

Expected: prints `(200, 100)` and writes `scratch_capture.png` showing the top-left corner of your screen. Delete the file after: `rm scratch_capture.png`.

Note: run with `PYTHONPATH=src` if not using pytest.ini's path — e.g. `set PYTHONPATH=src` (PowerShell: `$env:PYTHONPATH="src"`) before the command.

- [ ] **Step 3: Commit**

```bash
git add src/overlay_translator/capture.py
git commit -m "feat: add screen-region capture via mss"
```

---

## Task 7: Region selector (dim overlay + crosshair drag)

**Files:**
- Create: `src/overlay_translator/selector.py`

**Interfaces:**
- Consumes: nothing (reads the screen via a fullscreen tkinter window).
- Produces: `select_region() -> Optional[Rect]`. Shows a fullscreen semi-transparent window with a crosshair cursor; user drags a rectangle. Returns a `Rect` on release, or `None` if the selection area is < 25 px² (accidental click) or the user presses `Esc`.

- [ ] **Step 1: Implement `selector.py`**

```python
import tkinter as tk
from typing import Optional
from .models import Rect

MIN_AREA = 25


def select_region() -> Optional[Rect]:
    """Show a fullscreen dim overlay; let the user drag a selection box."""
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.25)
    root.attributes("-topmost", True)
    root.configure(bg="black", cursor="crosshair")

    canvas = tk.Canvas(root, highlightthickness=0, bg="black")
    canvas.pack(fill="both", expand=True)

    state = {"x0": 0, "y0": 0, "rect_id": None, "result": None}

    def on_press(event):
        state["x0"], state["y0"] = event.x_root, event.y_root
        state["rect_id"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="#00ff00", width=2
        )

    def on_drag(event):
        if state["rect_id"] is not None:
            x0 = state["x0"] - root.winfo_rootx()
            y0 = state["y0"] - root.winfo_rooty()
            canvas.coords(state["rect_id"], x0, y0, event.x, event.y)

    def on_release(event):
        x = min(state["x0"], event.x_root)
        y = min(state["y0"], event.y_root)
        w = abs(event.x_root - state["x0"])
        h = abs(event.y_root - state["y0"])
        rect = Rect(x=x, y=y, width=w, height=h)
        state["result"] = rect if rect.area >= MIN_AREA else None
        root.destroy()

    def on_escape(_event):
        state["result"] = None
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_escape)

    root.mainloop()
    return state["result"]
```

- [ ] **Step 2: Manual smoke test**

Run from repo root (with `$env:PYTHONPATH="src"` in PowerShell):

```bash
python -c "from overlay_translator.selector import select_region; print(select_region())"
```

Expected: screen dims, cursor is a crosshair, dragging draws a green box; on release it prints a `Rect(...)`. Pressing `Esc` prints `None`. A tiny click prints `None`.

- [ ] **Step 3: Commit**

```bash
git add src/overlay_translator/selector.py
git commit -m "feat: add dim-screen region selector"
```

---

## Task 8: Translation overlay bubble

**Files:**
- Create: `src/overlay_translator/overlay.py`

**Interfaces:**
- Consumes: shaped display text (already RTL-processed by `arabic.shape_for_display`), a `Rect`, and a `Config`.
- Produces: `show(text: str, rect: Rect, config: Config) -> None`. Displays a borderless top-most bubble just above `rect`'s top edge (flips to just below if there's no room above). Right-aligned text using `config.font_family/font_size/bubble_bg/bubble_fg`. Dismisses on `Esc` or any click.

- [ ] **Step 1: Implement `overlay.py`**

```python
import tkinter as tk
from .models import Rect
from .config import Config

MARGIN = 8


def show(text: str, rect: Rect, config: Config) -> None:
    """Show a dismissible Arabic bubble just above the selected region."""
    win = tk.Tk()
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=config.bubble_fg)  # thin border effect

    label = tk.Label(
        win,
        text=text,
        justify="right",
        anchor="e",
        bg=config.bubble_bg,
        fg=config.bubble_fg,
        font=(config.font_family, config.font_size),
        wraplength=max(rect.width, 300),
        padx=12,
        pady=8,
    )
    label.pack(padx=1, pady=1)

    win.update_idletasks()
    bw = win.winfo_reqwidth()
    bh = win.winfo_reqheight()

    x = rect.x
    y = rect.y - bh - MARGIN
    if y < 0:  # no room above -> place below the box
        y = rect.y + rect.height + MARGIN
    win.geometry(f"+{x}+{y}")

    win.bind("<Escape>", lambda _e: win.destroy())
    win.bind("<Button-1>", lambda _e: win.destroy())
    win.focus_force()
    win.mainloop()
```

- [ ] **Step 2: Manual smoke test**

Run from repo root (PowerShell `$env:PYTHONPATH="src"`):

```bash
python -c "from overlay_translator.overlay import show; from overlay_translator.models import Rect; from overlay_translator.config import Config; from overlay_translator.arabic import shape_for_display; show(shape_for_display('مرحبا بالعالم'), Rect(400,400,300,60), Config(deepl_api_key='x'))"
```

Expected: a dark bubble with right-aligned, correctly joined Arabic appears above y=400. Clicking it or pressing `Esc` closes it.

- [ ] **Step 3: Commit**

```bash
git add src/overlay_translator/overlay.py
git commit -m "feat: add Arabic translation overlay bubble"
```

---

## Task 9: App orchestration, startup checks, and entry point

**Files:**
- Create: `src/overlay_translator/app.py`
- Create: `main.py`

**Interfaces:**
- Consumes: all prior modules.
- Produces:
  - `check_tesseract() -> None` — raises `ConfigError` with install guidance if `pytesseract.get_tesseract_version()` fails.
  - `translate_selection(config, translator) -> None` — runs the full pipeline once: `selector.select_region()`; if `None`, return silently. Else `capture.grab` → `ocr.extract_text` → branch on empty ("No text found") → `translate.to_arabic` (catch `TranslationError` → error message) → `arabic.shape_for_display` → `overlay.show`.
  - `run() -> None` — loads `.env`, `load_config(os.environ)`, `check_tesseract()`, builds translator, registers the hotkey to call `translate_selection`, and blocks with `keyboard.wait()`.
- `main.py` calls `run()` and prints friendly `ConfigError` messages to the console.

- [ ] **Step 1: Implement `app.py`**

```python
import os
import pytesseract
from dotenv import load_dotenv
import keyboard

from .config import Config, ConfigError, load_config
from . import capture, ocr, translate, arabic, overlay, selector

NO_TEXT_MSG = "No text found"
ERROR_MSG = "Translation failed — check your connection and DeepL key."


def check_tesseract() -> None:
    """Verify Tesseract is installed and reachable."""
    try:
        pytesseract.get_tesseract_version()
    except Exception as exc:
        raise ConfigError(
            "Tesseract OCR is not installed or not on PATH. Install it from "
            "https://github.com/UB-Mannheim/tesseract/wiki and re-run."
        ) from exc


def translate_selection(config: Config, translator) -> None:
    """Run one full select -> OCR -> translate -> show cycle."""
    rect = selector.select_region()
    if rect is None:
        return
    image = capture.grab(rect)
    english = ocr.extract_text(image)
    if not english:
        overlay.show(NO_TEXT_MSG, rect, config)
        return
    try:
        arabic_text = translate.to_arabic(english, translator)
    except translate.TranslationError:
        overlay.show(ERROR_MSG, rect, config)
        return
    overlay.show(arabic.shape_for_display(arabic_text), rect, config)


def run() -> None:
    load_dotenv()
    config = load_config(os.environ)
    check_tesseract()
    translator = translate.make_translator(config.deepl_api_key)

    keyboard.add_hotkey(
        config.hotkey, lambda: translate_selection(config, translator)
    )
    print(f"OverlayTranslator ready. Press {config.hotkey} to translate. "
          f"Ctrl+C to quit.")
    keyboard.wait()
```

- [ ] **Step 2: Implement `main.py`**

```python
from overlay_translator.app import run
from overlay_translator.config import ConfigError

if __name__ == "__main__":
    try:
        run()
    except ConfigError as exc:
        print(f"[Setup needed] {exc}")
    except KeyboardInterrupt:
        print("\nOverlayTranslator stopped.")
```

- [ ] **Step 3: Verify import + config-error path without a key**

Temporarily ensure no `.env` exists (or `DEEPL_API_KEY` unset), then run:

```bash
python main.py
```

Expected: prints `[Setup needed] DEEPL_API_KEY is missing...` and exits (does not hang). If it instead reports the Tesseract message, that's also an acceptable setup error.

- [ ] **Step 4: End-to-end manual test (real key + Tesseract installed)**

1. Install Tesseract OCR (UB-Mannheim build). If not on PATH, note its path.
2. Copy `.env.example` to `.env` and set a real `DEEPL_API_KEY`.
3. Run `python main.py`.
4. Open a webpage with English text, press **Alt+Q**, drag a box over a sentence.
5. Expected: an Arabic bubble appears just above the box within ~1–2s. `Esc`/click dismisses it.

- [ ] **Step 5: Commit**

```bash
git add src/overlay_translator/app.py main.py
git commit -m "feat: wire pipeline, startup checks, and entry point"
```

---

## Task 10: README with setup instructions

**Files:**
- Create: `README.md`

**Interfaces:** none (documentation).

- [ ] **Step 1: Write `README.md`**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add setup and usage README"
```

---

## Self-Review Notes

- **Spec coverage:** hotkey (T9), selector/dim (T7), capture (T6), OCR (T3), DeepL EN→AR (T4), RTL shaping (T5/T8), bubble-above-with-flip (T8), Esc/click dismiss (T8), empty-OCR + DeepL-failure messages (T9), Tesseract + API-key startup checks (T2/T9), config from `.env` (T2), tiny-selection ignore (T7). All spec sections mapped.
- **Placeholders:** none — all code and commands are concrete.
- **Type consistency:** `Rect(x, y, width, height)` used identically across capture/selector/overlay; `Config` fields match between `config.py`, `overlay.show`, and `app.run`; `TranslationError` defined in T4 and caught in T9; `shape_for_display` name consistent T5/T9.
