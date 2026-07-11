"""English->Arabic translation engines.

- google (keyless): Google's free web endpoint via deep-translator.
- bing   (keyless): Bing's free web endpoint via translators.
- deepl  (API key): the official DeepL API. Best Arabic quality and reliable,
  but requires a free API key (https://www.deepl.com/pro-api). The keyless
  DeepL web endpoint is aggressively rate-limited (HTTP 429) and effectively
  unusable, so DeepL here goes through the official API.

Every engine exposes translate(text) -> str; build one with make_engine(name).
"""


class TranslationError(Exception):
    """Raised when a translation call fails (network, rate-limit, bad key)."""


class GoogleEngine:
    """Keyless Google Translate via deep-translator."""

    def __init__(self) -> None:
        from deep_translator import GoogleTranslator
        self._t = GoogleTranslator(source="en", target="ar")

    def translate(self, text: str) -> str:
        return self._t.translate(text)


class BingEngine:
    """Keyless Bing (Microsoft) via the `translators` free web endpoint."""

    def translate(self, text: str) -> str:
        import translators as ts
        return ts.translate_text(
            text, translator="bing", from_language="en", to_language="ar"
        )


class DeeplEngine:
    """Official DeepL API (free tier). Requires an API key."""

    def __init__(self, api_key: str) -> None:
        import deepl
        self._t = deepl.Translator(api_key)

    def translate(self, text: str) -> str:
        result = self._t.translate_text(
            text, source_lang="EN", target_lang="AR"
        )
        return result.text


def make_engine(name: str, api_key: str = "") -> object:
    """Build the engine named by `name` ('google'|'bing'|'deepl').

    'deepl' requires a non-empty `api_key`; otherwise a TranslationError with a
    clear, user-facing message is raised.
    """
    if name == "google":
        return GoogleEngine()
    if name == "bing":
        return BingEngine()
    if name == "deepl":
        if not (api_key or "").strip():
            raise TranslationError(
                "DeepL needs a free API key — add it in Settings."
            )
        return DeeplEngine(api_key)
    raise TranslationError(f"Unknown translation engine: {name!r}")


def to_arabic(text: str, engine) -> str:
    """Translate English text to Arabic. Empty input returns empty string."""
    if not text or not text.strip():
        return ""
    try:
        return engine.translate(text)
    except Exception as exc:  # engines raise several exception types
        raise TranslationError(str(exc)) from exc
