"""Menu and stats screens.

The menu is a 3x3 grid: the 7 games plus STATS and QUIT cells. Every cell
shows a number hint, a simple icon and a short label - designed to stay
readable at a ~3 cm window size.
"""
import pygame

from .constants import BG, FG, DIM, ACCENT, RED, GREEN, PANEL, FRAME

GRID_COLS, GRID_ROWS = 3, 3
CELL_GAP = 10
MARGIN = 18


def menu_cells(canvas_size):
    """Return list of (key, rect, label, icon, kind) for the 3x3 grid.

    The grid is centered in the full canvas (no title, no border), so it
    fills the window cleanly and stays aligned.
    """
    top_reserve = 24      # small top margin (no title anymore)
    bottom_reserve = 56   # room for the control hints at the bottom
    usable = canvas_size - top_reserve - bottom_reserve
    cell_h = (usable - (GRID_ROWS - 1) * CELL_GAP) // GRID_ROWS
    cell_w = (canvas_size - 2 * MARGIN - (GRID_COLS - 1) * CELL_GAP) // GRID_COLS
    cells = []
    for i in range(GRID_ROWS):
        for j in range(GRID_COLS):
            idx = i * GRID_COLS + j
            if idx >= 9:
                break
            x = MARGIN + j * (cell_w + CELL_GAP)
            y = top_reserve + i * (cell_h + CELL_GAP)
            if idx < 7:
                cells.append((str(idx + 1), pygame.Rect(x, y, cell_w, cell_h),
                              None, None, "game"))
            elif idx == 7:
                cells.append(("8", pygame.Rect(x, y, cell_w, cell_h),
                              "STATS", "stats", "stats"))
            else:
                cells.append(("9", pygame.Rect(x, y, cell_w, cell_h),
                              "QUIT", "quit", "quit"))
    return cells


def draw_icon(canvas, R, kind, cx, cy):
    """Draw a small game/screen icon centered at (cx, cy)."""
    if kind == "snake":
        for i, (dx, dy) in enumerate([(-10, -5), (0, 0), (10, 5)]):
            col = (120, 240, 160) if i == 0 else (46, 168, 88)
            R.circle(canvas, (cx + dx, cy + dy), 6, col)
    elif kind == "type":
        s = R.text(24, True, "Aa", DIM)
        R.blit_center(canvas, s, cx, cy)
    elif kind == "grid":
        for i in range(2):
            for j in range(2):
                col = [(230, 232, 238), (216, 208, 192),
                       (44, 48, 58), (248, 180, 110)][i * 2 + j]
                R.rr(canvas, (cx - 11 + i * 13, cy - 11 + j * 13, 10, 10),
                     col, radius=3)
    elif kind == "flap":
        R.rr(canvas, (cx - 11, cy - 7, 22, 14), (246, 202, 92), radius=7)
    elif kind == "memory":
        for i in range(2):
            for j in range(2):
                R.rr(canvas, (cx - 13 + i * 14, cy - 13 + j * 14, 10, 10),
                     PANEL if (i + j) % 2 else (90, 96, 108), radius=3)
    elif kind == "react":
        R.circle(canvas, (cx, cy), 11, (246, 202, 92))
        R.circle(canvas, (cx, cy), 4, FG)
    elif kind == "break":
        R.rr(canvas, (cx - 13, cy - 8, 26, 4), (248, 180, 110), radius=2)
        R.rr(canvas, (cx - 13, cy + 4, 26, 4), (246, 142, 98), radius=2)
        R.rr(canvas, (cx - 4, cy - 3, 8, 8), (234, 82, 72), radius=2)
    elif kind == "stats":
        for i, h in enumerate([10, 16, 12]):
            R.rr(canvas, (cx - 14 + i * 10, cy + 6 - h, 7, h),
                 (88, 198, 255) if i != 1 else (72, 222, 120), radius=2)
    elif kind == "quit":
        R.rr(canvas, (cx - 11, cy - 10, 22, 20), PANEL, radius=4)
        s = R.text(20, True, "X", RED)
        R.blit_center(canvas, s, cx, cy)


def draw_menu(canvas, R, meta, hover, store):
    """meta: list of (key, name, label, icon, desc) from the games registry."""
    R.clear(canvas)
    w = R.canvas_size
    # no title text (stealth) - grid fills the canvas cleanly
    meta_by_key = {m[0]: m for m in meta}
    for key, rect, label, icon, kind in menu_cells(w):
        if kind == "game":
            _, _, lbl, ic, _ = meta_by_key[key]
            label, icon = lbl, ic
        sel = hover is not None and rect.collidepoint(hover)
        border = RED if kind == "quit" else (ACCENT if kind == "stats" else DIM)
        fill = (60, 24, 24) if kind == "quit" else (PANEL if kind != "stats"
                                                   else (24, 40, 52))
        R.rr(canvas, rect, fill, radius=12)
        R.rr(canvas, rect, ACCENT if sel else border, radius=12, width=4)
        n = R.text(20, True, key, (160, 170, 186) if not sel else BG)
        R.blit(canvas, n, (rect.x + 10, rect.y + 8))
        draw_icon(canvas, R, icon, rect.x + rect.w // 2, rect.y + 30)
        l = R.text(20, True, label, BG if sel else FG)
        R.blit_center(canvas, l, rect.x + rect.w // 2, rect.y + 58)
    h1 = R.text(23, False, "1-9 / CLICK    ESC = QUIT", DIM)
    R.blit_center(canvas, h1, w // 2, w - 44)
    h2 = R.text(21, False, "drag to move    right-click quits", DIM)
    R.blit_center(canvas, h2, w // 2, w - 22)
    R.finish(canvas)


def draw_stats(canvas, R, store, meta):
    """Stats screen: per-game best / plays / wins + totals."""
    R.clear(canvas)
    w = R.canvas_size
    s = R.text(44, True, "STATS", FG)
    R.blit_center(canvas, s, w // 2, 30)
    meta_by_key = {m[0]: m for m in meta}
    rows = store.summary()
    y = 78
    for key, best, plays, wins in rows:
        name = meta_by_key.get(key, (key, key, key, "", ""))[2]
        suffix = " moves" if key == "5" else ""
        lbl = R.text(26, True, f"{name}", FG)
        R.blit(canvas, lbl, (26, y - 14))
        best_s = R.text(24, False, f"best {best}{suffix}", ACCENT)
        R.blit(canvas, best_s, (150, y - 13))
        p_s = R.text(22, False, f"plays {plays}", DIM)
        R.blit(canvas, p_s, (26, y + 14))
        w_s = R.text(22, False, f"wins {wins}", GREEN if wins else DIM)
        R.blit(canvas, w_s, (150, y + 15))
        y += 58
    if not rows:
        hint = R.text(24, False, "no games played yet", DIM)
        R.blit_center(canvas, hint, w // 2, 150)
    tot = R.text(28, True, f"TOTAL {store.total_score}", FG)
    R.blit_center(canvas, tot, w // 2, w - 44)
    back = R.text(21, False, "press Esc / click back", DIM)
    R.blit_center(canvas, back, w // 2, w - 22)
    R.finish(canvas)
