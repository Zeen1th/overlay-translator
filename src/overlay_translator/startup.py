import os


_STARTUP_FILE = "OverlayTranslator-Startup.cmd"


def _startup_dir() -> str:
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        raise RuntimeError("APPDATA is not available")
    return os.path.join(
        appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
    )


def startup_script_path() -> str:
    return os.path.join(_startup_dir(), _STARTUP_FILE)


def is_startup_enabled() -> bool:
    return os.path.isfile(startup_script_path())


def set_startup_enabled(enabled: bool, repo_root: str) -> bool:
    path = startup_script_path()
    if enabled:
        run_bat = os.path.join(repo_root, "run_overlay_translator.bat")
        content = (
            "@echo off\n"
            f'cd /d "{repo_root}"\n'
            f'start "" "{run_bat}"\n'
        )
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        return True
    if os.path.exists(path):
        os.remove(path)
    return False
