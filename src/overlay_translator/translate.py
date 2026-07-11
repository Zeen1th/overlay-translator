"""Keyless English->Arabic translation engines.

All three use free public web endpoints — no API key:
- google: Google's free web endpoint via deep-translator.
- bing:   Bing's free web endpoint via translators.
- deepl:  DeepL's free JSON-RPC web endpoint, implemented the DeepLX/Translumo
          way (browser-faithful request with the id + timestamp scheme). Best
          Arabic quality, but the free endpoint rate-limits by IP (HTTP 429):
          if your network is flagged it can fail — Google/Bing are the reliable
          keyless fallbacks.

Every engine exposes translate(text) -> str; build one with make_engine(name).
"""

import json
import random
import time


class TranslationError(Exception):
    """Raised when a translation call fails (network, rate-limit, etc.)."""


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
    """Keyless DeepL via its free JSON-RPC endpoint (the DeepLX/Translumo way).

    No API key. The endpoint rate-limits by IP; on a 429 we retry once, then
    raise a clear error so the app can suggest another engine.
    """

    URL = "https://www2.deepl.com/jsonrpc"
    _HEADERS = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Origin": "https://www.deepl.com",
        "Referer": "https://www.deepl.com/",
    }

    def __init__(self, post=None, sleep=None) -> None:
        # `post`/`sleep` are injectable for tests; default to the real ones.
        self._post = post
        self._sleep = sleep

    @staticmethod
    def _build_body(text: str) -> bytes:
        i_count = text.count("i")
        id_ = random.randint(8300000, 8399999) * 1000 + random.randint(0, 999)
        ts = int(time.time() * 1000)
        if i_count:
            step = i_count + 1
            ts = ts - (ts % step) + step
        body = {
            "jsonrpc": "2.0",
            "method": "LMT_handle_texts",
            "id": id_,
            "params": {
                "texts": [{"text": text, "requestAlternatives": 3}],
                "splitting": "newlines",
                "lang": {
                    "source_lang_user_selected": "EN",
                    "target_lang": "AR",
                },
                "timestamp": ts,
            },
        }
        s = json.dumps(body, ensure_ascii=False)
        # DeepL's web client varies the spacing after "method" based on the id.
        if (id_ + 5) % 29 == 0 or (id_ + 3) % 13 == 0:
            s = s.replace('"method":"', '"method" : "', 1)
        else:
            s = s.replace('"method":"', '"method": "', 1)
        return s.encode("utf-8")

    def translate(self, text: str) -> str:
        if self._post is not None:
            post = self._post
        else:
            import requests
            post = requests.post
        sleep = self._sleep or time.sleep

        for attempt in range(2):  # initial try + one retry on 429
            resp = post(
                self.URL,
                data=self._build_body(text),
                headers=self._HEADERS,
                timeout=20,
            )
            if getattr(resp, "status_code", None) == 429:
                if attempt == 0:
                    sleep(1.0)
                    continue
                raise TranslationError(
                    "DeepL is rate-limiting this network (429). Try again in a "
                    "moment, or switch to Google/Bing in Settings."
                )
            resp.raise_for_status()
            return resp.json()["result"]["texts"][0]["text"]
        raise TranslationError("DeepL request failed.")


_ENGINES = {"google": GoogleEngine, "bing": BingEngine, "deepl": DeeplEngine}


def make_engine(name: str) -> object:
    """Build the engine named by `name` ('google'|'bing'|'deepl')."""
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
    except TranslationError:
        raise
    except Exception as exc:  # engines raise several exception types
        raise TranslationError(str(exc)) from exc
