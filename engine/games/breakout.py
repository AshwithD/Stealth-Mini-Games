"""Game 7: Breakout (paddle + ball + bricks).

Deepened mechanics:
- Paddle controlled by the mouse (hover) or A/D; ball launches with
  Space / click and bounces off walls, the paddle and bricks.
- Paddle hit angle depends on where the ball strikes the paddle.
- 4 rows of bricks; clearing them all is a win. 3 lives; the ball falling
  below the paddle costs one. Ball speed ramps slightly with score.
"""
import math
import random

import pygame

from ..constants import BG, FG, DIM, ACCENT, GREEN, RED, PANEL, MUTED
from .base import GameBase

COLS, ROWS = 7, 4
BRICK_W, BRICK_H, BRICK_GAP = 36, 16, 4
PLAY_OX, PLAY_OY = 16, 44
PLAY_W, PLAY_H = 328, 300
PADDLE_W, PADDLE_H = 76, 12
BALL_R = 6
BRICK_COLORS = [(248, 180, 110), (246, 142, 98), (240, 112, 92), (234, 82, 72)]


class BreakoutGame(GameBase):
    KEY = "7"
    NAME = "BREAK"
    LABEL = "BREAK"
    ICON = "break"
    DESC = "Break all the bricks with the paddle"

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self.bricks = []
        for r in range(ROWS):
            for c in range(COLS):
                self.bricks.append({"x": PLAY_OX + (PLAY_W - (COLS * BRICK_W +
                                                          (COLS - 1) * BRICK_GAP)) // 2
                                   + c * (BRICK_W + BRICK_GAP),
                                   "y": PLAY_OY + 14 + r * (BRICK_H + BRICK_GAP),
                                   "row": r, "alive": True})
        self.paddle_x = PLAY_OX + PLAY_W / 2 - PADDLE_W / 2
        self.paddle_y = PLAY_OY + PLAY_H - 18
        self.ball = None
        self.vx = 0.0
        self.vy = 0.0
        self.speed = 3.2
        self.lives = 3
        self.score = 0
        self.over = False
        self.done = False
        self.won = False
        self._place_ball()

    def _place_ball(self):
        self.ball = (self.paddle_x + PADDLE_W / 2, self.paddle_y - BALL_R - 2)
        self.vx = 0.0
        self.vy = 0.0

    def _launch(self):
        if self.ball is None or self.vx != 0.0:
            return
        angle = random.uniform(-0.6, 0.6)  # radians from straight up
        self.vx = self.speed * math.sin(angle)
        self.vy = -self.speed * math.cos(angle)

    def _clamp_paddle(self):
        self.paddle_x = max(PLAY_OX, min(PLAY_OX + PLAY_W - PADDLE_W,
                                         self.paddle_x))

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or self.over:
                self.done = True
                return
            if event.key == pygame.K_a:
                self.paddle_x -= 9
                self._clamp_paddle()
            elif event.key == pygame.K_d:
                self.paddle_x += 9
                self._clamp_paddle()
            elif event.key == pygame.K_SPACE:
                self._launch()
        elif event.type == pygame.MOUSEMOTION:
            # hover control: ignore while a mouse button is held (dragging)
            if not event.buttons:
                self.paddle_x = event.pos[0] - PADDLE_W / 2
                self._clamp_paddle()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.over:
                self.done = True
            else:
                self._launch()

    def update(self, dt):
        if self.over:
            return
        # win check first: a cleared board wins even if the ball rests
        if not any(b["alive"] for b in self.bricks):
            self.over = True
            self.won = True
            return
        if self.vx == 0.0 and self.vy == 0.0:
            # ball resting on the paddle: follow it
            self.ball = (self.paddle_x + PADDLE_W / 2, self.paddle_y - BALL_R - 2)
            return
        # ramp speed gently with score
        self.speed = min(6.0, 3.2 + self.score * 0.02)
        vmag = (self.vx * self.vx + self.vy * self.vy) ** 0.5
        if vmag > 0:
            self.vx = self.vx / vmag * self.speed
            self.vy = self.vy / vmag * self.speed
        bx, by = self.ball
        bx += self.vx
        by += self.vy

        # walls
        if bx - BALL_R < PLAY_OX:
            bx = PLAY_OX + BALL_R
            self.vx = abs(self.vx)
        elif bx + BALL_R > PLAY_OX + PLAY_W:
            bx = PLAY_OX + PLAY_W - BALL_R
            self.vx = -abs(self.vx)
        if by - BALL_R < PLAY_OY:
            by = PLAY_OY + BALL_R
            self.vy = abs(self.vy)

        # paddle
        paddle = pygame.Rect(self.paddle_x, self.paddle_y, PADDLE_W, PADDLE_H)
        ball_rect = pygame.Rect(bx - BALL_R, by - BALL_R, BALL_R * 2, BALL_R * 2)
        if paddle.colliderect(ball_rect) and self.vy > 0:
            by = self.paddle_y - BALL_R - 1
            self.vy = -abs(self.vy)
            # angle from strike position
            offset = (bx - (self.paddle_x + PADDLE_W / 2)) / (PADDLE_W / 2)
            max_angle = 1.0
            angle = max(-max_angle, min(max_angle, offset * max_angle))
            v = self.speed
            self.vx = v * math.sin(angle)
            self.vy = -v * math.cos(angle)

        # bricks
        for brick in self.bricks:
            if not brick["alive"]:
                continue
            br = pygame.Rect(brick["x"], brick["y"], BRICK_W, BRICK_H)
            if br.colliderect(ball_rect):
                brick["alive"] = False
                self.score += 10 * (brick["row"] + 1)
                # decide bounce axis by overlap
                ox = min(bx + BALL_R, br.right) - max(bx - BALL_R, br.x)
                oy = min(by + BALL_R, br.bottom) - max(by - BALL_R, br.y)
                if ox < oy:
                    self.vx = -self.vx
                    bx += self.vx
                else:
                    self.vy = -self.vy
                    by += self.vy
                break

        # fall below paddle -> lose a life
        if by - BALL_R > PLAY_OY + PLAY_H:
            self.lives -= 1
            if self.lives <= 0:
                self.over = True
            else:
                self._place_ball()
            return

        self.ball = (bx, by)
        if not any(b["alive"] for b in self.bricks):
            self.over = True
            self.won = True

    # ------------------------------------------------------------------
    def draw(self, canvas, R):
        R.clear(canvas)
        R.rr(canvas, (PLAY_OX - 6, PLAY_OY - 6, PLAY_W + 12, PLAY_H + 12),
             MUTED, radius=12)
        for brick in self.bricks:
            if brick["alive"]:
                R.rr(canvas, (brick["x"], brick["y"], BRICK_W, BRICK_H),
                     BRICK_COLORS[brick["row"] % len(BRICK_COLORS)], radius=3)
        # paddle
        R.rr(canvas, (self.paddle_x, self.paddle_y, PADDLE_W, PADDLE_H),
             ACCENT, radius=6)
        # ball
        if self.ball:
            R.circle(canvas, self.ball, BALL_R, FG)
        s = R.text(32, False, f"B {self.score}", DIM)
        R.blit(canvas, s, (14, 10))
        R.dot_row(canvas, 3, self.lives, 180, 22, 8, 14, on_color=GREEN)
        if self.over:
            label = f"BREAK {self.score}" + ("  WIN" if self.won else "")
            self.finish(canvas, R, label)
        else:
            R.finish(canvas)
