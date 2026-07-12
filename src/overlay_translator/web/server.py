import os

from flask import Flask, render_template

_PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATES = os.path.join(_PKG, "templates")
_STATIC = os.path.join(_PKG, "static")


def _clipboard_copy(text):
    import pyperclip
    pyperclip.copy(text)


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

    from flask import request

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
        kind = request.form.get("kind", "translate")
        combo = keyboard.read_hotkey(suppress=False)
        if kind == "translate":
            ok = True if state.hotkey_manager is None else state.hotkey_manager.register(combo)
            if ok:
                state.settings.hotkey = combo
        elif kind == "region":
            ok = True if state.region_hotkey_manager is None else state.region_hotkey_manager.register(combo)
            if ok:
                state.settings.region_hotkey = combo
        elif kind == "auto":
            ok = True if state.auto_hotkey_manager is None else state.auto_hotkey_manager.register(combo)
            if ok:
                state.settings.auto_toggle_hotkey = combo
        state.save()
        return _settings_fragment()

    @app.post("/settings/ocr-region/set")
    def set_ocr_region():
        if state.capture_region is not None:
            state.capture_region()
        return _settings_fragment()

    @app.post("/settings/ocr-region/clear")
    def clear_ocr_region():
        state.settings.ocr_region = None
        state.settings.use_saved_region = False
        state.settings.auto_translate_enabled = False
        if state.stop_auto is not None:
            state.stop_auto()
        state.save()
        return _settings_fragment()

    @app.post("/settings/ocr-region/use-saved")
    def use_saved_region():
        state.settings.use_saved_region = (
            request.form["enabled"] == "1" and bool(state.settings.ocr_region)
        )
        if not state.settings.use_saved_region:
            state.settings.auto_translate_enabled = False
            if state.stop_auto is not None:
                state.stop_auto()
        state.save()
        return _settings_fragment()

    @app.post("/auto/start")
    def auto_start():
        if state.start_auto is not None:
            state.start_auto()
        return _home_fragment()

    @app.post("/auto/stop")
    def auto_stop():
        if state.stop_auto is not None:
            state.stop_auto()
        return _home_fragment()

    @app.post("/auto/toggle")
    def auto_toggle():
        if state.toggle_auto is not None:
            state.toggle_auto()
        return _home_fragment()

    @app.post("/settings/auto/start")
    def settings_auto_start():
        if state.start_auto is not None:
            state.start_auto()
        return _settings_fragment()

    @app.post("/settings/auto/stop")
    def settings_auto_stop():
        if state.stop_auto is not None:
            state.stop_auto()
        return _settings_fragment()

    @app.post("/settings/startup")
    def set_startup():
        enabled = request.form["enabled"] == "1"
        from ..startup import set_startup_enabled
        state.settings.start_with_windows = set_startup_enabled(enabled, state.repo_root)
        state.save()
        return _settings_fragment()

    @app.post("/history/delete/<int:i>")
    def delete_history(i):
        with state.lock:
            state.history.delete_by_id(i)
        return _history_fragment()

    @app.post("/history/clear")
    def clear_history():
        with state.lock:
            state.history.clear()
        return _history_fragment()

    @app.post("/history/copy/<int:i>")
    def copy_history(i):
        with state.lock:
            entry = state.history.get_by_id(i)
        if entry is not None:
            _clipboard_copy(entry.translation)
        return ("", 204)

    return app
