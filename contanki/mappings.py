"""Maps the controls to the corresponding indices in the Gamepad API. """

from __future__ import annotations
import json

from .funcs import int_keys, get_file

data = int_keys(json.loads(get_file('mappings.json')))
BUTTON_NAMES = data["BUTTON_NAMES"]
AXES_NAMES = data["AXES_NAMES"]
BUTTON_ORDER = data["BUTTON_ORDER"]
