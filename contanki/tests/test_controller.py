# pylint: disable=missing-docstring

from ..controller import (
    BUTTON_ORDER,
    Controller,
    get_controller_list,
    parse_controller_id,
    identify_controller,
)
from . import test

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


test_ids = [
    "Wireless Controller (STANDARD GAMEPAD Vendor: 054c Product: 0ce6)",
    "Wireless controller (STANDARD GAMEPAD Vendor: 054c Product: 05c4)",
    "Pro Controller (STANDARD GAMEPAD Vendor: 057e Product: 2009)",
    "PS3 GamePad (Vendor: 054c Product: 0268)",
    "PLAYSTATION(R)3 Controller (Vendor: 054c Product: 0268)",
    "Unknown Gamepad (STANDARD GAMEPAD Vendor: 054c Product: 09cc)",
    "Wireless Controller (Vendor: 054c Product: 0ce6)",
    "PLAYSTATION(R)3 Controller (STANDARD GAMEPAD Vendor: 054c Product: 0268)",
    "DualShock 3",
    "Xbox 360 Controller",
    "Invalid Id",
]

test_ids_parsed = [
    ("054c", "0ce6"),
    ("054c", "05c4"),
    ("057e", "2009"),
    ("054c", "0268"),
    ("054c", "0268"),
    ("054c", "09cc"),
    ("054c", "0ce6"),
    ("054c", "0268"),
    (None, None),
    (None, None),
    (None, None),
]


@test
def test_parse_controller_id():
    for test_id, (vendor_id, device_id) in zip(test_ids, test_ids_parsed):
        assert (vendor_id, device_id) == parse_controller_id(test_id)


test_controllers = [
    "DualSense",
    "DualShock 4",
    "Switch Pro",
    "DualShock 3",
    "DualShock 3",
    "DualShock 4",
    "DualSense",
    "DualShock 3",
    "DualShock 3",
    "Xbox 360",
    "Invalid Id",
]


@test
def test_identify_controller():
    for test_id, controller in zip(test_ids, test_controllers):
        result = identify_controller(test_id, 0, 0)
        assert result is not None
        assert result[0] == controller


@test
def test_button_order_includes_all_buttons():
    buttons = list()
    for controller in get_controller_list():
        buttons.extend(list(Controller(controller).buttons.values()))
    for button in buttons:
        if button not in BUTTON_ORDER:
            print(f"Button {button} not in BUTTON_ORDER")
        assert button in BUTTON_ORDER


toml = """\
# This file was generated by Contanki. Do not edit.
name = "8BitDo Pro"
num_buttons = 17
num_axes = 4
has_stick = true
has_dpad = true
supported = true
is_custom = false
parent = "8BitDo Pro"

[buttons]
0 = "B"
1 = "A"
2 = "Y"

[axes]
0 = "Left Stick Horizontal"
1 = "Left Stick Vertical"

[axis_buttons]
0 = "Left Stick Left"
1 = "Left Stick Right"
"""

@test
def test_to_from_toml():
    controller = Controller.from_toml(toml)
    assert controller.name == "8BitDo Pro"
    assert controller.num_buttons == 17
    assert controller.num_axes == 4
    assert controller.has_stick
    assert controller.has_dpad
    assert controller.supported
    assert not controller.is_custom
    assert controller.parent == "8BitDo Pro"
    assert controller.buttons[0] == "B"
    assert controller.axes[0] == "Left Stick Horizontal"
    assert controller.axis_buttons[0] == "Left Stick Left"
    assert controller.to_toml() == toml