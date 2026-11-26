"""Base class shared by every game.

Defines the common contract the App relies on:

- ``reset()``    - start a fresh game
- ``handle(e)``  - process one input event (keys + mouse clicks)
- ``update(dt)`` - advance simulation by dt seconds (only while playing)
- ``draw(c, R)`` - render onto the canvas via the shared Renderer
- state flags: ``over`` (game finished), ``done`` (return to menu),
  ``paused``, ``won`` (victory), plus ``score`` / ``best`` / ``new_best``.

Every game guarantees a fair start: a freshly reset game is never ``over``
and never ``done`` until the player actually plays it.
"""


class GameBase:
    KEY = ""        # menu selector, e.g. "1"
    NAME = ""       # full name, e.g. "SNAKE"
    LABEL = ""      # short label for the tiny menu, e.g. "SNAKE"
    ICON = ""       # icon kind: snake / type / grid / flap / memory / react / break
    DESC = ""       # one-line description for the stats / help screen

    def __init__(self):
        self.score = 0
        self.over = False       # game-over / win reached
        self.done = False       # player asked to return to the menu
        self.paused = False
        self.won = False        # clear victory condition reached
        self.best = 0           # best score (filled by the App on game end)
        self.new_best = False   # this run set a new best

    # ------------------------------------------------------------------
    def reset(self):
        raise NotImplementedError

    def handle(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, canvas, R):
        raise NotImplementedError

    # ------------------------------------------------------------------
    def finish(self, canvas, R, label=None):
        """Draw the game-over (or win) card and the frame border."""
        if label is None:
            label = f"{self.NAME} {self.score}"
        if self.won:
            R.draw_win(canvas, label)
        else:
            R.draw_over(canvas, label, self.best, self.new_best)
        R.finish(canvas)

    def end_score_label(self):
        return f"{self.NAME} {self.score}"

    def record_value(self):
        """The value persisted for best-score purposes.

        Returns (value, higher_is_better). Override for games where a lower
        number is better (e.g. Memory's move count).
        """
        return self.score, True
