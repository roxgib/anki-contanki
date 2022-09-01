from __future__ import annotations

from collections import defaultdict
from os import environ

from aqt import gui_hooks, mw
from aqt.qt import QAction, qconnect
from aqt.utils import tooltip, showInfo
from aqt.webview import AnkiWebView


from .icons import IconHighlighter
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
        self.icons = IconHighlighter()
        self.controllers: list[QAction] = list()

        mw.addonManager.setConfigAction(__name__, self.on_config)
        self.config = mw.addonManager.getConfig(__name__)
        self.menuItem = QAction("Controller Options", mw)
        qconnect(self.menuItem.triggered, self.on_config)

        if environ.get("DEBUG"):
            self.setFixedSize(10, 10)
        else:
            self.setFixedSize(0, 0)

        gui_hooks.webview_did_receive_js_message.append(self.on_receive_message)
        self.stdHtml(
            f"""<script type="text/javascript">\n{get_file("controller.js")}\n</script>"""
        )

        self.debug_info = ""
        self.update_debug_info()
        if environ.get("DEBUG"):
            from .tests import run_tests
            run_tests()

    def on_connect(self, buttons: str, axes: str, *con: list[str]) -> None:
        self.reset_controller()
        con = "::".join(con)
        self.len_buttons, self.len_axes = int(buttons), int(axes)
        controller = identify_controller(con, self.len_buttons, self.len_axes)[0]

        if controller:
            self.profile = find_profile(controller, self.len_buttons, self.len_axes)
            tooltip(f"{controller} Connected")
        else:
            self.profile = find_profile(con, self.len_buttons, self.len_axes)
            tooltip("Unknown Controller Connected | " + con)

        self.buttons = [False] * self.len_buttons
        self.axes = [False] * self.len_axes
        self.mods = [False] * len(self.profile.mods)

        mw.form.menuTools.addAction(self.menuItem)
        self.controlsOverlay = ControlsOverlay(
            self.profile, self.config["Large Overlays"]
        )
        self.update_debug_info()

    def on_disconnect(self, *args) -> None:
        if self.controllers is not None:
            for controller in self.controllers:
                mw.form.menuTools.removeAction(controller)
        self.controllers = list()
        self.reset_controller()
        self.update_debug_info()
        tooltip("Controller Disconnected")

    def reset_controller(self) -> None:
        if self.controlsOverlay:
            self.controlsOverlay.disappear()
        mw.form.menuTools.removeAction(self.menuItem)
        self.buttons = self.axes = self.profile = self.controlsOverlay = None
        self.update_debug_info()

    def register_controllers(self, *controllers) -> None:
        for controller in self.controllers:
            mw.form.menuTools.removeAction(controller)
        self.controllers: list[QAction] = list()
        for i, controller in enumerate(controllers):
            con = identify_controller(*(controller.split("%%%")))
            if con is None:
                continue
            self.controllers.append(QAction(con[0], mw))
            qconnect(self.controllers[-1].triggered, partial(self.change_controller, i))
        if len(self.controllers) > 1:
            for controller in self.controllers:
                mw.form.menuTools.addAction(controller)
            tooltip(
                f"{str(len(self.controllers))} controllers detected - pick the one you want to use in the Tools menu."
            )

    def change_controller(self, index: int) -> None:
        self._evalWithCallback(f"connect_controller(indices[{index}]);", None)

    def on_receive_message(self, handled: tuple, message: str, context: str) -> tuple:
        funcs = {
            "on_connect": self.on_connect,
            "on_disconnect": self.on_disconnect,
            "poll": self.poll,
            "register": self.register_controllers,
            "initialise": lambda *args, **kwargs: None,
        }

        if message[:8] == "contanki":
            _, func, *args = message.split("::")
            if func == "message":
                tooltip(str("::".join(args)))
            else:
                funcs[func](*args)
            return (True, None)
        else:
            return handled

    def poll(self, buttons: str, axes: str) -> None:
        state = get_state()
        if state == "NoFocus":
            return

        if self.profile is None:
            self.eval("on_controller_disconnect()")
            return

        buttons: list[bool] = [
            True if button == "true" else False for button in buttons.split(",")
        ]
        axes: list[float] = [float(axis) for axis in axes.split(",")]

        if not buttons:
            self.eval("on_controller_disconnect()")
            return

        mods = tuple(
            buttons[mod] if mod <= len(buttons) 
            else bool(axes[mod - 100]) if 0 <= mod - 100 < len(axes) 
            else False for mod in self.profile.mods
        )

        mod = mods.index(True) + 1 if any(mods) and not all(mods) else 0

        if state == "config":
            for i, value in enumerate(buttons):
                self.buttons[i] = value
                self.icons.set_highlight(i, value)

            for i, axis in enumerate(axes):
                self.icons.set_highlight(i * 2 + 101, axis > 0.5)
                self.icons.set_highlight(i * 2 + 100, axis < -0.5)

            return

        if self.config["Enable Overlays"]:
            if mods != self.mods:
                if any(mods):
                    self.controlsOverlay.appear(mods)
                else:
                    self.controlsOverlay.disappear()

            self.mods = mods

        for i, value in enumerate(buttons):
            if value == self.buttons[i]:
                continue
            if i in self.profile.mods:
                continue
            self.buttons[i] = value
            if value:
                self.profile.do_action(state, mod, i)
            else:
                self.profile.do_release_action(state, mod, i)

        if any(axes):
            self.profile.do_axes_actions(state, mod, axes)

    def on_config(self) -> None:
        if focus := current_window():
            ContankiConfig(focus, self.profile)

    def update_profile(self, profile: Profile) -> None:
        if self.profile:
            self.profile = profile
            self.config = mw.addonManager.getConfig(__name__)
            self.controlsOverlay = ControlsOverlay(
                profile, self.config["Large Overlays"]
            )

    def register_icon(self, index: int, icon: ControlButton) -> None:
        self.icons.register_icon(index, icon)

    def update_debug_info(self):
        self._evalWithCallback("get_controller_info()", self._update_debug_info)

    def _update_debug_info(self, controllers: str):
        if controllers is None:
            self.debug_info = "No controllers detected"
        else:
            self.debug_info = [
                con.split("%") for con in controllers.split("%%%") if con
            ]
