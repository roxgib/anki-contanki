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
def test_get_controller_list():
    assert get_controller_list() is not None
    assert sorted(get_controller_list()) == [
        "8BitDo Lite",
        "8BitDo Pro",
        "8BitDo Ultimate",
        "8BitDo Zero (D Input)",
        "8BitDo Zero (X Input)",
        "DualSense",
        "DualShock 3",
        "DualShock 4",
        "Joy-Con",
        "Joy-Con Left",
        "Joy-Con Right",
        "Steam Controller",
        "Steam Deck",
        "Super Nintendo",
        "Switch Pro",
        "Xbox 360",
        "Xbox One",
        "Xbox Series",
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
