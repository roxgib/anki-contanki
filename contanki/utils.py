"""
Provides utility functions.
"""

# For ease of testing, this file should not import from outside the standard library.

from __future__ import annotations

from typing import Literal
from os.path import join, dirname, abspath, exists
from os import environ

DEBUG = environ.get("DEBUG")

addon_path = dirname(abspath(__file__))
user_files_path = join(addon_path, "user_files")
user_profile_path = join(user_files_path, "profiles")
default_profile_path = join(addon_path, "profiles")
controllers_path = join(addon_path, "controllers")

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


def get_file(filename: str) -> str | None:
    """Gets a file from the addon folder and returns the contents as a string."""
    paths = [addon_path, user_files_path, user_profile_path, default_profile_path]
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

def dbg(value):
    """Prints a value if in debugging mode. ."""
    if DEBUG:
        print(f"Contanki: {value}")
    return value
