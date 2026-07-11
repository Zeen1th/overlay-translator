import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from overlay_translator.app import run

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nOverlayTranslator stopped.")
