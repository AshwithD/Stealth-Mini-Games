"""Persistent game data: best scores, play stats.

Stored as JSON next to the executable (``game_data.json``). The store is
deliberately defensive: every read/write is wrapped so a locked file, a
read-only folder or a corrupt file can never crash the game.
"""
import json
import os

from . import config

_DATA_FILE = "game_data.json"


class Store:
    """Best scores + play statistics, persisted to JSON."""

    def __init__(self, path=None):
        self.path = path or os.path.join(config.base_dir(), _DATA_FILE)
        self.best = {}      # game_key -> best score
        self.plays = {}     # game_key -> number of games played
        self.wins = {}      # game_key -> number of wins
        self.total_score = 0
        self.load()

    # ------------------------------------------------------------------
    def load(self):
        try:
            with open(self.path) as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                return
            self.best = {str(k): int(v) for k, v in data.get("best", {}).items()}
            self.plays = {str(k): int(v) for k, v in data.get("plays", {}).items()}
            self.wins = {str(k): int(v) for k, v in data.get("wins", {}).items()}
            self.total_score = int(data.get("total_score", 0))
        except Exception:
            self.best, self.plays, self.wins = {}, {}, {}
            self.total_score = 0

    def save(self):
        try:
            with open(self.path, "w") as fh:
                json.dump({
                    "best": self.best,
                    "plays": self.plays,
                    "wins": self.wins,
                    "total_score": self.total_score,
                }, fh, indent=2)
        except Exception:
            pass

    # ------------------------------------------------------------------
    def best_score(self, game_key):
        return self.best.get(str(game_key), 0)

    def record_game(self, game_key, value, won=False, higher=True):
        """Register a finished game. Returns (best, new_best).

        ``higher`` selects the comparison direction: True for score-like
        metrics (higher is better), False for metrics like Memory's move
        count (lower is better).
        """
        key = str(game_key)
        self.plays[key] = self.plays.get(key, 0) + 1
        self.total_score += int(value)
        best = self.best_score(key)
        new_best = False
        if higher:
            if value > best:
                best = int(value)
                self.best[key] = best
                new_best = True
        else:
            if best == 0 or value < best:
                best = int(value)
                self.best[key] = best
                new_best = True
        if won:
            self.wins[key] = self.wins.get(key, 0) + 1
        self.save()
        return best, new_best

    # ------------------------------------------------------------------
    def summary(self):
        """Flat list of (game_key, best, plays, wins) for the stats screen."""
        keys = sorted(set(self.best) | set(self.plays) | set(self.wins))
        return [(k, self.best_score(k), self.plays.get(k, 0), self.wins.get(k, 0))
                for k in keys]

    def reset(self):
        self.best, self.plays, self.wins = {}, {}, {}
        self.total_score = 0
        self.save()
