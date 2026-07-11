"""Translation engines (English -> Arabic).

Two interchangeable engines, selected by ``config.translation_engine``:

- ``"google"`` (default): keyless Google Translate via ``deep-translator``.
  No API key, no signup. Uses Google's free web endpoint.
- ``"deepl_api"``: the official DeepL API, which requires a free API key.

Both engines expose the same tiny interface: a ``translate(text) -> str``
method, so the rest of the app never needs to know which one is in use.
"""

from deep_translator import GoogleTranslator


class TranslationError(Exception):
    """Raised when a translation call fails."""


class GoogleEngine:
    """Keyless English->Arabic translation via Google's free web endpoint."""

    def __init__(self) -> None:
        self._translator = GoogleTranslator(source="en", target="ar")

    def translate(self, text: str) -> str:
        return self._translator.translate(text)


class DeepLApiEngine:
    """English->Arabic translation via the official DeepL API (needs a key)."""

    def __init__(self, api_key: str) -> None:
        import deepl

        self._translator = deepl.Translator(api_key)

    def translate(self, text: str) -> str:
        result = self._translator.translate_text(
            text, source_lang="EN", target_lang="AR"
        )
        return result.text


def make_translator(config) -> object:
    """Build the translation engine named by ``config.translation_engine``."""
    engine = config.translation_engine
    if engine == "google":
        return GoogleEngine()
    if engine == "deepl_api":
        return DeepLApiEngine(config.deepl_api_key)
    raise TranslationError(f"Unknown translation engine: {engine!r}")


def to_arabic(text: str, translator) -> str:
    """Translate English text to Arabic. Empty input returns empty string."""
    if not text or not text.strip():
        return ""
    try:
        return translator.translate(text)
    except Exception as exc:  # engines raise several exception types
        raise TranslationError(str(exc)) from exc
