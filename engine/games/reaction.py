"""Game 6: Reaction.

Deepened mechanics:
- A target dot appears at a random position and shrinks over its lifetime.
- Click it as fast as possible: each hit scores and measures your reaction
  time in milliseconds.
- Difficulty ramps: the target lives shorter as you score.
- Three misses (target expires) end the game. Best reaction time is kept.
"""
import random

import pygame

from ..constants import BG, FG, DIM, ACCENT, GREEN, RED, YELLOW
from .base import GameBase

BASE_LIFETIME = 2.4
MIN_LIFETIME = 1.2
RADIUS = 26
MARGIN = 48
LIVES = 3


class ReactionGame(GameBase):
    KEY = "6"
    NAME = "REACT"
    LABEL = "REACT"
    ICON = "react"
    DESC = "Click the dot before it disappears"

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self.score = 0
        self.lives = LIVES
        self.times = []           # reaction times (seconds) of this run
        self.target = None        # (x, y)
        self.life_left = 0.0
        self.lifetime = BASE_LIFETIME
        self.over = False
        self.done = False
        self.won = False
        self.spawn_target()

    # ------------------------------------------------------------------
    def _lifetime(self):
        return max(MIN_LIFETIME, BASE_LIFETIME - self.score * 0.04)

    def spawn_target(self):
        self.lifetime = self._lifetime()
        self.life_left = self.lifetime
        x = random.randint(MARGIN, 360 - MARGIN)
        y = random.randint(MARGIN + 20, 360 - MARGIN - 20)
        self.target = (x, y)

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or self.over:
                self.done = True
                return
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.over:
                self.done = True
                return
            if self.target is None:
                return
            dx = event.pos[0] - self.target[0]
            dy = event.pos[1] - self.target[1]
            if dx * dx + dy * dy <= RADIUS * RADIUS:
                # reaction time = how long the target had been visible
                self.times.append(self.lifetime - self.life_left)
                self.score += 1
                self.spawn_target()

    def update(self, dt):
        if self.over:
            return
        self.life_left -= dt
        if self.life_left <= 0:
            self.lives -= 1
            if self.lives <= 0:
                self.over = True
            else:
                self.spawn_target()

    # ------------------------------------------------------------------
    def best_reaction_ms(self):
        if not self.times:
            return None
        return int(min(self.times) * 1000)

    def draw(self, canvas, R):
        R.clear(canvas)
        # faint play-field panel for structure
        R.rr(canvas, (10, 10, 360 - 20, 360 - 20), (32, 35, 42), radius=14)
        if self.target is not None and not self.over:
            # shrinking ring: radius proportional to remaining lifetime
            ratio = max(0.0, self.life_left / self.lifetime)
            r = int(RADIUS * (0.45 + 0.55 * ratio))
            cx, cy = self.target
            R.circle(canvas, (cx, cy), r + 8, (48, 52, 60))
            R.circle(canvas, (cx, cy), r, YELLOW if ratio > 0.5 else RED)
            R.circle(canvas, (cx, cy), max(3, r // 4), FG)
        s = R.text(32, False, f"R {self.score}", DIM)
        R.blit(canvas, s, (16, 16))
        b = self.best_reaction_ms()
        if b is not None:
            t = R.text(24, False, f"BEST {b}ms", ACCENT)
            R.blit(canvas, t, (360 - 16 - t.get_width(), 18))
        R.dot_row(canvas, LIVES, self.lives, 180, 338, 8, 14,
                  on_color=GREEN)
        if self.over:
            label = f"REACT {self.score}"
            if self.times:
                label += f"  {self.best_reaction_ms()}ms"
            self.finish(canvas, R, label)
        else:
            R.finish(canvas)
