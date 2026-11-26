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


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


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
    user32.GetCursorPos.argtypes = [ctypes.POINTER(_POINT)]
    user32.GetCursorPos.restype = ctypes.c_int
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


def cursor_pos():
    """Absolute screen cursor position via Win32 GetCursorPos.

    Used for dragging: MOUSEMOTION events stop being delivered once the
    borderless window moves out from under the cursor, but Win32 can
    always report the absolute cursor position. This lets us follow the
    cursor smoothly for the whole drag.
    """
    if _USER32 is not None:
        try:
            p = _POINT()
            if _USER32.GetCursorPos(ctypes.byref(p)):
                return int(p.x), int(p.y)
        except Exception:
            pass
    # fallback (non-Windows / test): use pygame's mouse position
    try:
        mx, my = pygame.mouse.get_pos()
        # add the window offset so it is screen-absolute
        wx, wy = window_position()
        return wx + mx, wy + my
    except Exception:
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
    """Press -> threshold -> drag -> release, with click detection.

    Dragging is driven by **polling the absolute cursor position** every
    frame (Win32 GetCursorPos) rather than relying on MOUSEMOTION events.
    When a borderless window moves, it slides out from under the cursor
    and SDL stops delivering mouse-motion events, which makes event-based
    dragging stutter or stop. Polling the OS cursor position bypasses that
    entirely: the window always follows the cursor smoothly for the whole
    drag, regardless of where the window ends up.

    The window is positioned by **absolute** coordinates (cursor minus the
    grab offset) so it tracks the cursor exactly, with no drift.
    """

    def __init__(self, threshold=DRAG_THRESHOLD):
        self.threshold = threshold
        self.pressed = False
        self.dragging = False
        self._press_pos = None      # cursor screen position at press
        self._win_pos = None        # window screen position at press
        self._grab_dx = 0           # cursor.x - window.x at press
        self._grab_dy = 0           # cursor.y - window.y at press
        self._moved = False         # has the cursor moved past threshold

    # ------------------------------------------------------------------
    def on_press(self, pos):
        """Left mouse pressed: remember, but do not act yet."""
        self.pressed = True
        self.dragging = False
        self._moved = False
        # capture the absolute cursor position and the window position.
        # Prefer the event-provided pos (accurate + testable); on Windows
        # tick() re-polls the real cursor for smooth dragging.
        self._press_pos = pos
        self._win_pos = window_position()
        # grab offset: where the cursor sits relative to the window, so
        # the window follows the cursor with the same offset throughout
        self._grab_dx = self._press_pos[0] - self._win_pos[0]
        self._grab_dy = self._press_pos[1] - self._win_pos[1]

    def on_move(self, pos):
        """Mouse moved (event-based): track movement for click detection.

        The actual window moving during a drag is done by ``tick()``,
        which polls the absolute cursor position. This handler only
        decides click-vs-drag from the movement seen in events.
        """
        if not self.pressed:
            return False
        if not self._moved:
            dx = pos[0] - self._press_pos[0]
            dy = pos[1] - self._press_pos[1]
            if dx * dx + dy * dy > self.threshold * self.threshold:
                self._moved = True
                self.dragging = True
        return self.dragging

    def tick(self):
        """Called every frame while pressed: drive the window from the cursor.

        Polls the absolute cursor position and moves the window so the
        grab offset is preserved. This keeps the drag smooth even when the
        window has moved far from the cursor (where MOUSEMOTION stops).
        On non-Windows / in tests without a real cursor, this is a no-op
        for the click-vs-drag decision (handled by on_move).
        """
        if not self.pressed:
            return
        if self._moved and self.dragging:
            cur = cursor_pos()
            nx = cur[0] - self._grab_dx
            ny = cur[1] - self._grab_dy
            move_window_to(nx, ny)
            self._win_pos = (nx, ny)

    def on_release(self, pos):
        """Left mouse released: True if this was a click, False if a drag."""
        was_click = self.pressed and not self.dragging
        self.pressed = False
        self.dragging = False
        self._moved = False
        self._press_pos = None
        self._win_pos = None
        self._grab_dx = 0
        self._grab_dy = 0
        return was_click

    # ------------------------------------------------------------------
    def cancel(self):
        """Drop any pending press (e.g. on state change)."""
        self.pressed = False
        self.dragging = False
        self._moved = False
        self._press_pos = None
        self._win_pos = None
        self._grab_dx = 0
        self._grab_dy = 0
