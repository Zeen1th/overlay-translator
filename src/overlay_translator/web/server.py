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
