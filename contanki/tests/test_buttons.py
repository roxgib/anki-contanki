from ..buttons import BUTTON_NAMES, AXES_NAMES, BUTTON_ORDER
from . import test


@test
def test_button_order_includes_all_buttons():
    buttons = list()
    for _, controller in BUTTON_NAMES.items():
        for _, button in controller.items():
            buttons.append(button)
    
    for button in buttons:
        assert button in BUTTON_ORDER
