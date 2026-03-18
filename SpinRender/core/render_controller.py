"""Render Controller - orchestrates render workflow and progress reporting.

This component encapsulates all render orchestration logic, separating
it from UI concerns (SpinRenderPanel). It manages the RenderEngine instance,
background thread, cancellation, and progress tracking.

Architecture:
- Core layer (no wx dependencies)
- Uses callbacks to communicate back to UI layer
- Thread-safe with wx.CallAfter wrapping in UI callbacks
"""
import threading
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger("SpinRender")

try:
    from .settings import RenderSettings
    from .renderer import RenderEngine
except ImportError:
    # For backward compatibility, allow None types
    RenderSettings = Any
    RenderEngine = Any


class RenderController:
    """
    Controls render execution: start, cancel, progress tracking, completion.
    Designed to be owned by SpinRenderPanel (or any UI controller).
    """

    def __init__(self):
        """Initialize render controller."""
        self._engine: Optional[RenderEngine] = None
        self._thread: Optional[threading.Thread] = None
        self._cancel_flag = False
        self._is_rendering = False

        # Callbacks set by owner
        self.on_progress: Optional[Callable[[int, int, str, Optional[str]], None]] = None
        self.on_complete: Optional[Callable[[Any, Optional[str]], None]] = None

    def is_rendering(self) -> bool:
        """Check if a render is currently in progress."""
        return self._is_rendering

    def start_render(self, board_path: str, settings: RenderSettings,
                     progress_cb: Optional[Callable[[int, int, str, Optional[str]], None]] = None,
                     complete_cb: Optional[Callable[[Any, Optional[str]], None]] = None):
        """
        Start render in background thread.

        Args:
            board_path: Path to the KiCad PCB file
            settings: RenderSettings with render parameters
            progress_cb: Called with (current, total, message, frame_path=None)
            complete_cb: Called with (result, error=None) on completion
        """
        if self._is_rendering:
            logger.warning("Render already in progress - ignoring start request")
            return

        self._is_rendering = True
        self._cancel_flag = False
        self.on_progress = progress_cb
        self.on_complete = complete_cb

        def run_render():
            try:
                # Convert RenderSettings to dict for RenderEngine compatibility
                settings_dict = settings.to_dict() if hasattr(settings, 'to_dict') else dict(settings)
                self._engine = RenderEngine(board_path, settings_dict, progress_callback=self._on_internal_progress)
                result = self._engine.render()
                if self._cancel_flag:
                    # Render was cancelled - treat as stopped, not error
                    self._finish(None, None)
                else:
                    self._finish(result, None)
            except Exception as e:
                logger.error(f"Render error: {e}", exc_info=True)
                self._finish(None, str(e))

        self._thread = threading.Thread(target=run_render, daemon=True)
        self._thread.start()

    def cancel(self):
        """Request cancellation of current render."""
        if not self._is_rendering:
            return

        self._cancel_flag = True
        if self._engine:
            try:
                self._engine.cancel()
            except Exception as e:
                logger.error(f"Error cancelling render: {e}")

        # Thread will exit via self._finish() callback

    def _on_internal_progress(self, current: int, total: int, message: str, frame_path: Optional[str] = None):
        """
        Internal progress callback from RenderEngine.
        Forwards to owner's progress callback if set.
        """
        if self.on_progress:
            try:
                self.on_progress(current, total, message, frame_path)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}", exc_info=True)

    def _finish(self, result, error: Optional[str]):
        """
        Internal: Mark render complete and call owner's completion callback.
        Uses wx.CallAfter if available in the caller's context.
        """
        self._is_rendering = False
        self._engine = None
        self._thread = None

        if self.on_complete:
            try:
                # Try to use wx.CallAfter if we're in a wx context
                import wx
                wx.CallAfter(self.on_complete, result, error)
            except ImportError:
                # Not in wx context - call directly (e.g., during tests)
                try:
                    self.on_complete(result, error)
                except Exception as e:
                    logger.error(f"Error in complete callback: {e}", exc_info=True)
