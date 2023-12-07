"""
Quick select menu.
"""

from __future__ import annotations

from math import atan, sin, cos, pi, tau, sqrt
from typing import Any

from aqt.theme import theme_manager
from aqt.qt import Qt, QLabel, QRect, QPoint, QSize, QFont
from aqt import mw as _mw

from .funcs import get_config
from .utils import State
from .icons import get_button_icon
from .actions import button_actions
from .controller import Controller

HALF_PI = pi / 2
QUARTER_PI = pi / 4
assert _mw is not None
mw = _mw

LIGHT = """
    background-color: #ddd;
    color: #000;
    border-radius: 10px;
    border: 2px solid #000;
"""

DARK = """
    background-color: #555;
    color: #fff;
    border-radius: 10px;
    border: 2px solid #000;
"""

SELECTED_LIGHT = """
    background-color: #ddd;
    color: #000;
    border-radius: 10px;
    border: 5px solid #000;
"""

SELECTED_DARK = """
    background-color: #555;
    color: #fff;
    border-radius: 10px;
    border: 2px solid #fff;
"""


class QuickSelectMenu:
    """Quick select menu allowing user to access less common actions."""

    # pylint: disable=invalid-name
    settings = {
        "Enable Quick Select": True,
        "Select with Stick": True,
        "Select with D-Pad": True,
        "Do Action on Release": True,
        "Do Action on Stick Press": True,
        "Do Action on Stick Flick": False,
        "actions": {
            "review": [],
            "deckBrowser": [],
            "overview": [],
        },
    }
    buttons: dict[str, list[QuickSelectButton]] = {
        "review": [],
        "deckBrowser": [],
        "overview}": [],
    }
    positions: dict[str, list[tuple[float, float]]] = {
        "review": [],
        "deckBrowser": [],
        "overview}": [],
    }
    CENTRE_SIZE = 150
    centre = QLabel(mw)
    centre.setAlignment(Qt.AlignmentFlag.AlignCenter)
    centre.hide()
    config = get_config()
    countdown = -1
    is_shown = False
    current_action = ""
    dpad_pressed = False
    activation_distance = 0.75

    def __init__(self, contanki, settings: dict[str, Any]):
        self.is_active = contanki is not None
        self.contanki = contanki
        self.settings.update(settings)

        self.actions: dict[str, list[str]] = self.settings["actions"]  # type: ignore
        for state in ("review", "deckBrowser", "overview"):
            self.actions[state] = self.actions[state][:8]  # Maximum of 8 actions
            self.buttons[state] = [
                QuickSelectButton(mw, action) for action in self.actions[state]
            ]
            self.positions[state] = self.set_geometry(self.actions[state])

    def update_icon(self, controller: Controller):
        """Update the centre icon of the quick select menu."""
        button = (
            "D-Pad"
            if not self.settings["Select with Stick"] or not controller.has_stick
            else "Left Stick"
            if controller.num_axes == 4
            else "Stick"
        )
        self.centre.setPixmap(
            get_button_icon(controller, button).scaled(
                150,
                150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def set_geometry(self, actions: list[str]) -> list[tuple[float, float]]:
        """Get the arc size of each button when using a dpad."""
        angles = [
            0.0,
            pi,
            HALF_PI,
            pi + HALF_PI,
            QUARTER_PI + pi / 20,
            HALF_PI + QUARTER_PI - pi / 20,
            pi + QUARTER_PI + pi / 20,
            tau - QUARTER_PI - pi / 20,
        ]
        angles = sorted(angles[: len(actions)])

        distances = list()
        for action, angle in zip(actions, angles):
            height, width = self.get_size(action)
            x, y = self.get_cart(angle, 1)
            x, y = abs(x), abs(y)
            distances.append(
                50
                # + width * int(y) / 2
                # + height * int(x) / 2
                + (60 if len(actions) > 4 else 40)
            )
        print(list(zip(angles, distances)))

        return list(zip(angles, distances))

    def get_geometry(self, state: State) -> list[QPoint]:
        """Get the geometry of the quick select menu."""
        x, y = mw.geometry().width() // 2, mw.geometry().height() - 200
        return [
            QPoint(*self.get_cart(angle, radius, x, y))
            for angle, radius in self.positions[state]
        ]

    def appear(self, state: State):
        """Show the quick select menu."""
        if state in ("question", "answer"):
            state = "review"
        if self.is_shown or not self.is_active or not self.buttons[state]:
            return
        for action, location in zip(self.buttons[state], self.get_geometry(state)):
            action.place(location)
        self.place_centre()
        self.is_shown = True

    def disappear(self, do_action: bool = False):
        """Hide the quick select menu."""
        if not self.is_active:
            return
        for actions in self.buttons.values():
            for action in actions:
                action.hide()
        self.centre.hide()
        if (
            self.is_active
            and (do_action or self.settings["Do Action on Release"])
            and self.current_action
            and self.current_action in button_actions
        ):
            button_actions[self.current_action]()
        self.current_action = ""
        if self.contanki.overlay is not None:
            self.contanki.overlay.disappear()
        self.is_shown = False

    def place_centre(self):
        """Place the centre icon."""
        x, y = mw.geometry().width() // 2 - 75, mw.geometry().height() - 275
        self.centre.setGeometry(QRect(x, y, 150, 150))
        self.centre.show()

    def dpad_select(self, state, pad: tuple[bool, bool, bool, bool]) -> None:
        """Select an action based on D-pad input."""
        if not self.settings["Select with D-Pad"]:
            return
        self.dpad_pressed = True
        if state in ("question", "answer"):
            state = "review"
        if not self.is_shown or not self.is_active or state not in self.buttons:
            return
        up, down, left, right = pad
        angle = self.get_angle(right - left, up - down)
        distances = [
            self.get_angle_distance(angle, _angle)
            for _angle, _ in self.positions[state]
        ]
        if (min_d := min(distances)) < QUARTER_PI:
            index = distances.index(min_d)
            self.current_action = self.actions[state][index]
        else:
            index = -1
        self._select(state, index)

    def stick_select(self, state: State, x: float, y: float) -> None:
        """Select an action based on stick input."""
        if not self.settings["Select with Stick"]:
            return
        if state in ("question", "answer"):
            state = "review"
        if not self.is_shown or not self.is_active or state not in self.buttons:
            return
        y = -y
        if x**2 + y**2 > self.activation_distance:
            angle = self.get_angle(x, y)
            distances = [
                self.get_angle_distance(angle, _angle)
                for _angle, _ in self.positions[state]
            ]
            if (min_d := min(distances)) < QUARTER_PI:
                index = distances.index(min_d)
                self.current_action = self.actions[state][index]
            else:
                index = -1
        else:
            if (
                self.settings["Do Action on Stick Flick"]
                and not self.dpad_pressed
                and self.current_action
                and x**2 + y**2 < 0.1
            ):
                self.disappear(True)
                return
            index = -1
            self.current_action = ""
        self.dpad_pressed = False
        self._select(state, index)

    def _select(self, state: State, index: int) -> None:
        for i, action in enumerate(self.buttons[state]):
            action.selected(i == index)

    @staticmethod
    def get_size(action: str) -> tuple[int, int]:
        """Returns the height and width of the action name."""
        _action = action.split(" ")
        return len(_action) * 12 + 30, max(len(word) for word in _action) * 5 + 40

    @staticmethod
    def get_cart(angle: float, radius: float, x=0, y=0) -> tuple[int, int]:
        """Convert polar coordinates to cartesian."""
        angle -= HALF_PI
        return int(radius * cos(angle) + x), int(radius * sin(angle) + y)

    @staticmethod
    def get_angle_distance(angle1: float, angle2: float) -> float:
        """Get the angular distance."""
        distance = abs(angle1 - angle2)
        return min(distance, abs(tau - distance))

    @staticmethod
    def get_angle(x: float, y: float) -> float:
        """Get the angle from centre for the cartesian coordinates."""
        if not x:
            return 0.0 if y > 0 else pi
        angle = HALF_PI - atan(y / x)
        if x < 0:
            angle += pi
        return angle


class QuickSelectButton(QLabel):
    """Menu item of QuickSelectMenu."""

    standard_font = QFont()
    standard_font.setBold(True)

    large_font = QFont()
    large_font.setBold(True)
    large_font.setPointSize(20)

    def __init__(self, parent, action: str, is_large=False):
        super().__init__(action.replace(" ", "\n"), parent)
        self.action = action
        self._height, self._width = QuickSelectMenu.get_size(action)
        self.setFont(self.large_font if is_large else self.standard_font)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def place(self, location: QPoint) -> None:
        """Place the menu item on the screen"""
        location.setX(location.x() - self._width // 2)
        location.setY(location.y() - self._height // 2)
        self.setGeometry(QRect(location, QSize(self._width, self._height)))
        self.show()

    def selected(self, selected: bool):
        """Glow the menu item."""
        if theme_manager.night_mode:
            self.setStyleSheet(SELECTED_DARK if selected else DARK)
        else:
            self.setStyleSheet(SELECTED_LIGHT if selected else LIGHT)
        self.show()
