"""
Provides utility functions.
"""

# For ease of testing, this file should not import from outside the standard library.

from __future__ import annotations

from typing import Callable, Literal
from os.path import join, dirname, abspath, exists

addon_path = dirname(abspath(__file__))

State = Literal[
    "all",
    "deckBrowser",
    "overview",
    "review",
    "question",
    "answer",
    "dialog",
    "config",
    "NoFocus",
]


def get_file(filename: str) -> str | None:  # FIXME: refactor this
    """Gets a file from the addon folder and returns the contents as a string."""
    paths = [
        addon_path,
        join(addon_path, "user_files"),
        join(addon_path, "profiles"),
        join(addon_path, "user_files", "profiles"),
    ]
    for path in paths:
        if exists(join(path, filename)):
            with open(join(path, filename), "r", encoding="utf8") as file:
                return file.read()
    return None


def int_keys(input_dict: dict) -> dict:
    """Converts the keys of a dict to ints when possible."""
    if not isinstance(input_dict, dict):
        return input_dict
    output_dict = dict()
    for key, value in input_dict.items():
        try:
            int(key)
        except (ValueError, TypeError):
            output_dict[key] = int_keys(value)
        else:
            output_dict[int(key)] = int_keys(value)
    return output_dict


def if_connected(func: Callable) -> Callable:
    def if_connected_wrapper(self, *args, **kwargs):
        if self.connected:
            func(self, *args, **kwargs)
    return if_connected_wrapper