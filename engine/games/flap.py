"""Game 4: Flappy.

Deepened mechanics:
- Bird starts with a flap plus a long no-collision grace window, and is
  clamped to the play field during grace, so it can never die before the
  player has a fair chance to react.
- Difficulty ramps with score: pipes move faster and gaps narrow slightly.
- Bird tilts with velocity (classic flappy feel).
- Physics tuned to feel snappy (no sluggish float) while staying forgiving.
"""
import random

import pygame

from ..constants import BG, FG, DIM, GREEN, YELLOW, GRID_D
from .base import GameBase


class FlapGame(GameBase):
    KEY = "4"
    NAME = "FLAP"
    LABEL = "FLAP"
    ICON = "flap"
    DESC = "Tap to fly between the pipes"

    def __init__(self):
        super().__init__()
        self.bird_w, self.bird_h = 38, 30
        self.gx = 92
        self.gravity = 0.20
        self.jump = -7.5
        self.base_speed = 1.9
        self.base_gap = 185.0
        self.pipe_w = 46
        self.spawn_every = 95
        # pre-render the bird once (rotated copies are cheap)
        self.bird_img = pygame.Surface((self.bird_w + 14, self.bird_h + 14),
                                       pygame.SRCALPHA)
        pygame.draw.ellipse(self.bird_img, YELLOW, self.bird_img.get_rect())
        pygame.draw.ellipse(self.bird_img, (30, 30, 30), (16, 8, 10, 10))
        self.reset()

    def reset(self):
        self.y = 360 * 0.42
        self.vy = self.jump * 0.8    # starts with a flap
        self.grace = 120             # long no-collision grace at the start
        self.pipes = []
        self.frame = 0
        self.score = 0
        self.over = False
        self.done = False
        self.won = False
        self.spawn_timer = 90

    def _speed(self):
        return min(2.6, self.base_speed + self.score * 0.04)

    def _gap(self):
        return max(110.0, self.base_gap - self.score * 1.0)

    def _new_pipe(self):
        gap = self._gap()
        center = random.uniform(gap / 2 + 14, 360 - gap / 2 - 14)
        return {"x": 360 + 10, "gap_y": center, "passed": False}

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or self.over:
                self.done = True
                return
            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                self.vy = self.jump
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.over:
                self.done = True
            else:
                self.vy = self.jump

    def update(self, dt):
        if self.over:
            return
        self.frame += 1
        self.spawn_timer -= 1
        if self.spawn_timer <= 0 and not self.pipes:
            self.pipes.append(self._new_pipe())
            self.spawn_timer = self.spawn_every
        self.y += self.vy
        self.vy += self.gravity
        speed = self._speed()
        gap = self._gap()
        for p in self.pipes:
            p["x"] -= speed
            if not p["passed"] and p["x"] + self.pipe_w < self.gx:
                p["passed"] = True
                self.score += 1
        self.pipes = [p for p in self.pipes if p["x"] + self.pipe_w > 0]
        # cap the fall speed so the bird never accelerates into an edge
        if self.vy > 7.0:
            self.vy = 7.0
        if self.grace > 0:
            # grace: no collisions and clamp to the field so the bird can
            # never fall out before the player can react
            self.grace -= 1
            self.y = max(14.0, min(360 - self.bird_h - 26.0, self.y))
            return
        # forgiving death bounds: the bird must reach well past the field
        # edge before it dies, giving ample room to recover
        if self.y < 2 or self.y > 360 - self.bird_h - 12:
            self.over = True
            return
        bird = pygame.Rect(self.gx, self.y, self.bird_w, self.bird_h)
        for p in self.pipes:
            top = pygame.Rect(p["x"], 8, self.pipe_w, p["gap_y"] - gap / 2 - 8)
            bottom = pygame.Rect(p["x"], p["gap_y"] + gap / 2,
                                 self.pipe_w, 360 - 8 - (p["gap_y"] + gap / 2))
            if top.colliderect(bird) or bottom.colliderect(bird):
                self.over = True
                return

    def draw(self, canvas, R):
        R.clear(canvas)
        # subtle background dots for texture
        for (dx, dy) in [(58, 66), (300, 88), (170, 46), (320, 180)]:
            R.circle(canvas, (dx, dy), 5, (52, 56, 66))
        ground = 360 - 20
        R.rr(canvas, (12, ground, 360 - 24, 8), GRID_D, radius=4)
        R.line(canvas, (12, ground), (360 - 12, ground), DIM, 3)
        for p in self.pipes:
            top_h = p["gap_y"] - self._gap() / 2
            bot_y = p["gap_y"] + self._gap() / 2
            R.rr(canvas, (p["x"], 8, self.pipe_w, top_h - 8), GREEN, radius=6)
            R.rr(canvas, (p["x"], bot_y, self.pipe_w, 360 - 8 - bot_y),
                 GREEN, radius=6)
        angle = max(-25.0, min(90.0, self.vy * 2.4))
        rot = pygame.transform.rotate(self.bird_img, angle)
        R.blit(canvas, rot, (self.gx - 7, self.y - 7))
        s = R.text(32, False, f"F {self.score}", DIM)
        R.blit(canvas, s, (14, 10))
        if self.over:
            self.finish(canvas, R)
        else:
            R.finish(canvas)
