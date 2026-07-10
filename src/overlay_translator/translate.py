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
