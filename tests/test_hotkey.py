import pytest
from overlay_translator.hotkey import HotkeyManager


class FakeBackend:
    def __init__(self, fail_on=None):
        self.added = []
        self.removed = []
        self._fail_on = fail_on
        self._handles = 0

    def add_hotkey(self, combo, callback):
        if combo == self._fail_on:
            raise ValueError("invalid hotkey")
        self.added.append(combo)
        self._handles += 1
        return f"handle-{self._handles}"

    def remove_hotkey(self, handle):
        self.removed.append(handle)


def test_register_success_sets_current():
    be = FakeBackend()
    mgr = HotkeyManager(lambda: None, backend=be)
    assert mgr.register("alt+q") is True
    assert mgr.current() == "alt+q"
    assert be.added == ["alt+q"]


def test_register_replaces_previous():
    be = FakeBackend()
    mgr = HotkeyManager(lambda: None, backend=be)
    mgr.register("alt+q")
    mgr.register("ctrl+space")
    assert mgr.current() == "ctrl+space"
    assert be.removed == ["handle-1"]      # old one removed
    assert be.added == ["alt+q", "ctrl+space"]


def test_register_invalid_returns_false_and_keeps_previous():
    be = FakeBackend(fail_on="bogus++")
    mgr = HotkeyManager(lambda: None, backend=be)
    mgr.register("alt+q")
    assert mgr.register("bogus++") is False
    assert mgr.current() == "alt+q"        # unchanged
