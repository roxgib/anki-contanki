from ..icons import get_button_icon, ControlButton
from ..buttons import BUTTON_NAMES, AXES_NAMES, BUTTON_ORDER
from . import test

@test
def test_can_get_button_icons():
    for controller, buttons in BUTTON_NAMES.items():
        for _, button in buttons.items():
            get_button_icon(controller, button)