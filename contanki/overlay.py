"""
Overlays which appear when mod keys are pressed.
"""

from __future__ import annotations

from aqt.qt import QLayout, QVBoxLayout, QWidget, Qt, QLabel

from .mappings import BUTTON_NAMES, BUTTON_ORDER
from .utils import State
from .profile import Profile
from .icons import ControlButton


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

    def __init__(self, parent: QWidget, profile: Profile, is_large: bool = False):
        self.parent = parent
        self.profile = profile
        self.left = QWidget(parent)
        self.right = QWidget(parent)

        self.controls = {
            control: ControlButton(
                button, self.profile.controller, on_left=False, is_large=is_large
            )
            for control, button in BUTTON_NAMES[self.profile.controller].items()
            # if control not in self.profile.mods
        }

        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        self.left_layout.setSpacing(0)
        self.right_layout.setSpacing(0)
        self.left_layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        lcount = rcount = 0
        for _, control in sorted(
            self.controls.items(),
            key=lambda control: BUTTON_ORDER.index(control[1].button),
        ):
            if get_left_right_centre(control.button):
                rcount += 1
                control.configure_action(False)
                self.right_layout.addWidget(control)
            else:
                lcount += 1
                control.configure_action(True)
                self.left_layout.addWidget(control)
        self.counts = lcount, rcount
        self.left.setLayout(self.left_layout)
        self.right.setLayout(self.right_layout)

    def disappear(self) -> None:
        """Hide the overlay."""
        self.left.hide()
        self.right.hide()

    def appear(self, state: State, mods: list[int]) -> None:
        """Show the overlay."""
        lcount, rcount = self.counts
        geometry_left = self.parent.geometry()
        geometry_left.setBottom(min(lcount * 80, self.parent.height()))
        geometry_left.setTop(20)
        geometry_left.setLeft(0)
        geometry_left.setRight(self.parent.width() // 2)
        self.left.setGeometry(geometry_left)

        geometry_right = self.parent.geometry()
        geometry_right.setBottom(min(rcount * 80, self.parent.height()))
        geometry_right.setTop(20)
        geometry_right.setLeft(self.parent.width() // 2)
        geometry_right.setRight(self.parent.width())
        self.right.setGeometry(geometry_right)

        mod = 0 if all(mods) else mods.index(True) + 1

        for i, control in self.controls.items():
            if text := self.profile.get(state, mod, i):
                # FIXME: ControlButton method should handle this
                assert isinstance(control.action, QLabel)
                if control.action.height() > text.count(" ") * 25:
                    text = text.replace(" ", "\n")
                control.action.setText(text)
                control.show()
            else:
                control.hide()

        self.left.show()
        self.right.show()

        # FIXME: Why is this needed?
        for _ in range(3):
            self.left.hide()
            self.right.hide()

            for _, control in self.controls.items():
                control.refresh_icon()

            self.left.show()
            self.right.show()
