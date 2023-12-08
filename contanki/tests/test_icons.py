# pylint: disable=missing-docstring

from ..icons import get_button_icon, ButtonIcon
from ..controller import Controller, get_controller_list
from . import test

@test
def test_can_get_all_button_icons():
    for controller in get_controller_list():
        for button in Controller(controller).buttons.values():
            get_button_icon(Controller(controller), button)
            ButtonIcon(None, button, Controller(controller))
