import os
from time import time
from typing import List

from aqt import mw
from aqt.webview import AnkiWebView
from aqt.utils import tooltip, showInfo
from aqt import gui_hooks

from .funcs import *
from .CONSTS import *
from .help import *
from .config import *

class CSE(AnkiWebView):
    def __init__(self, parent):
        super().__init__(parent=parent)

        self.config = mw.addonManager.getConfig(__name__)['options']

        self.mappings = build_mappings(mw.addonManager.getConfig(__name__)['mappings'])
        addon_path = os.path.dirname(os.path.abspath(__file__))
        self.controlsOverlay = ControlsOverlay(mw, addon_path, self.mappings)

        self.stdHtml(f"""DS4 Support\n<p id="ds4"></p>\n<script type="text/javascript">\n{get_file("controller.js")}\n</script>\n<!DOCTYPE html><body></body></html>""")
        
        self.last = {'time': 0, 'button': 0, 'Left Stick': 0, 'Right Stick': 0}

        self.axes = {
            'Left Stick Horizontal':    False,
            'Left Stick Vertical':      False,
            'Right Stick Horizontal':   False,
            'Right Stick Vertical':     False,
        }

        self.triggers = [False, False]

        self.funcs = {
            'on_connect':               self.on_connect,
            'on_disconnect':            self.on_disconnect,
            'on_button_press':          self.on_button_press,
            'on_button_release':        self.on_button_release,
            'update_triggers':          self.on_update_triggers,
            'update_buttons':           self.on_update_buttons,
            'update_right':             self.on_move_mouse,
            'update_left':              self.on_left_stick,
        }

        gui_hooks.webview_did_receive_js_message.append(self.on_receive_message)
        mw.addonManager.setConfigAction(__name__, lambda: dialogs.open('ControllerConfigEditor'))
        dialogs.register_dialog('ControllerConfigEditor', self.on_config)
        #gui_hooks.focus_did_change.append(lambda _, __: tooltip(get_state()))


    def on_config(self) -> None:
        ControllerConfigEditor(self, self.mappings)


    def update_config(self) -> dict:
        self.mappings = build_mappings(mw.addonManager.getConfig(__name__)['mappings'])
        return self.mappings


    def on_update_buttons(self, buttons: str) -> None:
        buttons = [True if button == 'true' else False for button in buttons.split(',')]
        for i, value in enumerate(buttons):
            if value == self.buttons[i]: continue
            self.buttons[i] = value
            if value:
                self.on_button_press(BUTTONS[i])
            else:
                self.on_button_release(BUTTONS[i])


    def on_button_press(self, button: str) -> None:
        if button == 'L2' or button == 'R2': return
        mapping = self.mappings[get_state()]

        button = ' + '.join(self.get_triggers() + [button])
        if button not in mapping:
            tooltip(f"{button} | '(not mapped)'")
            return
        
        action = mapping[button]
        if action not in func_map:
            tooltip(f"'{action}' not found.")
            return

        tooltip(f"{button} | {action if action else '(not mapped)'}")
        try:
            func_map[action]()
        except Exception as err: 
            showInfo(f"Something went wrong!\n\nButton: {button}\nAction: {action}\n{str(err)}")


    def on_button_release(self, button: str) -> None:
        pass


    def on_move_mouse(self, x: str, y: str) -> None:
        x, y = float(x), float(y)
        if abs(x) + abs(y) < 0.05: return
        cursor = mw.cursor()
        pos = cursor.pos()
        x = pos.x() + quadCurve(x, 8)
        y = pos.y() + quadCurve(y, 8)

        geom = mw.screen().geometry()
        x, y = max(x, geom.x()), max(y, geom.y())
        x, y = min(x, geom.width()), min(y, geom.height())
        
        pos.setX(x)
        pos.setY(y)
        cursor.setPos(pos)


    def on_update_triggers(self, *values: List[str]) -> None:
        T = [True if float(value) > 0.4 else False for value in values]
        if self.triggers == T: return
        self.triggers = T
        if any(T):
            self.controlsOverlay.appear(' + '.join(self.get_triggers()))
        else:
            self.controlsOverlay.disappear()        


    def on_left_stick(self, x: str, y: str) -> None:
        x, y = float(x), float(y)
        abs_x, abs_y = abs(x), abs(y)
        if max(abs_x, abs_y) < 0.08: return
        
        if self.get_triggers() == ['R2']:
            mw.web.eval(f'window.scrollBy({quadCurve(x)}, {quadCurve(y)})')
        
        elif self.timeGuard("Left Stick", max(abs_x, abs_y)):
            return
        
        elif abs_x > abs_y:
            if abs_x < 0.4: return
            if x < 0:
                back()
            else:
                forward()
        else:
            if y < 0:
                keyPress(Qt.Key.Key_Tab, Qt.KeyboardModifier.ShiftModifier)
            else:
                keyPress(Qt.Key.Key_Tab)


    def timeGuard(self, axis: str, value: float) -> bool:
        if (_time := time()) - self.last[axis] > 1 - abs(value): 
            self.last[axis] = _time
            return False
        return True


    def get_triggers(self) -> List[str]:
        triggers = list()
        if self.triggers[0]:
            triggers.append('L2')
        if self.triggers[1]:
            triggers.append('R2')
        return triggers


    def on_connect(self, buttons, *con) -> None:
        self.buttons = [False for i in range(int(buttons))]
        tooltip('Controller Connected | ' + str(con))


    def on_disconnect(self, *args) -> None:
        self.controlsOverlay.disappear()
        tooltip('Controller Disconnected')


    def on_receive_message(self, handled: tuple, message: str, context: str) -> tuple:
        if message[:3] == 'pcs':
            _, func, *values = message.split(':')
            if func == 'message':
                tooltip(str(values))
            else:
                if type(values) != list(): values=list(values)
                self.funcs[func](*values)
            return (True, None)
        else:
            return handled


def initialise() -> None:
    mw.controller = CSE(mw)
    mw.controller.show()
    mw.controller.setFixedSize(0,0)