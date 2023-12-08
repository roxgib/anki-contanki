from __future__ import annotations
from collections import defaultdict

from os.path import dirname, abspath, join
from weakref import WeakSet

from aqt import mw
from aqt.qt import (
    QFont,
    QLabel,
    QSizePolicy,
    QWidget,
    Qt,
    QPixmap,
    QPainter,
    QColor,
    QGraphicsColorizeEffect,
)
from aqt.utils import tooltip

from .controller import Controller


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


def icon_path(folder, file):
    return join(dirname(abspath(__file__)), "buttons", folder, file)


def get_button_icon(controller: Controller, button: str) -> QPixmap:
    """Fetches the icon for a button, and applies glow effect."""
    controller_name = str(controller.parent)
    if "(" in controller_name:
        controller_name = controller_name.split(" (")[0]
    pixmap = QPixmap(icon_path("Other", "background.png"))
    with QPainter(pixmap) as painter:
        if not (icon := QPixmap(icon_path(controller_name, button))).isNull():
            painter.drawPixmap(pixmap.rect(), icon, icon.rect())
        elif (
            button
            and button != "Not Assigned"
            and (direction := button.split(" ")[-1]) in directions
            and (button := " ".join(button.split(" ")[:-1]))
            and not (icon := QPixmap(icon_path(controller_name, button))).isNull()
            and not (dpixmap := QPixmap(icon_path("Arrows", direction))).isNull()
        ):
            painter.drawPixmap(pixmap.rect(), icon, icon.rect())
            painter.drawPixmap(pixmap.rect(), dpixmap, dpixmap.rect())
        else:
            painter.setFont(QFont("Arial", 20))
            painter.drawText(
                pixmap.rect(), Qt.AlignmentFlag.AlignCenter, button.replace(" ", "\n")
            )
            if button and button != "Not Assigned":
                tooltip(f"Error: Couldn't load {button} icon for {controller_name}.")
    return pixmap


class ButtonIcon(QLabel):
    """A label that displays a button icon."""

    def __init__(
        self,
        parent: QWidget | None,
        button: str,
        controller: Controller,
        index: int | None = None,
        is_large=False,
    ) -> None:
        super().__init__(parent)
        self.is_large = is_large
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        self.setMaximumHeight(120 if is_large else 60)
        self.setContentsMargins(0, 0, 0, 0)
        self._pixmap = get_button_icon(controller, button)
        if index is not None:
            IconHighlighter.register_icon(index, self)
        self.colorize_effect = QGraphicsColorizeEffect()
        self.colorize_effect.setColor(QColor(255, 255, 255, 128))
        self.setGraphicsEffect(self.colorize_effect)
        self.glow(False)
        self.resizeEvent(None)

    def glow(self, glow=False):
        """Updates the icon for size and glow."""
        self.colorize_effect.setEnabled(glow)

    def resizeEvent(self, event):
        self.setPixmap(
            self._pixmap.scaled(
                self.height(),
                self.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )


class IconHighlighter:
    """Manages the highlighting of icons."""

    icons: defaultdict[int, WeakSet[ButtonIcon]] = defaultdict(WeakSet)

    @classmethod
    def register_icon(cls, index: int, icon: ButtonIcon) -> None:
        """Registers an icon to be highlighted when pressed."""
        cls.icons[index].add(icon)

    def set_highlight(self, index: int, highlight: bool) -> None:
        """Sets the highlight for an icon."""
        if index in self.icons:
            for icon in self.icons[index]:
                icon.glow(highlight)
