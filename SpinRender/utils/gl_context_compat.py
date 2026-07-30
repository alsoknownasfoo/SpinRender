"""
Compatibility shim for PyOpenGL's per-context array-pointer bookkeeping.

PyOpenGL's client-side array calls (glVertexPointer, glNormalPointer, ...)
ask OpenGL.contextdata to remember which numpy array backs the pointer, so
it isn't garbage-collected while the GL still holds a raw pointer to it.
That bookkeeping is keyed by "the current GL context", which contextdata
determines by asking OpenGL.platform.GetCurrentContext() (a ctypes call
into the platform GL library, e.g. glXGetCurrentContext on Linux).

On at least one tested Linux/aarch64 build, that platform call returns a
falsy value even though wx's SetCurrent() has genuinely made a context
current - contextdata then raises "Attempt to retrieve context when no
valid context", and every vertex-array draw call is silently dropped.

Since SpinRender's mesh arrays are held for the lifetime of the loaded
model (SpinRenderPanel.mesh_data), rather than created fresh and discarded
each frame, the array-liveness guarantee this bookkeeping exists to
provide is already satisfied by our own object graph - the bookkeeping
itself is redundant for us. This patches contextdata.getContext() to fall
back to a fixed dummy id instead of raising when the platform lookup
fails, so the array-pointer wrapper can proceed normally.
"""
import logging

logger = logging.getLogger("SpinRender")

_PATCHED = False
_FALLBACK_CONTEXT_ID = 1


def patch_context_lookup():
    """Idempotently patch OpenGL.contextdata.getContext with a fallback."""
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    from OpenGL import contextdata, platform

    def _get_context_or_fallback(context=None):
        if context is None:
            context = platform.GetCurrentContext()
            if not context:
                context = _FALLBACK_CONTEXT_ID
        return context

    contextdata.getContext = _get_context_or_fallback
    logger.debug("gl_context_compat: patched OpenGL.contextdata.getContext with fallback id")
