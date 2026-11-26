"""Game 1: Snake.

Deepened mechanics:
- Two modes: ``wrap`` (walls wrap around) and ``walls`` (hitting a wall
  kills the snake). Toggle with M at any time.
- Two food types: normal (1 pt) and golden (5 pts, rare, pulsing).
- Speed ramps up slightly with score.
- **Smooth sliding**: the body interpolates between grid cells every frame
  so it glides instead of teleporting - no glitchy jumps at tiny sizes.
"""
import math
import random

import pygame

from ..constants import BG, FG, DIM, ACCENT, GREEN, RED, YELLOW, MUTED, MOVE_KEYS
from .base import GameBase


class SnakeGame(GameBase):
    KEY = "1"
    NAME = "SNAKE"
    LABEL = "SNAKE"
    ICON = "snake"
    DESC = "Eat food, grow longer, don't bite yourself"

    def __init__(self):
        super().__init__()
        self.cells = 8
        self.cell = 42
        self.ox = 18
        self.oy = 18
        self.mode = "wrap"
        self.t = 0
        self.reset()

    # ------------------------------------------------------------------
    def reset(self):
        mid = self.cells // 2
        self.body = [(mid, mid), (mid - 1, mid), (mid - 2, mid)]
        # smooth render positions (one float (x, y) per segment)
        self.pos = [self._center(*seg) for seg in self.body]
        self.dir = (1, 0)
        self.pending = 0
        self.score = 0
        self.mode = "wrap"
        self.t = 0
        self.food = self._spawn_food()
        self.over = False
        self.done = False
        self.won = False

    def _center(self, x, y):
        return (self.ox + (x + 0.5) * self.cell,
                self.oy + (y + 0.5) * self.cell)

    def _spawn_food(self):
        free = [(x, y) for x in range(self.cells) for y in range(self.cells)
                if (x, y) not in self.body]
        if not free:
            return None, False
        golden = random.random() < 0.15
        return random.choice(free), golden

    def _speed(self):
        # frames between logical moves; base 9 = relaxed/slow, ramps gently
        return max(5, 9 - self.score // 15)

    # ------------------------------------------------------------------
    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or self.over:
                self.done = True
                return
            if event.key == pygame.K_m:
                self.mode = "walls" if self.mode == "wrap" else "wrap"
                return
            if event.key in MOVE_KEYS:
                dr, dc = MOVE_KEYS[event.key]
                nd = (dc, dr)
                if nd[0] != -self.dir[0] or nd[1] != -self.dir[1]:
                    self.dir = nd
        elif event.type == pygame.MOUSEBUTTONDOWN and self.over:
            self.done = True

    def update(self, dt):
        if self.over:
            return
        self.t += 1
        # advance logical move on schedule
        self.pending -= 1
        if self.pending <= 0:
            self._step()
            self.pending = self._speed()
        # smooth-slide every segment toward its target cell
        for i, (x, y) in enumerate(self.body):
            tx, ty = self._center(x, y)
            px, py = self.pos[i]
            # gentle glide toward target (slow + smooth, never a teleport)
            self.pos[i] = (px + (tx - px) * 0.35, py + (ty - py) * 0.35)

    def _step(self):
        hx = self.body[0][0] + self.dir[0]
        hy = self.body[0][1] + self.dir[1]
        if self.mode == "wrap":
            hx %= self.cells
            hy %= self.cells
        else:  # walls mode: hitting the border kills the snake
            if hx < 0 or hy < 0 or hx >= self.cells or hy >= self.cells:
                self.over = True
                return
        if (hx, hy) in self.body:
            self.over = True
            return
        # new head render position starts at current head (so it slides out)
        self.pos.insert(0, self.pos[0])
        self.body.insert(0, (hx, hy))
        if (hx, hy) == self.food[0]:
            self.score += 5 if self.food[1] else 1
            self.food = self._spawn_food()
        else:
            self.body.pop()
            self.pos.pop()

    # ------------------------------------------------------------------
    def draw(self, canvas, R):
        R.clear(canvas)
        R.rr(canvas, (8, 8, R.canvas_size - 16, R.canvas_size - 16),
             MUTED, radius=16)
        for i, (cx, cy) in enumerate(self.pos):
            if i == 0:
                R.circle(canvas, (cx, cy), 19, (120, 240, 160))
                dx, dy = self.dir
                R.circle(canvas, (cx + dx * 9 + dy * 5, cy + dy * 9 - dx * 5), 3, BG)
                R.circle(canvas, (cx + dx * 9 - dy * 5, cy + dy * 9 + dx * 5), 3, BG)
            else:
                R.circle(canvas, (cx, cy), 16, (46, 168, 88))
        if self.food[0] is not None:
            fx, fy = self.food[0]
            r = (16 + 3 * math.sin(self.t * 0.12)) if self.food[1] else \
                (14 + 3 * math.sin(self.t * 0.12))
            R.circle(canvas,
                     (self.ox + (fx + 0.5) * self.cell,
                      self.oy + (fy + 0.5) * self.cell),
                     r, YELLOW if self.food[1] else RED)
        s = R.text(32, False, f"S {self.score}", DIM)
        R.blit(canvas, s, (14, 10))
        # mode badge
        m = R.text(22, True, "WRAP" if self.mode == "wrap" else "WALLS",
                   ACCENT if self.mode == "wrap" else YELLOW)
        R.blit(canvas, m, (R.canvas_size - 14 - m.get_width(), 12))
        if self.over:
            self.finish(canvas, R)
        else:
            R.finish(canvas)
