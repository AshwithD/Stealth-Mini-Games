"""Input handling: mouse click-vs-drag disambiguation and window moving.

The window is borderless, so it has no title bar to drag. This module
implements a drag controller with a movement threshold:

- press left mouse anywhere  -> remember the press
- move beyond DRAG_THRESHOLD  -> it's a drag: the window follows the cursor
- release without moving      -> it's a click: normal game/menu action

This makes dragging work in every state (menu and games) while clicks keep
working exactly as before.

Window movement uses **SDL's native window-position API**
(``pygame.display.get_window_position`` / ``set_window_position``) as the
primary, reliable path. It needs NO window handle and NO ctypes, so it works
even when ``pygame.display.get_window_handle()`` returns an invalid value on
some Windows builds with borderless windows. Win32 ``SetWindowPos`` is kept
only as a secondary fallback and for the always-on-top toggle (which SDL does
not expose). On non-Windows platforms the Win32 calls are no-ops.
"""
import sys

import pygame

from .constants import SWP_NOSIZE, SWP_NOMOVE

DRAG_THRESHOLD = 6  # pixels (window space) before press becomes a drag

# Win32 constants (used only for the fallback / always-on-top)
HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SM_CYVIRTUALSCREEN = 79


def _user32():
    """Return ctypes user32 with proper signatures (Windows only)."""
    if not sys.platform.startswith("win"):
        return None
    import ctypes

    user32 = ctypes.windll.user32
    # HWND is a pointer -> c_void_p; everything else is int/uint
    user32.SetWindowPos.argtypes = [
        ctypes.c_void_p, ctypes.c_int,  # hWnd, hWndInsertAfter
        ctypes.c_int, ctypes.c_int,      # x, y
        ctypes.c_int, ctypes.c_int,      # cx, cy
        ctypes.c_uint,                   # uFlags
    ]
    user32.SetWindowPos.restype = ctypes.c_int
    user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    user32.GetSystemMetrics.restype = ctypes.c_int
    return user32


_USER32 = _user32()


def _handle():
    """The window handle as a c_void_p-compatible value, or None."""
    try:
        h = pygame.display.get_window_handle()
    except Exception:
        return None
    if not h:
        return None
    return h


def window_position():
    """Current screen position of the window as (x, y).

    Uses SDL's get_window_position (no handle needed). Falls back to the
    Win32 GetWindowRect, then to (0, 0).
    """
    try:
        pos = pygame.display.get_window_position()
        if pos is not None:
            return int(pos[0]), int(pos[1])
    except Exception:
        pass
    if _USER32 is not None:
        try:
            import ctypes

            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                            ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            h = _handle()
            if h is not None:
                r = RECT()
                if _USER32.GetWindowRect(h, ctypes.byref(r)):
                    return r.left, r.top
        except Exception:
            pass
    return 0, 0


def move_window_to(x, y):
    """Move the window to screen (x, y) without resizing it.

    Primary: SDL set_window_position (reliable, no handle). Secondary:
    Win32 SetWindowPos. Neither ever resizes the window.
    """
    # Primary - SDL native, works even with an invalid HWND
    try:
        pygame.display.set_window_position(int(x), int(y))
        return
    except Exception:
        pass
    # Secondary - Win32 fallback
    if _USER32 is not None:
        try:
            h = _handle()
            if h is not None and _USER32.SetWindowPos(
                    h, HWND_TOP, int(x), int(y), 0, 0, SWP_NOSIZE):
                return
        except Exception:
            pass


def set_topmost(flag):
    """Toggle always-on-top (HWND_TOPMOST / HWND_NOTOPMOST).

    SDL does not expose always-on-top, so this needs Win32 SetWindowPos.
    """
    if _USER32 is not None:
        try:
            h = _handle()
            if h is not None:
                _USER32.SetWindowPos(h, HWND_TOPMOST if flag else HWND_NOTOPMOST,
                                     0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE)
        except Exception:
            pass


def move_to_bottom_left(window_size):
    """Place the window at the bottom-left corner of the virtual screen."""
    # screen height via a system call (no window handle needed)
    sy = None
    if _USER32 is not None:
        try:
            sy = _USER32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        except Exception:
            sy = None
    if sy is None:
        try:
            sy = pygame.display.Info().current_h
        except Exception:
            sy = window_size
    y = max(0, sy - window_size)
    move_window_to(0, y)


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
        # SDL gives the real window position with no handle dependency
        self._win_pos = window_position()

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
            # move by the same delta the cursor moved, from the window's
            # real screen position -> the window follows the cursor exactly
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
