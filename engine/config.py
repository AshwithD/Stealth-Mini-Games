"""Configuration and settings persistence.

Settings live in ``settings.json`` next to the executable (or next to the
script when running from source). Values from the file are merged over the
defaults, so upgrading the app never loses user settings.
"""
import json
import os
import sys

# ----------------------------------------------------------------------
# Defaults. "pixels_per_cm" is the one knob that maps the window to a real
# physical size: window_pixels = target_cm * pixels_per_cm.
# See README.md for the calibration table.
# ----------------------------------------------------------------------
DEFAULT_CONFIG = {
    "title": "Mini Games",
    "target_cm": 3.0,
    "pixels_per_cm": 38,
    "always_on_top": False,
    "fps": 60,
    "version": "3.0.0",
}

_SETTINGS_FILE = "settings.json"

# Keys we accept from the user file, with validators.
_VALIDATORS = {
    "title": lambda v: str(v) if str(v) else DEFAULT_CONFIG["title"],
    "target_cm": lambda v: float(v)
                      if 1.0 <= float(v) <= 10.0
                      else DEFAULT_CONFIG["target_cm"],
    "pixels_per_cm": lambda v: int(v)
                        if 10 <= int(v) <= 200
                        else DEFAULT_CONFIG["pixels_per_cm"],
    "always_on_top": lambda v: bool(v),
    "fps": lambda v: int(v) if 20 <= int(v) <= 144
                    else DEFAULT_CONFIG["fps"],
}


def base_dir():
    """Directory next to the executable / script (where data files live)."""
    try:
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    except Exception:
        return os.getcwd()


def settings_path():
    return os.path.join(base_dir(), _SETTINGS_FILE)


def load_settings(path=None):
    """Load settings.json merged over defaults; never raises.

    ``path`` overrides the default location (useful for tests).
    """
    cfg = dict(DEFAULT_CONFIG)
    path = path or settings_path()
    try:
        with open(path) as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            for key, value in data.items():
                validator = _VALIDATORS.get(key)
                if validator is not None:
                    try:
                        cfg[key] = validator(value)
                    except Exception:
                        pass  # keep default for malformed values
    except Exception:
        pass
    return cfg


def save_settings(cfg, path=None):
    """Persist the supported subset of settings; never raises."""
    out = {}
    for key in _VALIDATORS:
        if key in cfg:
            out[key] = cfg[key]
    try:
        with open(path or settings_path(), "w") as fh:
            json.dump(out, fh, indent=2)
    except Exception:
        pass


def window_size(cfg):
    """Pixel size of the on-screen window for a given config."""
    return int(round(cfg["target_cm"] * cfg["pixels_per_cm"]))
