from aqt.qt import QLayout, QVBoxLayout, QWidget, Qt
from aqt import mw

from .buttons import BUTTON_NAMES, BUTTON_ORDER
from .funcs import get_state
from .profile import Profile
from .icons import ControlButton

def get_left_right_centre(button: str) -> int:
    button = button.lower()
    if "d-pad" in button:
        return 0
    if 'left' in button:
        return 0
    if 'right' in button:
        return 2
    if button in 'abxyr':
        return 2 
    if button in ['cross', 'circle', 'square', 'triangle', 'r1', 'r2', 'options', 'start']:
        return 2
    return 0


class ControlsOverlay():
    def __init__(self, profile: Profile, is_large: bool = False):
        self.profile = profile
        self.actions = profile.getInheritedBindings()
        self.left = QWidget(mw)
        self.right = QWidget(mw)
        
        self.controls = {
            control: ControlButton(button, self.profile.controller, on_left=False, is_large=is_large)
            for control, button 
            in BUTTON_NAMES[self.profile.controller].items()
            # if control not in self.profile.mods
        }

        self.left.layout = QVBoxLayout()
        self.right.layout = QVBoxLayout()
        self.left.layout.setSpacing(0) 
        self.right.layout.setSpacing(0)
        self.left.layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.right.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.left.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        lcount = rcount = 0
        for i, control in sorted(self.controls.items(), key = lambda control: BUTTON_ORDER.index(control[1].button)):
            if get_left_right_centre(control.button):
                rcount += 1
                control.configure_action(False)
                self.right.layout.addWidget(control)
            else:
                lcount += 1
                control.configure_action(True)
                self.left.layout.addWidget(control)
        self.counts = lcount, rcount
        self.left.setLayout(self.left.layout)
        self.right.setLayout(self.right.layout)
        
    def disappear(self) -> None:
        self.left.hide()
        self.right.hide()

    def appear(self, mods: int) -> None:
        state = get_state()
        if state not in self.actions: return

        lcount, rcount = self.counts
        geometry_left = mw.geometry()
        geometry_left.setBottom(min(lcount * 80, mw.height()))
        geometry_left.setTop(20)
        geometry_left.setLeft(0)
        geometry_left.setRight(mw.width() // 2)
        self.left.setGeometry(geometry_left)

        geometry_right = mw.geometry()
        geometry_right.setBottom(min(rcount * 80, mw.height()))
        geometry_right.setTop(20)
        geometry_right.setLeft(mw.width() // 2)
        geometry_right.setRight(mw.width())
        self.right.setGeometry(geometry_right)

        mod = 0 if all(mods) else mods.index(True) + 1

        for i, control in self.controls.items():
            if i in self.actions[state][mod]:
                if control.action.height() > ((text := self.actions[state][mod][i]).count(' ') * 25):
                    control.action.setText(text.replace(' ', '\n'))
                else:
                    control.action.setText(text)
            else:
                control.action.setText("")
            
            if control.action.text() == '':
                control.hide()
            else:
                control.show()

        self.left.show()
        self.right.show()

        for i in range(3):
            self.left.hide()
            self.right.hide()

            for i, control in self.controls.items():
                control.refresh_icon()

            self.left.show()
            self.right.show()