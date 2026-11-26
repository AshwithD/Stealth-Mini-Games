"""Game registry: metadata + classes for the menu and the App.

Adding a new game = create a class in this package, add it to GAME_CLASSES
and GAME_META below. Nothing else needs to change.
"""
from .base import GameBase
from .snake import SnakeGame
from .type_rush import TypeRushGame
from .game2048 import Game2048
from .flap import FlapGame
from .memory import MemoryGame
from .reaction import ReactionGame
from .breakout import BreakoutGame

# key -> class
GAME_CLASSES = {
    "1": SnakeGame,
    "2": TypeRushGame,
    "3": Game2048,
    "4": FlapGame,
    "5": MemoryGame,
    "6": ReactionGame,
    "7": BreakoutGame,
}

# Menu metadata in display order: (key, name, label, icon, description)
GAME_META = [
    ("1", "SNAKE", "SNAKE", "snake",
     "Eat food, grow longer, don't bite yourself"),
    ("2", "TYPE", "TYPE", "type",
     "Type the words fast - looks like real work"),
    ("3", "2048", "2048", "grid",
     "Slide and merge tiles, reach 2048 (U = undo)"),
    ("4", "FLAP", "FLAP", "flap",
     "Tap to fly between the pipes"),
    ("5", "MEM", "MEMORY", "memory",
     "Flip cards, match all pairs in fewest moves"),
    ("6", "REACT", "REACT", "react",
     "Click the dot before it disappears"),
    ("7", "BREAK", "BREAK", "break",
     "Break all the bricks with the paddle"),
]

__all__ = ["GameBase", "GAME_CLASSES", "GAME_META"]
