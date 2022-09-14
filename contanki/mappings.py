"""
Maps the controls to the corresponding indices in the Gamepad API.
"""

# For ease of testing, this file should not import any
# Anki modules or Contanki modules other than utils.

import json

from .utils import int_keys, get_file

file = get_file("mappings.json")
if file is None:
    raise FileNotFoundError("Could not find mappings.json")
data = int_keys(json.loads(file))
BUTTON_NAMES: dict[str, dict[int, str]] = data["BUTTON_NAMES"]
AXES_NAMES: dict[str, dict[int, str]] = data["AXES_NAMES"]
BUTTON_ORDER: list[str] = data["BUTTON_ORDER"]
HAS_STICK: dict[str, bool] = data["HAS_STICK"]