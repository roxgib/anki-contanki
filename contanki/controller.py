from __future__ import annotations

from collections import defaultdict
import json

from .utils import int_keys, get_file

file = get_file("controllers.json")
if file is None:
    raise FileNotFoundError("Could not find controllers.json")
controller_data = int_keys(json.loads(file))


class Controller:
    """Represents a controller, gamepad, or other input device."""

    def __init__(self, controller: str) -> None:
        data = controller_data[controller]
        self.name: str = data["name"]
        self.buttons: dict[int, str] = defaultdict(str, data["buttons"])
        self.axis_buttons: dict[int, str] = defaultdict(str, data["axis_buttons"])
        self.axes: dict[int, str] = defaultdict(str, data["axes"])
        self.num_buttons: int = data["num_buttons"]
        self.num_axes: int = data["num_axes"]
        self.has_stick: bool = data["has_stick"]
        self.has_dpad: bool = data["has_dpad"]
        self.supported: bool = data["supported"]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Controller: {self.name}>"

    def __getitem__(self, index: int) -> str:
        return self.buttons[index]

    def __len__(self) -> tuple[int, int]:
        return self.num_buttons, self.num_axes

    def axis(self, index: int) -> str:
        return self.axes[index]

    def axis_button(self, index: int) -> str:
        return self.axis_buttons[index]

    def button(self, index: int) -> str:
        return self.buttons[index]


def get_controller_list() -> list[str]:
    """Returns a list of all supported controllers."""
    return [controller["name"] for controller in controller_data.values() if controller["supported"]]

BUTTON_ORDER = [
    "Left Shoulder",
    "Right Shoulder",
    "Left Trigger",
    "Right Trigger",
    "L2",
    "R2",
    "Triangle",
    "Circle",
    "Square",
    "Cross",
    "Y",
    "X",
    "B",
    "A",
    "D-Pad Up",
    "D-Pad Down",
    "D-Pad Left",
    "D-Pad Right",
    "Up",
    "Down",
    "Left",
    "Right",
    "Up Arrow",
    "Down Arrow",
    "Left Arrow",
    "Right Arrow",
    "Z",
    "LZ",
    "RZ",
    "Capture",
    "Plus",
    "Minus",
    "Menu",
    "View",
    "Start",
    "Select",
    "Star",
    "Steam",
    "Forward",
    "Back",
    "Xbox",
    "Home",
    "Share",
    "Options",
    "Stick",
    "Left Stick",
    "Right Stick",
    "Left Stick Click",
    "Right Stick Click",
    "Click Left Stick",
    "Click Right Stick",
    "Stick Up",
    "Stick Down",
    "Stick Left",
    "Stick Right",
    "Left Stick",
    "Right Stick",
    "Left Stick Up",
    "Left Stick Down",
    "Left Stick Left",
    "Left Stick Right",
    "Right Track",
    "Left Track Up",
    "Left Track Down",
    "Left Track Left",
    "Left Track Right",
    "Right Stick Up",
    "Right Stick Down",
    "Right Stick Left",
    "Right Stick Right",
    "Right Track Up",
    "Right Track Down",
    "Right Track Left",
    "Right Track Right",
    "Left D-Pad Up",
    "Left D-Pad Down",
    "Left D-Pad Left",
    "Left D-Pad Right",
    "Right D-Pad Up",
    "Right D-Pad Down",
    "Right D-Pad Left",
    "Right D-Pad Right",
    "Left Grip",
    "Right Grip",
    "Pad",
    "PS",
]