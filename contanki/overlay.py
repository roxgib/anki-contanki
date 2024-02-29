"""
Overlays which appear when mod keys are pressed.
"""

from __future__ import annotations

from aqt.qt import (
    QVBoxLayout,
    QWidget,
    Qt,
    QLabel,
    QHBoxLayout,
    QSizePolicy,
    QFont,
)

from .funcs import get_config, get_state
from .utils import State
from .profile import Profile
from .icons import ButtonIcon
from .controller import BUTTON_ORDER


# FIXME: Must be better way to do this
def get_left_right_centre(button: str) -> int:
    """Returns whether to put the button in the left, right, or either side."""
    button = button.lower()
    if "d-pad" in button or "left" in button:
        return 0
    if "right" in button or button in "abxyr":
        return 2
    if button in [
        "cross",
        "circle",
        "square",
        "triangle",
        "r1",
        "r2",
        "options",
        "start",
    ]:
        return 2
    return 0


class ControlsOverlay:
    """Overlay that shows the current actions of the gamepad."""

    def __init__(self, parent: QWidget, profile: Profile):
        self.parent = parent
        self.profile = profile
        config = get_config()
        self.always_shown = config["Overlays Always On"]
        self.is_shown = False

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        left_layout.setSpacing(0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        controller = self.profile.controller
        self.controls: dict[int, OverlayItem] = dict()
        buttons = list(controller.buttons.items())
        axes = [
            (i + 100, b)
            for i, b in controller.axis_buttons.items()
            if self.profile.axes_bindings[i // 2] == "Buttons"
        ]

        inputs = buttons + axes
        for input in inputs:
            if input[1] not in BUTTON_ORDER:
                BUTTON_ORDER.append(input[1])
        inputs.sort(key=lambda inputs: BUTTON_ORDER.index(inputs[1]))

        for index, button in inputs:
            on_left = not get_left_right_centre(button)
            self.controls[index] = OverlayItem(
                index, self.profile, on_left, config["Large Overlays"]
            )

            layout = left_layout if on_left else right_layout
            layout.addWidget(self.controls[index])

        self.rcount = right_layout.count()
        self.lcount = left_layout.count()
        self.left = QWidget(parent)
        self.right = QWidget(parent)
        self.left.setLayout(left_layout)
        self.right.setLayout(right_layout)
        self.left.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.right.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.appear(get_state())
        self.disappear()
        if self.always_shown:
            self.appear(get_state())

    def disappear(self) -> None:
        """Hide the overlay."""
        if not self.always_shown:
            self.left.hide()
            self.right.hide()
            self.is_shown = False

    def appear(self, state: State) -> None:
        """Show the overlay."""
        width = self.parent.width() // 2
        height = self.parent.height() - 10
        self.left.setGeometry(0, 20, width, height)
        self.right.setGeometry(width, 20, width, height)
        self.right.show()
        self.left.show()
        for control in self.controls.values():
            control.appear(state)
        self.is_shown = True

    def close(self):
        """
        Closes the overlay. Needed because if self.always_shown is True,
        the overlay will remain open even after being replaced by an
        updated instance.
        """
        self.always_shown = False
        self.disappear()


class OverlayItem(QWidget):
    """Displays a button icon and the associated action."""

    def __init__(self, button: int, profile: Profile, on_left=True, is_large=False):
        super().__init__()
        self.button = button
        button_name = (
            profile.controller.buttons[button]
            if button in profile.controller.buttons
            else profile.controller.axis_buttons[button - 100]
        )
        self.is_large = is_large
        self.profile = profile
        self.setMaximumHeight(120 if is_large else 80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        align = Qt.AlignmentFlag.AlignLeft if on_left else Qt.AlignmentFlag.AlignRight

        layout = QHBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setAlignment(align)
        if not on_left:
            layout.setDirection(QHBoxLayout.Direction.RightToLeft)

        self.icon = ButtonIcon(self, button_name, profile.controller, is_large)
        self.action = QLabel()
        font = QFont()
        font.setBold(True)
        if is_large:
            font.setPointSize(20)
        self.action.setFont(font)
        self.action.setAlignment(align | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.icon)
        layout.addWidget(self.action)
        self.setLayout(layout)

    def appear(self, state: State):
        """Shows the button, refreshing it in the process."""
        self.hide()
        if text := self.profile.get(state, self.button):
            if self.width() - 300 < len(text) * 8:
                text = text.replace(" ", "\n")
            self.action.setText(text)
            self.update()
            self.show()
