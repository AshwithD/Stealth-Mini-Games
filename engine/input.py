"""Input handling: mouse click-vs-drag disambiguation and window moving.

The window is borderless, so it has no title bar to drag. This module
implements a drag controller with a movement threshold:

- press left mouse anywhere  -> remember the press
- move beyond DRAG_THRESHOLD  -> it's a drag: the window follows the cursor
- release without moving      -> it's a click: normal game/menu action

This makes dragging work in every state (menu and games) while clicks keep
working exactly as before.

Window movement is layered for maximum reliability on Windows. Different
SDL/pygame builds expose window positioning differently, and a borderless
window's handle is not always obtainable, so ``move_window_to`` tries every
available method until one succeeds:

1. SDL native ``pygame.display.set_window_position``
2. Win32 ``SetWindowPos`` using the handle from ``get_window_handle()``
3. Win32 ``FindWindowW`` by caption + ``SetWindowPos`` (handle-independent)
4. SDL2 ``SDL_SetWindowPosition`` via ctypes on the SDL2 DLL

On non-Windows platforms the Win32 calls are no-ops.
"""
import ctypes
import sys

import pygame

from .constants import SWP_NOSIZE, SWP_NOMOVE

DRAG_THRESHOLD = 6  # pixels (window space) before press becomes a drag

# Win32 constants
HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SM_CYVIRTUALSCREEN = 79

# The window caption used to locate the window via FindWindowW
WINDOW_CAPTION = "Mini Games"


def _user32():
    """Return ctypes user32 with proper signatures (Windows only)."""
    if not sys.platform.startswith("win"):
        return None
    user32 = ctypes.windll.user32
    user32.SetWindowPos.argtypes = [
        ctypes.c_void_p, ctypes.c_int,
        ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int,
        ctypes.c_uint,
    ]
    user32.SetWindowPos.restype = ctypes.c_int
    user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    user32.GetSystemMetrics.restype = ctypes.c_int
    user32.FindWindowW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    user32.FindWindowW.restype = ctypes.c_void_p
    return user32


_USER32 = _user32()


def _handle():
    """The window handle from pygame, or None."""
    try:
        h = pygame.display.get_window_handle()
    except Exception:
        return None
    if not h:
        return None
    return h


def _handle_by_caption():
    """Find the window by caption via FindWindowW (handle-independent)."""
    if _USER32 is None:
        return None
    try:
        h = _USER32.FindWindowW(None, WINDOW_CAPTION)
        if h:
            return h
    except Exception:
        pass
    return None


def window_position():
    """Current screen position of the window as (x, y).

    Tries SDL first, then Win32 GetWindowRect on either handle source.
    Falls back to (0, 0).
    """
    try:
        pos = pygame.display.get_window_position()
        if pos is not None:
            return int(pos[0]), int(pos[1])
    except Exception:
        pass
    if _USER32 is not None:
        try:
            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                            ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            for h in (_handle(), _handle_by_caption()):
                if h:
                    r = RECT()
                    if _USER32.GetWindowRect(h, ctypes.byref(r)):
                        return r.left, r.top
        except Exception:
            pass
    return 0, 0


def _set_window_pos(h, x, y):
    """Low-level Win32 SetWindowPos on a given handle."""
    return bool(_USER32.SetWindowPos(h, HWND_TOP, int(x), int(y),
                                     0, 0, SWP_NOSIZE))


def move_window_to(x, y):
    """Move the window to screen (x, y) without resizing it.

    Win32 SetWindowPos is tried FIRST because it is synchronous and smooth
    (SDL's set_window_position can stutter/lag on some builds, which makes
    dragging feel jerky). Tries every available method until one succeeds.
    Never resizes.
    """
    x, y = int(x), int(y)

    # 1. Win32 SetWindowPos via caption-found handle (handle-independent,
    #    fast + synchronous -> smooth drag)
    if _USER32 is not None:
        h = _handle_by_caption()
        if h and _set_window_pos(h, x, y):
            return True

    # 2. Win32 SetWindowPos via pygame handle
    if _USER32 is not None:
        h = _handle()
        if h and _set_window_pos(h, x, y):
            return True

    # 3. SDL native (fallback - can be laggy on some builds)
    try:
        pygame.display.set_window_position(x, y)
        return True
    except Exception:
        pass

    # 4. SDL2 SDL_SetWindowPosition via ctypes
    try:
        _sdl_set_window_position(x, y)
        return True
    except Exception:
        pass
    return False


