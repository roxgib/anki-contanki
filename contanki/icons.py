from __future__ import annotations
from collections import defaultdict

from os.path import dirname, abspath, join
from weakref import WeakSet

from aqt import (
    QComboBox,
    QFont,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
    Qt,
    QPixmap,
    QPainter,
    QColor,
)
from aqt.utils import tooltip

ExpaningPolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


def get_button_icon(controller: str, button: str, glow: bool = False) -> QPixmap:
    """Fetches the icon for a button, and applies glow effect."""
    if "(" in controller:
        controller = controller.split(" (")[0]
    directions = [
        "Left",
        "Right",
        "Up",
        "Down",
        "Horizontal",
        "Vertical",
        "Diagonal",
        "UpLeft",
        "UpRight",
        "DownLeft",
        "DownRight",
        "HorizontalVertical",
    ]

    def path(folder, file):
        return join(dirname(abspath(__file__)), "buttons", folder, file)

    pixmap = QPixmap(path(controller, button))
    if pixmap.isNull() and button.split(" ")[-1] in directions:
        direction = button.split(" ")[-1]
        button = " ".join(button.split(" ")[:-1])
        pixmap = QPixmap(path(controller, button))
        if not pixmap.isNull():
            dpixmap = QPixmap(path("Arrows", direction))
            with QPainter(pixmap) as painter:
                painter.drawPixmap(pixmap.rect(), dpixmap, dpixmap.rect())
    if pixmap.isNull():
        pixmap = QPixmap(100, 100)
        # not sure how or why, but the last icon will still be there, so we clear it
        pixmap.fill(QColor(255, 255, 255, 255))
        with QPainter(pixmap) as painter:
            painter.setFont(QFont("Arial", 20))
            painter.drawText(
                pixmap.rect(), Qt.AlignmentFlag.AlignCenter, button.replace(" ", "\n")
            )
        tooltip(f"Error: Couldn't load {button} icon for {controller}.")
        return pixmap

    if glow:
        gpixmap = QPixmap(path("Other", "glow"))
        with QPainter(pixmap) as painter:
            painter.drawPixmap(pixmap.rect(), gpixmap, gpixmap.rect())

    return pixmap


class ControlButton(QWidget):
    """Displays a button icon, and optionally a dropdown to select an action."""

    def __init__(
        self,
        button: str,
        controller: str,
        on_left=True,
        actions: list[str] = None,
        is_large=False,
    ) -> None:
        super().__init__()
        self.button = button
        self.is_large = is_large
        self._layout = QHBoxLayout()
        self._layout.setSpacing(15)
        self.setMaximumHeight(120 if is_large else 80)
        self.setSizePolicy(ExpaningPolicy)
        self._layout.setContentsMargins(1, 1, 1, 1)
        self.icon = QLabel()
        self.pixmap = get_button_icon(controller, button)
        self.pixmap_glow = get_button_icon(controller, button, glow=True)
        self.icon.setPixmap(self.pixmap)
        self.icon.setMaximumHeight(60)
        self.icon.setMaximumWidth(60)
        self.icon.setSizePolicy(ExpaningPolicy)
        self.refresh_icon()

        if on_left:
            self.configure_action(on_left, actions)

    def refresh_icon(self, glow=False):
        """Updates the icon for size and glow."""
        self.icon.setMaximumWidth(self.icon.height())
        if glow:
            pixmap = self.pixmap_glow
        else:
            pixmap = self.pixmap
        self.icon.setPixmap(
            pixmap.scaled(
                self.icon.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def configure_action(self, on_left=False, actions: list[str] = None) -> None:
        """Configures the action dropdown menu."""
        font = QFont()
        font.setBold(True)
        if self.is_large:
            font.setPointSize(20)

        if actions:
            self.action: QComboBox | QLabel = QComboBox()
            self.action.addItems(actions)
            self.currentText = self.action.currentText  # pylint: disable=invalid-name
        else:
            self.action = QLabel()
            self.action.setFont(font)

        if on_left:
            self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self._layout.addWidget(self.icon)
            self._layout.addWidget(self.action)
        else:
            self._layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.action.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self._layout.addWidget(self.action)
            self._layout.addWidget(self.icon)

        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.action.setSizePolicy(policy)
        self.setLayout(self._layout)

    def show(self):
        """Shows the button, refreshing it in the process."""
        super().show()
        self.refresh_icon()
        super().show()


class IconHighlighter:
    """Manages the highlighting of icons."""

    def __init__(self) -> None:
        self.icons: defaultdict[int, WeakSet[ControlButton]] = defaultdict(WeakSet)

    def register_icon(self, index: int, icon: ControlButton) -> None:
        """Registers an icon to be highlighted when pressed."""
        self.icons[index].add(icon)

    def set_highlight(self, index: int, highlight: bool) -> None:
        """Sets the highlight for an icon."""
        if index in self.icons:
            for icon in self.icons[index]:
                icon.refresh_icon(highlight)
