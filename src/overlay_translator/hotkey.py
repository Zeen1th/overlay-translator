class _KeyboardBackend:
    """Thin wrapper over the real `keyboard` library (swappable in tests)."""

    def add_hotkey(self, combo, callback):
        import keyboard
        return keyboard.add_hotkey(combo, callback)

    def remove_hotkey(self, handle):
        import keyboard
        keyboard.remove_hotkey(handle)


class HotkeyManager:
    """Registers a single global hotkey, re-registerable at runtime."""

    def __init__(self, on_trigger, backend=None) -> None:
        self._on_trigger = on_trigger
        self._backend = backend or _KeyboardBackend()
        self._handle = None
        self._current = None

    def current(self):
        return self._current

    def register(self, hotkey_str: str) -> bool:
        """Register hotkey_str, replacing any previous one. False if invalid."""
        try:
            handle = self._backend.add_hotkey(hotkey_str, self._on_trigger)
        except ValueError:
            return False
        if self._handle is not None:
            self._backend.remove_hotkey(self._handle)
        self._handle = handle
        self._current = hotkey_str
        return True
