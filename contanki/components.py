from copy import copy
from os import path
from re import S
from typing import List
from aqt import QComboBox, QEvent, QFont, QHBoxLayout, QLabel, QLayout, QObject, QPixmap, QSizePolicy, QWidget, Qt, mw

from .funcs import get_button_icon

class ControlButton(QWidget):
    def __init__(self, button: str, controller: str, on_left: bool = True, actions: List[str] = None) -> None:
        super().__init__()
        self.button = button
        self.layout = QHBoxLayout()
        self.layout.setSpacing(15)
        self.setMaximumHeight(80)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        self.layout.setContentsMargins(1,1,1,1)
        self.icon = QLabel()
        self.pixmap = get_button_icon(controller, button)
        self.pixmap_glow = get_button_icon(controller, button, glow=True)
        self.icon.setPixmap(self.pixmap)
        self.icon.setMaximumHeight(60)
        self.icon.setMaximumWidth(60)
        self.icon.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
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
                self.icon.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
        )

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

    def show_pressed(self):
        self.refresh_icon(True)

    def show_not_pressed(self):
        self.refresh_icon()
    
    def show(self):
        super().show()
        self.refresh_icon()
        super().show()