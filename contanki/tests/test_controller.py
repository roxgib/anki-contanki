# pylint: disable=missing-docstring

from ..controller import BUTTON_ORDER, Controller, get_controller_list
from . import test


@test
def test_get_controller_list():
    assert get_controller_list() is not None
    assert get_controller_list() == [
        "DualShock 3",
        "DualShock 4",
        "DualSense",
        "Xbox One",
        "Xbox Series",
        "Xbox 360",
        "Switch Pro",
        "Steam Controller",
        "Joy-Con Right",
        "Joy-Con Left",
        "Joy-Con",
        "Super Nintendo",
        "8BitDo Zero",
        "8BitDo Zero (Direct Input)",
        "8BitDo Lite",
        "8BitDo Pro",
    ]


@test
def test_controller():
    controller = Controller("DualShock 4")
    assert controller.name == "DualShock 4"
    assert controller[0] == "Cross"
    assert controller.button(0) == "Cross"
    assert controller.axis(0) == "Left Stick Horizontal"
    assert controller.axis_button(0) == "Left Stick Left"
    print(controller.get_dpad_buttons())
    assert controller.get_dpad_buttons() == (12, 13, 14, 15)
    assert controller.get_stick_button() == 10
    assert controller.num_buttons == 18
    assert controller.num_axes == 4
    assert controller.has_stick
    assert controller.has_dpad
    assert controller.supported

    controller = Controller("Xbox One")
    assert controller.name == "Xbox One"
    assert controller[0] == "A"
    assert controller.button(0) == "A"
    assert controller.axis(0) == "Left Stick Horizontal"
    assert controller.axis_button(0) == "Left Stick Left"
    assert controller.get_dpad_buttons() == (12, 13, 14, 15)
    assert controller.get_stick_button() == 10
    assert controller.num_buttons == 17
    assert controller.num_axes == 4
    assert controller.has_stick
    assert controller.has_dpad
    assert controller.supported

    controller = Controller("Super Nintendo")
    assert controller.name == "Super Nintendo"
    assert controller[0] == "X"
    assert controller.button(0) == "X"
    assert controller.axis(0) == "D-Pad Horizontal"
    assert controller.axis_button(0) == "D-Pad Up"
    # assert controller.get_dpad_buttons() == (4, 5, 6, 7)  # FIXME
    assert controller.num_buttons == 8
    assert controller.num_axes == 2
    assert not controller.has_stick
    assert controller.has_dpad
    assert controller.supported


@test
def test_button_order_includes_all_buttons():
    buttons = list()
    for controller in get_controller_list():
        buttons.extend(list(Controller(controller).buttons.values()))
    for button in buttons:
        if button not in BUTTON_ORDER:
            print(f"Button {button} not in BUTTON_ORDER")
        assert button in BUTTON_ORDER
