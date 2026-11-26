"""Input handling: mouse click-vs-drag disambiguation and window moving.

The window is borderless, so it has no title bar to drag. This module
implements a drag controller with a movement threshold:

- press left mouse anywhere  -> remember the press
- move beyond DRAG_THRESHOLD  -> it's a drag: the window follows the cursor
- release without moving      -> it's a click: normal game/menu action

This makes dragging work in every state (menu and games) while clicks keep
working exactly as before.

Window movement uses Win32 SetWindowPos (borderless windows can still be
moved programmatically); on non-Windows platforms the calls are no-ops.
"""
import sys

import pygame

from .constants import SWP_NOSIZE, SWP_NOMOVE

DRAG_THRESHOLD = 6  # pixels (window space) before press becomes a drag


def window_rect():
    """Return (left, top) of the window on Windows, else None."""
    if not sys.platform.startswith("win"):
        return None
    try:
        import ctypes

        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        user32 = ctypes.windll.user32
        r = RECT()
        user32.GetWindowRect(pygame.display.get_window_handle(), ctypes.byref(r))
        return r.left, r.top
    except Exception:
        return None


def move_window_to(x, y):
    """Move the window to screen (x, y) without resizing it."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        user32 = ctypes.windll.user32
        user32.SetWindowPos(pygame.display.get_window_handle(), 0,
                            int(x), int(y), 0, 0, SWP_NOSIZE)
    except Exception:
        pass


def set_topmost(flag):
    """Toggle always-on-top (HWND_TOPMOST / HWND_NOTOPMOST)."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        user32 = ctypes.windll.user32
        z = -1 if flag else -2
        user32.SetWindowPos(pygame.display.get_window_handle(), z,
                            0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE)
    except Exception:
        pass


def move_to_bottom_left(window_size):
    """Place the window at the bottom-left corner of the virtual screen."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            user32 = ctypes.windll.user32
            sy = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
            user32.SetWindowPos(pygame.display.get_window_handle(), 0,
                                0, max(0, sy - window_size), 0, 0, SWP_NOSIZE)
            return
        except Exception:
            pass
    else:
        try:
            pygame.display.set_window_position(0, 0)
        except Exception:
            pass


class DragController:
    """Press -> threshold -> drag -> release, with click detection."""

    def __init__(self, threshold=DRAG_THRESHOLD):
        self.threshold = threshold
        self.pressed = False
        self.dragging = False
        self._press_pos = None
        self._win_pos = None

    # ------------------------------------------------------------------
    def on_press(self, pos):
        """Left mouse pressed: remember, but do not act yet."""
        self.pressed = True
        self.dragging = False
        self._press_pos = pos
        # On non-Windows platforms window_rect() is None; fall back to a
        # virtual origin so the press/drag state machine still tracks.
        self._win_pos = window_rect() or (0, 0)

    def on_move(self, pos):
        """Mouse moved: start dragging once past the threshold."""
        if not self.pressed or self.dragging:
            return False
        if self._press_pos is None or self._win_pos is None:
            return False
        dx = pos[0] - self._press_pos[0]
        dy = pos[1] - self._press_pos[1]
        if dx * dx + dy * dy > self.threshold * self.threshold:
            self.dragging = True
            move_window_to(self._win_pos[0] + dx, self._win_pos[1] + dy)
        return self.dragging

    def on_release(self, pos):
        """Left mouse released: True if this was a click, False if a drag."""
        was_click = self.pressed and not self.dragging
        self.pressed = False
        self.dragging = False
        self._press_pos = None
        self._win_pos = None
        return was_click

    # ------------------------------------------------------------------
    def cancel(self):
        """Drop any pending press (e.g. on state change)."""
        self.pressed = False
        self.dragging = False
        self._press_pos = None
        self._win_pos = None
