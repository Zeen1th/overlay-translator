import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from overlay_translator.app import run
from overlay_translator.config import ConfigError

if __name__ == "__main__":
    try:
        run()
    except ConfigError as exc:
        print(f"[Setup needed] {exc}")
    except KeyboardInterrupt:
        print("\nOverlayTranslator stopped.")
