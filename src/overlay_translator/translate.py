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
