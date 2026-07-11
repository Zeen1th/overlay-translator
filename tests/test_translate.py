import pytest
from unittest.mock import MagicMock
from overlay_translator.translate import (
    to_arabic, make_engine, TranslationError,
    GoogleEngine, DeeplEngine, BingEngine,
)


class _Resp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_empty_returns_empty_without_calling_engine():
    engine = MagicMock()
    assert to_arabic("   ", engine) == ""
    engine.translate.assert_not_called()


def test_returns_translation():
    engine = MagicMock()
    engine.translate.return_value = "مرحبا"
    assert to_arabic("Hello", engine) == "مرحبا"
    engine.translate.assert_called_once_with("Hello")


def test_wraps_errors():
    engine = MagicMock()
    engine.translate.side_effect = RuntimeError("boom")
    with pytest.raises(TranslationError):
        to_arabic("Hello", engine)


def test_make_engine_types_all_keyless():
    assert isinstance(make_engine("google"), GoogleEngine)
    assert isinstance(make_engine("bing"), BingEngine)
    assert isinstance(make_engine("deepl"), DeeplEngine)


def test_make_engine_unknown_raises():
    with pytest.raises(TranslationError):
        make_engine("bogus")


def test_deepl_engine_parses_result():
    calls = []

    def fake_post(url, data=None, headers=None, timeout=None):
        calls.append((url, data, headers))
        return _Resp(200, {"result": {"texts": [{"text": "مرحبا"}]}})

    engine = DeeplEngine(post=fake_post)
    assert engine.translate("Hello") == "مرحبا"
    assert calls[0][0] == DeeplEngine.URL
    # the request body must carry the source text
    assert b"Hello" in calls[0][1]


def test_deepl_engine_429_retries_then_raises():
    attempts = {"n": 0}

    def fake_post(url, data=None, headers=None, timeout=None):
        attempts["n"] += 1
        return _Resp(429)

    engine = DeeplEngine(post=fake_post, sleep=lambda _s: None)
    with pytest.raises(Exception):
        engine.translate("Hello")
    assert attempts["n"] >= 2  # retried at least once before giving up


def test_deepl_engine_429_then_success():
    seq = [_Resp(429), _Resp(200, {"result": {"texts": [{"text": "أهلا"}]}})]

    def fake_post(url, data=None, headers=None, timeout=None):
        return seq.pop(0)

    engine = DeeplEngine(post=fake_post, sleep=lambda _s: None)
    assert engine.translate("Hi") == "أهلا"
