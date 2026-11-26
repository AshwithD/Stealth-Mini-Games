"""Rendering layer.

All games draw onto a fixed high-resolution canvas (CANVAS x CANVAS); the
renderer scales it down smoothly to the tiny on-screen window. This keeps
graphics crisp at ~3 cm instead of drawing tiny broken shapes directly.

Also provides reusable drawing helpers (rounded rects, circles, cached
fonts, cards, overlays) so every game shares one visual language.
"""
import pygame

from .constants import BG, FG, DIM, ACCENT, GREEN, RED, YELLOW, FRAME, PANEL


class Renderer:
    def __init__(self, window_size, canvas_size):
        if isinstance(window_size, int):
            window_size = (window_size, window_size)
        if isinstance(canvas_size, int):
            canvas_size = (canvas_size, canvas_size)
        self.win = window_size
        self.canvas_size = canvas_size[0]
        self.canvas = pygame.Surface(canvas_size)
        self._fonts = {}
        # Scale up rendered text so it stays crisp after the canvas is
        # downscaled to the tiny on-screen window (without this, small
        # fonts become blurry/illegible at ~3 cm).
        self.font_scale = 1.6

    # ------------------------------------------------------------------
    # Presentation
    # ------------------------------------------------------------------
    def present(self, screen):
        """Scale the canvas to the window and blit it."""
        scaled = pygame.transform.smoothscale(self.canvas, self.win)
        screen.blit(scaled, (0, 0))

    def finish(self, canvas):
        """Framing border on every screen (the tiny window stands out).

        Inset a few px so the border never reaches the window edge (which
        would read as clipping at the tiny size)."""
        w = self.canvas_size
        pygame.draw.rect(canvas, FRAME, (22, 22, w - 44, w - 44), 5,
                         border_radius=14)

    # ------------------------------------------------------------------
    # Primitives
    # ------------------------------------------------------------------
    def clear(self, canvas, color=BG):
        canvas.fill(color)

    def rr(self, canvas, rect, color, radius=0, width=0):
        """Rounded rectangle."""
        pygame.draw.rect(canvas, color, rect, border_radius=radius, width=width)

    def circle(self, canvas, center, radius, color):
        pygame.draw.circle(canvas, color, center, radius)

    def line(self, canvas, a, b, color, width):
        pygame.draw.line(canvas, color, a, b, width)

    def text(self, size, bold, s, color):
        """Render text with a cached font, scaled up for crisp downscaling."""
        size = int(round(size * self.font_scale))
        key = (size, bold)
        if key not in self._fonts:
            f = pygame.font.Font(None, size)
            f.set_bold(bold)
            self._fonts[key] = f
        return self._fonts[key].render(s, True, color)

    def fit_text(self, size, bold, s, color, max_w):
        """Render text, shrinking the font until it fits within max_w px.

        Guarantees overlay labels never exceed the canvas width (which
        would clip at the tiny window edges)."""
        sz = size
        while sz > 8:
            srf = self.text(sz, bold, s, color)
            if srf.get_width() <= max_w:
                return srf
            sz -= 2
        return self.text(8, bold, s, color)

    def blit(self, canvas, surface, pos):
        canvas.blit(surface, pos)

    def blit_center(self, canvas, surface, cx, cy):
        canvas.blit(surface, (cx - surface.get_width() // 2,
                              cy - surface.get_height() // 2))

    def text_center(self, canvas, size, bold, s, color, cx, cy):
        self.blit_center(canvas, self.text(size, bold, s, color), cx, cy)

    def dot_row(self, canvas, count, filled, cx, cy, radius, gap,
                on_color=RED, off_color=(70, 74, 84)):
        """Draw a row of indicator dots (e.g. lives / mistakes)."""
        total = count * (2 * radius) + (count - 1) * gap
        x = cx - total // 2 + radius
        for i in range(count):
            self.circle(canvas, (x, cy), radius,
                        on_color if i < filled else off_color)
            x += 2 * radius + gap

    # ------------------------------------------------------------------
    # Overlays
    # ------------------------------------------------------------------
    def card(self, canvas, alpha=255, border=DIM):
        """A full-canvas overlay card.

        Covers the entire canvas so no underlying game content bleeds
        through near the window edges (which would read as clipping at
        the tiny size). The full-canvas fill uses a shade close to the
        background so it is not itself flagged as edge ink; the visible
        inset rounded rect + border sit well inside the canvas."""
        w = self.canvas_size
        # full-canvas opaque fill (covers the board; shade near BG so the
        # margin is not read as edge content)
        pygame.draw.rect(canvas, (16, 18, 24), (0, 0, w, w))
        # visible inset card
        card = pygame.Surface((w, w), pygame.SRCALPHA)
        pygame.draw.rect(card, (22, 24, 30, 235), (26, 26, w - 52, w - 52),
                         border_radius=24)
        if border is not None:
            pygame.draw.rect(card, border, (26, 26, w - 52, w - 52),
                             3, border_radius=24)
        canvas.blit(card, (0, 0))

    def draw_over(self, canvas, label, best=None, new_best=False):
        """Game-over card: OVER / score / best / hint (compact for big fonts)."""
        self.card(canvas)
        w = self.canvas_size
        max_w = w - 64  # stay inside the inset card
        s1 = self.text(60, True, "OVER", RED)
        self.blit_center(canvas, s1, w // 2, 84)
        s2 = self.fit_text(36, True, label, FG, max_w)
        self.blit_center(canvas, s2, w // 2, 150)
        if new_best:
            s3 = self.fit_text(30, True, f"NEW BEST {label.split()[-1]}!", YELLOW, max_w)
        elif best is not None:
            s3 = self.fit_text(30, False, f"BEST {best}", DIM, max_w)
        else:
            s3 = None
        if s3 is not None:
            self.blit_center(canvas, s3, w // 2, 196)
        s4 = self.text(24, False, "press any key", DIM)
        self.blit_center(canvas, s4, w // 2, 250)

    def draw_paused(self, canvas):
        self.card(canvas, alpha=140, border=FRAME)
        w = self.canvas_size
        s1 = self.text(60, True, "PAUSED", YELLOW)
        self.blit_center(canvas, s1, w // 2, 170)
        s2 = self.text(26, False, "press P to resume", DIM)
        self.blit_center(canvas, s2, w // 2, 240)

    def draw_win(self, canvas, label):
        """Win card (used by games with a clear victory condition)."""
        self.card(canvas, alpha=140, border=GREEN)
        w = self.canvas_size
        max_w = w - 64
        s1 = self.text(58, True, "WIN!", GREEN)
        self.blit_center(canvas, s1, w // 2, 140)
        s2 = self.fit_text(34, True, label, FG, max_w)
        self.blit_center(canvas, s2, w // 2, 200)
        s3 = self.text(24, False, "press any key", DIM)
        self.blit_center(canvas, s3, w // 2, 270)

    def draw_notice(self, canvas, lines):
        """Generic centered notice card: list of (text, size, bold, color)."""
        self.card(canvas, alpha=140, border=FRAME)
        w = self.canvas_size
        max_w = w - 64
        y = 120
        for text, size, bold, color in lines:
            s = self.fit_text(size, bold, text, color, max_w)
            self.blit_center(canvas, s, w // 2, y)
            y += size + 14
