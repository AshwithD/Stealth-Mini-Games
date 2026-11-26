"""Shared constants: colors, key maps, SDL/window flags.

Kept in one place so the renderer and all games share the same visual
language and control scheme.
"""
import pygame

# ----------------------------------------------------------------------
# Window / rendering
# ----------------------------------------------------------------------
try:
    NOFRAME = pygame.NOFRAME
except AttributeError:
    NOFRAME = 0x00000008

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002

CANVAS = 360          # internal render resolution (~3x the window)

# ----------------------------------------------------------------------
# Colors
# ----------------------------------------------------------------------
BG     = (23, 25, 31)     # window background
FG     = (236, 239, 246)  # primary text / foreground
DIM    = (120, 128, 140)  # secondary text / hints
ACCENT = (88, 198, 255)   # highlights, selection
GREEN  = (72, 222, 120)   # success / snake / pipes
RED    = (242, 92, 92)    # danger / food / game over
YELLOW = (246, 202, 92)   # bonus / warnings
PANEL  = (38, 42, 52)     # button / card fill
FRAME  = (96, 106, 128)   # window border
MUTED  = (52, 56, 66)     # play-field panel
GRID_D = (44, 48, 58)     # empty 2048 cells / ground

# 2048 tile palette by value
TILE_COLORS = {
    2: (230, 232, 238), 4: (216, 208, 192),
    8: (246, 194, 128), 16: (240, 146, 96),
    32: (236, 106, 84), 64: (230, 84, 74),
    128: (238, 132, 166), 256: (236, 116, 186),
    512: (232, 100, 206), 1024: (228, 92, 226),
    2048: (250, 176, 84), 4096: (250, 156, 64),
}

# ----------------------------------------------------------------------
# Movement key map: key -> (dr, dc)
# ----------------------------------------------------------------------
MOVE_KEYS = {
    pygame.K_UP: (-1, 0), pygame.K_DOWN: (1, 0),
    pygame.K_LEFT: (0, -1), pygame.K_RIGHT: (0, 1),
    pygame.K_w: (-1, 0), pygame.K_s: (1, 0),
    pygame.K_a: (0, -1), pygame.K_d: (0, 1),
}
