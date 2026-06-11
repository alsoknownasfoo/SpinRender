"""Exception guard for wx EVT_PAINT handlers.

An exception escaping a paint handler is far worse than a drawing glitch:
wxPython reports it via PyErr_Print, which stores the traceback in
sys.last_traceback. That traceback keeps the handler's frame — and the
wx.(Auto)BufferedPaintDC local in it — alive past the handler. When the
window is later destroyed and the trapped DC finally gets garbage-collected,
~wxBufferedPaintDC blits its buffer into the dead window and the host app
(KiCad) dies with an access violation (0xc0000005).

Wrapping handlers with @guarded_paint keeps the exception inside the
handler: it is logged to the SpinRender log, and the DC is released at
handler exit while the window still exists.
"""
import functools
import logging

logger = logging.getLogger("SpinRender")


def guarded_paint(handler):
    """Decorator for EVT_PAINT handlers: log exceptions instead of leaking
    them (and the paint DC) into sys.last_traceback."""
    @functools.wraps(handler)
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except Exception:
            logger.exception(f"Paint handler {handler.__qualname__} failed")
    return wrapper
