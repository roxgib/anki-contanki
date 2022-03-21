from os import path
from re import S
from typing import List
from aqt import QComboBox, QEvent, QFont, QHBoxLayout, QLabel, QLayout, QObject, QPixmap, QSizePolicy, QWidget, Qt

from .funcs import get_button_icon


class ControlButton(QWidget):
    def __init__(self, button: str, controller: str, on_left: bool = True, actions: List[str] = None) -> None:
        super().__init__()
        self.button = button
        self.layout = QHBoxLayout()
        self.layout.setSpacing(15)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum))
        self.icon = QLabel()
        self.pixmap = get_button_icon(controller, button)
        self.icon.setPixmap(self.pixmap)
        self.icon.setMaximumHeight(60)
        self.icon.setMaximumWidth(60)
        self.icon.setPixmap(
            self.pixmap.scaled(
                self.icon.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            )
        self.icon.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        self.installEventFilter(self)

        if on_left:
            self.configure_action(on_left, actions)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if (source is self):
            self.icon.setPixmap(
                self.pixmap.scaled(
                    self.icon.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                    )
            )
            self.icon.setMaximumWidth(self.icon.height())
        return super().eventFilter(source, event)

    def configure_action(self, on_left: bool = False, actions: List[str] = None) -> None:
        font = QFont()
        font.setBold(True)
        
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
            self.action.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.layout.addWidget(self.action)
            self.layout.addWidget(self.icon)
        
        self.action.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum))
        self.setLayout(self.layout)

    def currentText(self):
        return self.action.currentText()