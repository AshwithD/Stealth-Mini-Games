"""Game 3: 2048 with undo and slide/merge animations.

Deepened mechanics:
- Full 2048 rules (slide, merge, spawn 2/4, game-over detection).
- **Undo** (U key): the last 20 moves can be reverted (grid + score).
- **Animations**: moved tiles slide to their destination, merged tiles pop,
  new tiles scale in - all interpolated over a few frames.
- Victory when a 2048 tile is created (the game continues; stats record it).
"""
import copy
import random

import pygame

from ..constants import BG, FG, DIM, GRID_D, TILE_COLORS, MOVE_KEYS
from .base import GameBase

ANIM_DUR = 22         # frames for slide/merge animation (slow, smooth)
UNDO_LIMIT = 20


class Game2048(GameBase):
    KEY = "3"
    NAME = "2048"
    LABEL = "2048"
    ICON = "grid"
    DESC = "Slide and merge tiles, reach 2048 (U = undo)"

    def __init__(self):
        super().__init__()
        self.gap = 10
        self.tile = 64
        self.ox = 16
        self.oy = 48
        self.reset()

    def reset(self):
        self.grid = [[0] * 4 for _ in range(4)]
        self.score = 0
        self.max_tile = 0
        self.over = False
        self.done = False
        self.won = False
        self.anim = None          # {"t", "dur", "tiles": [...]}
        self.history = []         # [(grid, score, max_tile), ...]
        self.add_tile()
        self.add_tile()

    # ------------------------------------------------------------------
    # Spawning
    # ------------------------------------------------------------------
    def add_tile(self):
        cells = [(r, c) for r in range(4) for c in range(4) if self.grid[r][c] == 0]
        if not cells:
            return None
        r, c = random.choice(cells)
        self.grid[r][c] = 2 if random.random() < 0.9 else 4
        self.max_tile = max(self.max_tile, self.grid[r][c])
        return (r, c, self.grid[r][c])

    # ------------------------------------------------------------------
    # Sliding logic (with move tracking for animations)
    # ------------------------------------------------------------------
    def _slide_line(self, slots, values):
        """Slide one line toward slot 0.

        slots: list of (r, c) in traversal order (slot 0 = destination side)
        values: aligned tile values
        Returns (out_values, out_src, out_merge): for each output slot, the
        value, the source slot index, and whether it was a merge.
        """
        nonzero = [(i, v) for i, v in enumerate(values) if v]
        out_values, out_src, out_merge = [], [], []
        i = 0
        while i < len(nonzero):
            if i + 1 < len(nonzero) and nonzero[i][1] == nonzero[i + 1][1]:
                v = nonzero[i][1] * 2
                self.score += v
                out_values.append(v)
                out_src.append(nonzero[i][0])
                out_merge.append(True)
                i += 2
            else:
                out_values.append(nonzero[i][1])
                out_src.append(nonzero[i][0])
                out_merge.append(False)
                i += 1
        while len(out_values) < len(slots):
            out_values.append(0)
            out_src.append(-1)
            out_merge.append(False)
        return out_values, out_src, out_merge

    def move(self, dr, dc):
        if self.over or self.anim:
            return False
        prev = copy.deepcopy(self.grid)
        prev_score = self.score
        moves = []

        if dr == -1:      # up
            for c in range(4):
                slots = [(r, c) for r in range(4)]
                values = [self.grid[r][c] for r in range(4)]
                out_v, out_src, out_m = self._slide_line(slots, values)
                for j, v in enumerate(out_v):
                    if v:
                        moves.append({"from": slots[out_src[j]], "to": slots[j],
                                      "v": v, "merge": out_m[j]})
                        self.grid[slots[j][0]][slots[j][1]] = v
        elif dr == 1:     # down
            for c in range(4):
                slots = [(r, c) for r in range(3, -1, -1)]
                values = [self.grid[r][c] for r in range(3, -1, -1)]
                out_v, out_src, out_m = self._slide_line(slots, values)
                for j, v in enumerate(out_v):
                    if v:
                        moves.append({"from": slots[out_src[j]], "to": slots[j],
                                      "v": v, "merge": out_m[j]})
                        self.grid[slots[j][0]][slots[j][1]] = v
        elif dc == -1:    # left
            for r in range(4):
                slots = [(r, c) for c in range(4)]
                values = self.grid[r][:]
                out_v, out_src, out_m = self._slide_line(slots, values)
                for j, v in enumerate(out_v):
                    if v:
                        moves.append({"from": slots[out_src[j]], "to": slots[j],
                                      "v": v, "merge": out_m[j]})
                        self.grid[r][slots[j][1]] = v
        else:             # right
            for r in range(4):
                slots = [(r, c) for c in range(3, -1, -1)]
                values = self.grid[r][3::-1]
                out_v, out_src, out_m = self._slide_line(slots, values)
                for j, v in enumerate(out_v):
                    if v:
                        moves.append({"from": slots[out_src[j]], "to": slots[j],
                                      "v": v, "merge": out_m[j]})
                        self.grid[r][slots[j][1]] = v

        if self.grid == prev and self.score == prev_score:
            return False  # nothing changed

        self.history.append((copy.deepcopy(prev), prev_score, self.max_tile))
        if len(self.history) > UNDO_LIMIT:
            self.history.pop(0)

        spawn = self.add_tile()
        anim_tiles = list(moves)
        if spawn:
            anim_tiles.append({"from": spawn[:2], "to": spawn[:2], "v": spawn[2],
                               "merge": False, "new": True})
        self.anim = {"t": 0, "dur": ANIM_DUR, "tiles": anim_tiles}

        if self.max_tile >= 2048:
            self.won = True
        self.check_over()
        return True

    def check_over(self):
        if any(0 in row for row in self.grid):
            return
        for r in range(4):
            for c in range(4):
                if c + 1 < 4 and self.grid[r][c] == self.grid[r][c + 1]:
                    return
                if r + 1 < 4 and self.grid[r][c] == self.grid[r + 1][c]:
                    return
        self.over = True

    def undo(self):
        if not self.history:
            return False
        self.anim = None  # cancel any in-flight animation
        grid, score, max_tile = self.history.pop()
        self.grid = grid
        self.score = score
        self.max_tile = max_tile
        return True

    # ------------------------------------------------------------------
    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or self.over:
                self.done = True
                return
            if event.key == pygame.K_u:
                self.undo()
                return
            if event.key in MOVE_KEYS:
                dr, dc = MOVE_KEYS[event.key]
                self.move(dr, dc)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.over:
            self.done = True

    def update(self, dt):
        if self.anim:
            self.anim["t"] += 1
            if self.anim["t"] > self.anim["dur"]:
                self.anim = None

    # ------------------------------------------------------------------
    def _tile_center(self, r, c):
        return (self.ox + c * (self.tile + self.gap) + self.tile / 2,
                self.oy + r * (self.tile + self.gap) + self.tile / 2)

    def _draw_tile(self, canvas, R, cx, cy, value, scale=1.0):
        size = self.tile * scale
        color = TILE_COLORS.get(value, (35, 30, 45))
        R.rr(canvas, (cx - size / 2, cy - size / 2, size, size), color, radius=10)
        fs = 22 if value >= 1000 else 28 if value >= 100 else 34
        txt = R.text(fs, True, str(value), (40, 40, 50) if value in (2, 4) else FG)
        R.blit_center(canvas, txt, cx, cy)

    def draw(self, canvas, R):
        R.clear(canvas)
        if self.anim:
            moving = {t["to"] for t in self.anim["tiles"]}
            frac_all = self.anim["t"] / self.anim["dur"]
            # static (non-moving) tiles
            for r in range(4):
                for c in range(4):
                    if (r, c) in moving:
                        continue
                    if self.grid[r][c]:
                        cx, cy = self._tile_center(r, c)
                        self._draw_tile(canvas, R, cx, cy, self.grid[r][c])
                    else:
                        cx, cy = self._tile_center(r, c)
                        R.rr(canvas, (cx - self.tile / 2, cy - self.tile / 2,
                                      self.tile, self.tile), GRID_D, radius=10)
            # animated tiles
            for t in self.anim["tiles"]:
                fr = t["from"]
                to = t["to"]
                f = self._tile_center(*fr)
                t2 = self._tile_center(*to)
                cx = f[0] + (t2[0] - f[0]) * frac_all
                cy = f[1] + (t2[1] - f[1]) * frac_all
                if t.get("new"):
                    scale = 0.55 + 0.45 * frac_all
                elif t["merge"]:
                    scale = 1.0 + 0.3 * (0.5 - abs(frac_all - 0.5) * 2)
                else:
                    scale = 1.0
                self._draw_tile(canvas, R, cx, cy, t["v"], scale)
        else:
            for r in range(4):
                for c in range(4):
                    cx, cy = self._tile_center(r, c)
                    if self.grid[r][c]:
                        self._draw_tile(canvas, R, cx, cy, self.grid[r][c])
                    else:
                        R.rr(canvas, (cx - self.tile / 2, cy - self.tile / 2,
                                      self.tile, self.tile), GRID_D, radius=10)
        s = R.text(32, False, f"P {self.score}", DIM)
        R.blit(canvas, s, (16, 10))
        u = R.text(20, False, "U:undo", DIM)
        R.blit(canvas, u, (R.canvas_size - 14 - u.get_width(), 12))
        if self.over:
            self.finish(canvas, R)
        else:
            R.finish(canvas)
