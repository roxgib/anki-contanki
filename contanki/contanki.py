from collections import defaultdict
from typing import Tuple

from aqt import QMenu, gui_hooks, mw
from aqt.qt import QAction, qconnect
from aqt.utils import tooltip
from aqt.webview import AnkiWebView

from .actions import *
from .config import *
from .buttons import *
from .funcs import *
from .overlay import *
from .profile import *


class Contanki(AnkiWebView):
    def __init__(self, parent):
        super().__init__(parent=parent)

        self.buttons = self.axes = self.profile = self.controlsOverlay = None
        self.icons = defaultdict(list)
        self.controllers = list() 

        mw.addonManager.setConfigAction(__name__, self.on_config)
        self.config = mw.addonManager.getConfig(__name__)
        self.menuItem = QAction(f"Controller Options", mw)
        qconnect(self.menuItem.triggered, self.on_config)
        
        self.setFixedSize(0,0)
        
        gui_hooks.webview_did_receive_js_message.append(self.on_receive_message)
        self.stdHtml(f"""<script type="text/javascript">\n{get_file("controller.js")}\n</script>""")

    def on_connect(self, buttons: str, axes: str, *con: Tuple[str]) -> None:
        self.reset_controller()
        buttons, axes, con = int(buttons), int(axes), '::'.join(con)
        controller = identifyController(con, buttons, axes)[0]
        
        if controller:
            self.profile = findProfile(controller, buttons, axes)
            tooltip(f'{controller} Connected')
        else:
            self.profile = findProfile(con, buttons, axes)
            tooltip('Unknown Controller Connected | ' + con)

        self.buttons = [False] * buttons
        self.axes = [False] * axes
        self.len_buttons = buttons
        self.len_axes = axes

        self.mods = [False] * len(self.profile.mods)
        mw.form.menuTools.addAction(self.menuItem)
        self.controlsOverlay = ControlsOverlay(self.profile, is_large=self.config['Large Overlays'])

    def on_disconnect(self, *args) -> None:
        if self.controllers is not None:
            for controller in self.controllers:
                mw.form.menuTools.removeAction(controller)
        self.controllers = None
        self.reset_controller()
        tooltip('Controller Disconnected')

    def reset_controller(self) -> None:
        if self.controlsOverlay:
            self.controlsOverlay.disappear()
        mw.form.menuTools.removeAction(self.menuItem)
        self.icons = defaultdict(list)
        self.buttons = self.axes = self.profile = self.controlsOverlay = None

    def register_controllers(self, *controllers) -> None:
        if self.controllers is not None:
            for controller in self.controllers:
                mw.form.menuTools.removeAction(controller)
        controllers = [
            con[1] for controller in controllers
            if (con := identifyController(*(controller.split('%%%')))) is not None
            ]
        if len(controllers) > 1:
            self.controllers = [QAction(controller, mw) for controller in controllers]
            for i, controller in enumerate(self.controllers):
                qconnect(controller.triggered, partial(self.change_controller, i))
                mw.form.menuTools.addAction(controller)
            tooltip(f"{str(len(controllers))} controllers detected - pick the one you want to use in the Tools menu.")

    def change_controller(self, index: int) -> None:
        self._evalWithCallback(f"connect_controller(indices[{index}]);", None)

    def on_receive_message(self, handled: tuple, message: str, context: str) -> tuple:
        funcs = {
            'on_connect':       self.on_connect,
            'on_disconnect':    self.on_disconnect,
            'poll':             self.poll,
            'register':         self.register_controllers, 
            'initialise':       lambda *args, **kwargs: None
        }

        if message[:8] == 'contanki':
            _, func, *args = message.split('::')
            if func == 'message':
                tooltip(str('::'.join(args)))
            else:
                funcs[func](*args)
            return (True, None)
        else:
            return handled

    def poll(self, buttons: str, axes: str) -> None:
        state = get_state()
        if state == 'NoFocus': return
        
        buttons = [True if button == 'true' else False for button in buttons.split(',')]
        axes = [float(axis) for axis in axes.split(',')]

        mods = tuple(
            buttons[mod] if mod < 100 
            else (True if axes[mod-100] else False)
            for mod in self.profile.mods
        )

        mod = mods.index(True) + 1 if any(mods) else 0
        
        if state == 'config':
            for i, value in enumerate(buttons):
                if value == self.buttons[i]: continue
                if i in self.profile.mods: continue
                self.buttons[i] = value
                if i in self.icons:
                    for f in self.icons[i]:
                        f[not(value)]()
            
            if any(axes):
                self.profile.doAxesActions(state, mod, axes)
            
            return

        if self.config['Enable Overlays']:
            if mods != self.mods:
                if any(mods):    
                    self.controlsOverlay.appear(mods)
                else:
                    self.controlsOverlay.disappear()

            self.mods = mods

        for i, value in enumerate(buttons):
            if value == self.buttons[i]: continue
            if i in self.profile.mods: continue
            self.buttons[i] = value
            if value:
                self.profile.doAction(state, mod, i)
            else:
                self.profile.doReleaseAction(state, mod, i)

        if any(axes):
            self.profile.doAxesActions(state, mod, axes)

    def on_config(self) -> None:
        if focus := current_window():
            ContankiConfig(focus, self.profile)

    def update_profile(self, profile: Profile) -> None:
        if self.profile:
            self.profile = profile
            self.config = mw.addonManager.getConfig(__name__)
            self.controlsOverlay = ControlsOverlay(profile, self.config['Large Overlays'])

    def register_icon(self, index: int, on_func: Callable, off_func: Callable) -> None:
        self.icons[index].append((on_func, off_func))