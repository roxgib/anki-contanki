import os
from time import time

from aqt import mw
from aqt.webview import AnkiWebView
from aqt.utils import tooltip
from aqt import gui_hooks

from .funcs import _get_state
from .funcs import *
from .CONSTS import *
from .help import *

class DS4(AnkiWebView):
    def __init__(self, parent):
        super().__init__(parent=parent)

        self.config = mw.addonManager.getConfig(__name__)
        self.last = {'time':0, 'button':0}

        self.states = {
            "startup": None,
            "deckBrowser": self.config['deckBrowser'],
            "overview": self.config['overview'],
            "profileManager": None,
            'question': self.config['question'],
            'answer': self.config['answer'],
        }
        
        addon_path = os.path.dirname(os.path.abspath(__file__))
        
        with open(os.path.join(addon_path, "controller.js"), 'r') as f:
            html = f"""DS4 Support\n<p id="ds4"></p>\n<script type="text/javascript">\n{f.read()}\n</script>\n<!DOCTYPE html><body></body></html>"""

        self.stdHtml(html)
        self.controlsOverlay = ControlsOverlay(mw, addon_path)

        self.axes = {
            'LEFT_H': False,
            'LEFT_V': False,
            'RIGHT_H': False,
            'RIGHT_V': False,
            'L2': False,
            'R2': False,
        }

        self.funcs = {
            'on_connect': self.on_connect,
            'on_button_press': self.on_button_press,
            'on_update_axis': self.on_update_axis,
        }

        gui_hooks.webview_did_receive_js_message.append(self.on_receive_message)

    def on_button_press(self, button):
        if self.last['button'] == button:
            if time() - self.last['time'] < 0.3:
                return

        self.last['time'] = time()
        self.last['button'] = button

        axes = self.get_shoulders()
        axes.append(BUTTONS[button])
        button = ' + '.join(axes)
        
        action = self.states[_get_state()][button]
        func_map[action]()

        tooltip(f"""Button: {button} | Action: {action}""")

    def on_update_axis(self, axis: str, _value: str) -> None:
        value = float(_value)
        if axis == '2':
            if abs(value) > 0.05:
                cursor = mw.cursor()
                pos = cursor.pos()
                pos.setX(pos.x() + value * 10)
                cursor.setPos(pos)
        elif axis == '3':
            if abs(value) > 0.1:
                cursor = mw.cursor()
                pos = cursor.pos()
                pos.setY(pos.y() + value * 10)
                cursor.setPos(pos)
        elif axis == '4' or axis == '5':
            value = True if value > 0.4 else False
            if self.axes[AXES[axis]] != value:
                self.axes[AXES[axis]] = value
                self.on_shoulder()

    def on_shoulder(self) -> None:
        if len((shoulders := self.get_shoulders())) > 0:
            self.controlsOverlay.appear(' + '.join(shoulders))
        else:
            self.controlsOverlay.disappear()

    def get_shoulders(self) -> list:
        axes = list()
        if self.axes['L2'] == True:
            axes.append('L2')
        if self.axes['R2'] == True:
            axes.append('R2')
        return axes

    def on_connect(self, *con):
        if con == '(None,)':
            tooltip('No controller connected')
        else:
            tooltip('Controller Connected | ' + str(con))
        
    def on_receive_message(self, handled, message, context):
        if message[:3] == 'ds4':
            _, func, *values = message.split(':')
            if func == 'message':
                tooltip(values)
            else:
                if type(values) != list(): values=list(values)
                self.funcs[func](*values)
            return (True, None)
        else:
            return handled

def initialise():
    mw.controller = DS4(mw)
    mw.controller.show()
    mw.controller.setFixedSize(0,0)