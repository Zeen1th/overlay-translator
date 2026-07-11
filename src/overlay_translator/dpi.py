import ctypes

# Windows DPI awareness context: PER_MONITOR_AWARE_V2
_PER_MONITOR_AWARE_V2 = -4


def enable_dpi_awareness(user32=None) -> bool:
    """Make the process per-monitor DPI-aware (Windows) so tkinter reports and
    uses PHYSICAL pixels. Must run BEFORE any Tk window is created. Returns True
    on success; safely returns False on non-Windows or if the call fails."""
    if user32 is None:
        windll = getattr(ctypes, "windll", None)
        if windll is None:
            return False
        user32 = windll.user32
    try:
        return bool(
            user32.SetProcessDpiAwarenessContext(
                ctypes.c_void_p(_PER_MONITOR_AWARE_V2)
            )
        )
    except Exception:
        return False
