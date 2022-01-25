import os

from aqt import mw

from aqt.webview import AnkiWebView
from aqt.utils import qconnect, QAction, tooltip
from aqt import gui_hooks

from .CONSTS import *
from .funcs import *

addon_path = os.path.dirname(os.path.abspath(__file__))

class ds4(AnkiWebView):
    def __init__(self, parent):
        super().__init__(parent=parent)

        with open(os.path.join(addon_path, "controller.js"), 'r') as f:
            html = f"""DS4 Support\n<p id="ds4"></p>\n<script type="text/javascript">\n{f.read()}\n</script>\n<!DOCTYPE html><body></body></html>"""
        self.stdHtml(html)

        self.axes = {}
        # self.button_pressed.connect(self.on_button_pressed)
        # self.bindings = config['bindings']

        self.funcs = {
            'on_connect': self.on_connect,
            'on_button_press': self.on_button_press,
            'on_update_axis': self.on_update_axis,
        }
        gui_hooks.webview_did_receive_js_message.append(self.on_receive_message)

    def on_button_press(self, button):
        tooltip('button_pressed: ' + self.active_axis() + ' | ' + button)
        func_map[config_map[(self.active_axis(), button)]]()


    def on_update_axis(self, axis, value):
        self.axes[AXES[axis]] = float(value)

    def on_connect(self, *con):
        if con == 'None':
            tooltip('No controller connected')
        else:
            tooltip('Controller Connected | ' + str(con))

    def active_axis(self):
        axes = list()
        if self.axes['L2'] > 0.6:
            axes.append('L2')
        if self.axes['R2'] > 0.6:
            axes.append('R2')
        
        return ' & '.join(axes)
        
    def on_receive_message(self, handled, message, context):
        mod, func, *values = message.split(':')
        if mod == 'ds4':
            if func == 'message':
                tooltip(values)
                return (True, None)
            else:
                self.funcs[func](*values)
                return (True, None)
        else:
            return handled

def initialise():
    mw.controller = ds4(mw)
    mw.controller.show()
    mw.controller.setFixedSize(200, 500)
    mw.controller.setFocus()