def _sdl_set_window_position(x, y):
    """Call SDL_SetWindowPosition directly via ctypes on the SDL2 DLL."""
    if sys.platform.startswith("win"):
        sdl2 = ctypes.CDLL("SDL2.dll")
        sdl2.SDL_SetWindowPosition.argtypes = [ctypes.c_void_p,
                                               ctypes.c_int, ctypes.c_int]
        sdl2.SDL_SetWindowPosition.restype = ctypes.c_int
        h = _handle() or _handle_by_caption()
        if h:
            sdl2.SDL_SetWindowPosition(h, x, y)
    else:
        pygame.display.set_window_position(x, y)


def set_topmost(flag):
    """Toggle always-on-top (HWND_TOPMOST / HWND_NOTOPMOST)."""
    if _USER32 is not None:
        for h in (_handle(), _handle_by_caption()):
            if h:
                try:
                    _USER32.SetWindowPos(h, HWND_TOPMOST if flag
                                         else HWND_NOTOPMOST,
                                         0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE)
                    return
                except Exception:
                    pass


def move_to_bottom_left(window_size):
    """Place the window at the bottom-left corner of the virtual screen."""
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
    return move_window_to(0, y)


class DragController:
    """Press -> threshold -> drag -> release, with click detection."""

    def __init__(self, threshold=DRAG_THRESHOLD):
        self.threshold = threshold
        self.pressed = False
        self.dragging = False
        self._press_pos = None      # mouse position at press
        self._last_pos = None       # last mouse position seen
        self._win_pos = None        # window screen position at press

    # ------------------------------------------------------------------
    def on_press(self, pos):
        """Left mouse pressed: remember, but do not act yet."""
        self.pressed = True
        self.dragging = False
        self._press_pos = pos
        self._last_pos = pos
        # capture the window's real screen position (best effort)
        self._win_pos = window_position()

    def on_move(self, pos):
        """Mouse moved: start dragging once past the threshold, then follow.

        Uses incremental deltas (movement since the last event) so the
        window follows the cursor smoothly, independent of how accurate
        the initial position capture was.
        """
        if not self.pressed or self.dragging:
            return False
        if self._last_pos is None or self._win_pos is None:
            return False
        # movement since the last event
        dx = pos[0] - self._last_pos[0]
        dy = pos[1] - self._last_pos[1]
        self._last_pos = pos
        if not self.dragging:
            # still below threshold: accumulate, do not move yet
            total_dx = pos[0] - self._press_pos[0]
            total_dy = pos[1] - self._press_pos[1]
            if total_dx * total_dx + total_dy * total_dy <=                     self.threshold * self.threshold:
                return False
            self.dragging = True
        # move by the incremental delta from the current window position
        move_window_to(self._win_pos[0] + dx, self._win_pos[1] + dy)
        self._win_pos = (self._win_pos[0] + dx, self._win_pos[1] + dy)
        return self.dragging

    def on_release(self, pos):
        """Left mouse released: True if this was a click, False if a drag."""
        was_click = self.pressed and not self.dragging
        self.pressed = False
        self.dragging = False
        self._press_pos = None
        self._last_pos = None
        self._win_pos = None
        return was_click

    # ------------------------------------------------------------------
    def cancel(self):
        """Drop any pending press (e.g. on state change)."""
        self.pressed = False
        self.dragging = False
        self._press_pos = None
        self._last_pos = None
        self._win_pos = None
