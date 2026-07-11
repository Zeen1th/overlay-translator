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

    return app
