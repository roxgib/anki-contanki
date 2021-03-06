from __future__ import annotations

from os.path import dirname, abspath, join, exists

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


def get_button_icon(controller: str, button: str, glow: bool = False) -> QPixmap:
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
        # not sure how or why, but the last icon will still be there, so we need to clear it
        pixmap.fill(QColor(255, 255, 255, 255))
        with QPainter(pixmap) as painter:
            painter.setFont(QFont("Arial", 20))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, button.replace(" ", "\n"))
        tooltip(f"Error: Couldn't load {button} icon for {controller}.")
        return pixmap

    if glow:
        gpixmap = QPixmap(path("Other", "glow"))
        with QPainter(pixmap) as painter:
            painter.drawPixmap(pixmap.rect(), gpixmap, gpixmap.rect())

    return pixmap


class ControlButton(QWidget):
    def __init__(
        self,
        button: str,
        controller: str,
        on_left: bool = True,
        actions: list[str] = None,
        is_large: bool = False,
    ) -> None:
        super().__init__()
        self.button = button
        self.is_large = is_large
        self.layout = QHBoxLayout()
        self.layout.setSpacing(15)
        self.setMaximumHeight(120 if is_large else 80)
        self.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.icon = QLabel()
        self.pixmap = get_button_icon(controller, button)
        self.pixmap_glow = get_button_icon(controller, button, glow=True)
        self.icon.setPixmap(self.pixmap)
        self.icon.setMaximumHeight(60)
        self.icon.setMaximumWidth(60)
        self.icon.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
        self.refresh_icon()

        if on_left:
            self.configure_action(on_left, actions)

    def refresh_icon(self, on=False):
        self.icon.setMaximumWidth(self.icon.height())
        if on:
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

    def configure_action(
        self, on_left: bool = False, actions: list[str] = None
    ) -> None:
        font = QFont()
        font.setBold(True)
        if self.is_large:
            font.setPointSize(20)

        if actions:
            self.action = QComboBox()
            self.action.addItems(actions)
        else:
            self.action = QLabel()
            self.action.setFont(font)

        if on_left:
            self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.layout.addWidget(self.icon)
            self.layout.addWidget(self.action)
        else:
            self.layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.action.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.layout.addWidget(self.action)
            self.layout.addWidget(self.icon)

        self.action.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        )
        self.setLayout(self.layout)

    def currentText(self):
        return self.action.currentText()

    def show_pressed(self):
        self.refresh_icon(True)

    def show_not_pressed(self):
        self.refresh_icon()

    def show(self):
        super().show()
        self.refresh_icon()
        super().show()
