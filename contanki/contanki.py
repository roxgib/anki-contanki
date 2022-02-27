from time import time

from aqt import gui_hooks, mw
from aqt.qt import QAction, qconnect
from aqt.utils import tooltip
from aqt.webview import AnkiWebView

from .actions import *
from .config import *
from .config_new import *
from .CONSTS import *
from .funcs import *
from .overlay import *
from .profile import *


class Contanki(AnkiWebView):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.profile = None

        self.stdHtml(f"""<script type="text/javascript">\n{get_file("controller.js")}\n</script>\n<!DOCTYPE html><body></body></html>""")

        self.funcs = {
            'on_connect':               self.on_connect,
            'on_disconnect':            self.on_disconnect,
            'poll':                     self.poll,
        }

        gui_hooks.webview_did_receive_js_message.append(self.on_receive_message)
        mw.addonManager.setConfigAction(__name__, lambda: dialogs.open('ControllerConfigEditor'))
        dialogs.register_dialog('ControllerConfigEditor', self.on_config)
        self.setFixedSize(0,0)
        self.show()


    def on_connect(self, buttons: str, axes:str, *con: List[str]) -> None:
        buttons, axes, con = int(buttons), int(axes), '::'.join(con)
        controller = identifyController(con, buttons, axes)

        self.buttons = [False] * buttons
        self.axes = [False] * axes
        self.len_buttons = buttons
        self.len_axes = axes
        
        if controller:
            self.controller = controller
            self.profile = findProfile(controller, buttons, axes)
            tooltip(f'{controller} Connected')
        else:
            self.controller = "DualShock 4"
            self.profile = findProfile(con, buttons, axes)
            tooltip('Unknown Controller Connected | ' + con)
 
        menuItem = QAction(f"Controller Options", mw)
        qconnect(menuItem.triggered, self.on_config)
        mw.form.menuTools.addAction(menuItem)
        #self.controlsOverlay = ControlsOverlay(mw, addon_path, self.profile)


    def on_disconnect(self, *args) -> None:
        # self.controlsOverlay.disappear()
        tooltip('Controller Disconnected')
        self.buttons = self.axes = self.profile = self.controlsOverlay = None


    def on_receive_message(self, handled: tuple, message: str, context: str) -> tuple:
        if message[:8] == 'contanki':
            _, func, *args = message.split('::')
            if func == 'message':
                tooltip(str(args[0]))
            else:
                if type(args) != list(): args=list(args)
                self.funcs[func](*args)
            return (True, None)
        else:
            return handled
            
    
    def on_config(self) -> None:
        ContankiConfig(mw, self.profile)


    def poll(self, buttons, axes):
        buttons = [True if button == 'true' else False for button in buttons.split(',')]
        axes = [float(axis) for axis in axes.split(',')]
        state = get_state()

        mods = tuple(
            buttons[mod] if mod < 100 
            else (True if axes[mod-100] else False)
            for mod in self.profile.mods
        )

        # if mods != self.mods:
        #     if any(mods):    
        #         self.controlsOverlay.appear(mods)
        #     else:
        #         self.controlsOverlay.disappear()

        self.mods = mods

        mod = mods.index(True) + 1 if any(mods) else 0

        for i, value in enumerate(buttons):
            if value == self.buttons[i]: continue
            self.buttons[i] = value
            if value:
                self.profile.doAction(state, mod, i)
            else:
                self.profile.doReleaseAction(state, mod, i)

        if any(axes):
            self.profile.doAxesActions(state, mod, axes)


    def timeGuard(self, axis: str, value: float) -> bool:
        if (_time := time()) - self.last[axis] > 1 - abs(value): 
            self.last[axis] = _time
            return False
        return True