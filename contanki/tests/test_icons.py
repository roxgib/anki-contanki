# pylint: disable=missing-docstring

from ..icons import get_button_icon, ControlButton
from ..mappings import BUTTON_NAMES, AXES_NAMES, BUTTON_ORDER
from . import test

@test
def test_can_get_all_button_icons():
    for controller, buttons in BUTTON_NAMES.items():
        for _, button in buttons.items():
            get_button_icon(controller, button)

@test
def test_control_button():
    control_button = ControlButton('Cross', 'DualShock 4')