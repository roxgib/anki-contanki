from __future__ import annotations
from collections import defaultdict

from os.path import dirname, abspath, join
from weakref import WeakSet

from aqt import mw
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
    QIcon,
)
from aqt.utils import tooltip

from .controller import Controller



def get_button_icon(
    controller: Controller | str, button: str, glow: bool = False
) -> QPixmap:
    """Fetches the icon for a button, and applies glow effect."""
    controller = str(controller)
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


class ButtonIcon(QLabel):
    """A label that displays a button icon."""
    def __init__(
        self,
        parent: QWidget | None,
        button: str,
        controller: Controller,
        index: int = None,
        is_large=False,
    ) -> None:
        super().__init__(parent)
        self.is_large = is_large
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        self.setMaximumHeight(120 if is_large else 60)
        self.setContentsMargins(0, 0, 0, 0)
        self._pixmap = get_button_icon(controller, button)
        self._pixmap_glow = get_button_icon(controller, button, glow=True)
        if index is not None:
            IconHighlighter.register_icon(index, self)
        self.refresh()

    def refresh(self, glow=False):
        """Updates the icon for size and glow."""
        size = self.height()
        if glow:
            pixmap = self._pixmap_glow
        else:
            pixmap = self._pixmap
        self.setPixmap(
            pixmap.scaled(
                size,
                size,
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
                icon.refresh(highlight)
