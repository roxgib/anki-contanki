from os import path
from re import S
from typing import List
from aqt import QComboBox, QFont, QHBoxLayout, QLabel, QPixmap, QWidget, Qt


class ControlButton(QWidget):
    def __init__(self, button: str, controller: str, on_left: bool = True, actions: List[str] = None) -> None:
        super().__init__()
        self.button = button
        self.layout = QHBoxLayout()
        self.layout.setSpacing(15)

        self.icon = QLabel()

        _path = path.join(path.dirname(path.abspath(__file__)), f"buttons/{controller}/{button}.png")
        self.icon.setPixmap(QPixmap(_path).scaledToHeight(50))

        if on_left:
            self.configure_action(on_left, actions)

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
        
        self.setLayout(self.layout)

    def currentText(self):
        return self.action.currentText()