import ctypes
from overlay_translator.dpi import enable_dpi_awareness


class FakeUser32:
    """Stand-in for ctypes.windll.user32 to test without touching the real API."""

    def __init__(self, result=1, raises=False):
        self.calls = []
        self._result = result
        self._raises = raises

    def SetProcessDpiAwarenessContext(self, ctx):
        self.calls.append(ctx)
        if self._raises:
            raise OSError("boom")
        return self._result


def test_sets_per_monitor_v2_context():
    fake = FakeUser32()
    assert enable_dpi_awareness(user32=fake) is True
    assert len(fake.calls) == 1
    # PER_MONITOR_AWARE_V2 == -4, passed as a c_void_p
    assert fake.calls[0].value == ctypes.c_void_p(-4).value


def test_returns_false_when_api_fails():
    fake = FakeUser32(raises=True)
    assert enable_dpi_awareness(user32=fake) is False


def test_returns_false_when_api_reports_failure():
    fake = FakeUser32(result=0)
    assert enable_dpi_awareness(user32=fake) is False
