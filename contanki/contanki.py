"""An add-on for Anki, adding support for controllers and gamepads"""

from __future__ import annotations

from os import environ
from functools import partial
from typing import Callable

from aqt import gui_hooks, mw
from aqt.qt import QAction, qconnect
from aqt.utils import current_window, tooltip
from aqt.webview import AnkiWebView

from .icons import IconHighlighter, ControlButton
from .config import ContankiConfig
from .funcs import get_state, move_mouse_build, scroll_build
from .utils import get_file
from .overlay import ControlsOverlay
from .profile import Profile, identify_controller, find_profile
from .actions import button_actions, release_actions

move_mouse = move_mouse_build()
scroll = scroll_build()
DEBUG = environ.get("DEBUG")

class Contanki(AnkiWebView):
    """Main add-on object. The webview contains JavaScript code that interfaces with
    the controller, and this classes functions handle translating the controller's
    input into actions and handling other aspects of the add-on"""

    profile = None
    controls_overlay = None
    mods = None
    buttons = None
    axes = None
    len_buttons = None
    len_axes = None
    icons = IconHighlighter()
    controllers: list[QAction] = list()
    debug_info = ""

    def __init__(self, parent):
        super().__init__(parent=parent)
        mw.addonManager.setConfigAction(__name__, self.on_config)
        config = mw.addonManager.getConfig(__name__)
        if config is None:
            raise Exception("Unable to load config")
        self.config = config
        self.menu_item = QAction("Controller Options", mw)
        qconnect(self.menu_item.triggered, self.on_config)

        gui_hooks.webview_did_receive_js_message.append(self.on_receive_message)
        script = get_file("controller.js")
        self.stdHtml(f"""<script type="text/javascript">\n{script}\n</script>""")
        self.update_debug_info()

        if DEBUG:
            self.setFixedSize(10, 10)
            from .tests import run_tests  # pylint: disable=import-outside-toplevel
            run_tests()
        else:
            self.setFixedSize(0, 0)


    def on_config(self) -> None:
        """Opens the config dialog"""
        if focus := current_window():
            ContankiConfig(focus, self.profile)

    def on_receive_message(self, handled: tuple, message: str, _context: str) -> tuple:
        """Called when a message is received from the JavaScript interface"""
        funcs: dict[str, Callable] = {
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

    def poll(self, input_buttons: str, input_axes: str) -> None:
        """Handles the polling of the controller"""
        state = get_state()
        if state == "NoFocus":
            return
        if self.profile is None:
            self.eval("on_controller_disconnect()")
            return

        buttons = [button == "true" for button in input_buttons.split(",")]
        axes = [float(axis) for axis in input_axes.split(",")]

        if not buttons:
            self.eval("on_controller_disconnect()")
            return

        mods = tuple(
            buttons[mod]
            if mod <= len(buttons)
            else bool(axes[mod - 100])
            if 0 <= mod - 100 < len(axes)
            else False
            for mod in self.profile.mods
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
                    self.controls_overlay.appear(state, mods)
                else:
                    self.controls_overlay.disappear()
            self.mods = mods

        for i, value in enumerate(buttons):
            if value == self.buttons[i]:
                continue
            self.buttons[i] = value
            if i in self.profile.mods:
                continue
            if value:
                self.do_action(state, mod, i)
            else:
                self.do_release_action(state, mod, i)

        if any(axes):
            self.do_axes_actions(state, mod, axes)

    def do_action(self, state: str, mod: int, button: int) -> None:
        """Calls the appropriate function on button press."""
        if (action := self.profile.get(state, mod, button)) in button_actions:
            try:
                button_actions[action]()
            except Exception as err:  # pylint: disable=broad-except
                tooltip("Error: " + repr(err))

    def do_release_action(self, state: str, mod: int, button: int) -> None:
        """Calls the appropriate function on button release."""
        if (action := self.profile.get(state, mod, button)) in release_actions:
            try:
                release_actions[action]()
            except Exception as err:  # pylint: disable=broad-except
                tooltip("Error: " + repr(err))

    def do_axes_actions(self, state: str, mod: int, axes: list[float]) -> None:
        """Handles actions for axis movement."""
        mouse_x = mouse_y = scroll_x = scroll_y = 0.0
        for (axis, assignment), value in zip(self.profile.axes_bindings.items(), axes):
            if assignment == "Unassigned":
                continue
            elif assignment == "Buttons":
                if abs(value) > 0.5:
                    if not self.axes[axis]:
                        self.do_action(state, mod, axis * 2 + (value > 0) + 100)
                        self.axes[axis] = True
                else:
                    self.axes[axis] = False
            elif assignment == "Scroll Horizontal":
                scroll_x = value
            elif assignment == "Scroll Vertical":
                scroll_y = value
            elif assignment == "Cursor Horizontal":
                mouse_x = value
            elif assignment == "Cursor Vertical":
                mouse_y = value
        if mouse_x or mouse_y:
            try:
                move_mouse(mouse_x, mouse_y)
            except Exception as err:  # pylint: disable=broad-except
                tooltip("Error: " + str(err))
        if scroll_x or scroll_y:
            try:
                scroll(scroll_x, scroll_y)
            except Exception as err:  # pylint: disable=broad-except
                tooltip("Error: " + str(err))

    def on_connect(self, buttons: str, axes: str, *con: str) -> None:
        """Called when a controller is connects through the JavaScript interface"""
        assert mw is not None
        self.reset_controller()
        controller_id = "::".join(con)
        self.len_buttons, self.len_axes = int(buttons), int(axes)
        _controller = identify_controller(
            controller_id, self.len_buttons, self.len_axes
        )
        if _controller is None:
            return
        else:
            controller = _controller[0]

        if controller:
            self.profile = find_profile(controller, self.len_buttons, self.len_axes)
            tooltip(f"{controller} Connected")
        else:
            self.profile = find_profile(controller_id, self.len_buttons, self.len_axes)
            tooltip("Unknown Controller Connected | " + controller_id)

        self.buttons = [False] * self.len_buttons
        self.axes = [False] * self.len_axes
        self.mods = [False] * len(self.profile.mods)

        mw.form.menuTools.addAction(self.menu_item)
        self.controls_overlay = ControlsOverlay(
            mw, self.profile, self.config["Large Overlays"]
        )
        self.update_debug_info()

    def on_disconnect(self, *_) -> None:
        """Called when a controller is disconnected through the JavaScript interface"""
        assert mw is not None
        if self.controllers is not None:
            for controller in self.controllers:
                mw.form.menuTools.removeAction(controller)
        self.controllers = list()
        self.reset_controller()
        self.update_debug_info()
        tooltip("Controller Disconnected")

    def reset_controller(self) -> None:
        """Clears the current controller"""
        assert mw is not None
        if self.controls_overlay:
            self.controls_overlay.disappear()
        mw.form.menuTools.removeAction(self.menu_item)
        self.buttons = self.axes = self.profile = self.controls_overlay = None
        self.update_debug_info()

    def register_controllers(self, *controllers) -> None:
        """
        When multiple controllers are detected, this function adds them to the menu.
        """
        assert mw is not None
        for controller_action in self.controllers:
            mw.form.menuTools.removeAction(controller_action)
        self.controllers = list()
        for i, controller in enumerate(controllers):
            con = identify_controller(*(controller.split("%%%")))
            if con is None:
                continue
            self.controllers.append(QAction(con[0], mw))
            qconnect(self.controllers[-1].triggered, partial(self.change_controller, i))
        if num_controllers := len(self.controllers) <= 1:
            return
        for controller in self.controllers:
            mw.form.menuTools.addAction(controller)
        tooltip(f"{num_controllers} controllers detected - select from the Tools menu.")

    def change_controller(self, index: int) -> None:
        """Calls JavaScript to change the controller"""
        self._evalWithCallback(
            f"connect_controller(indices[{index}]);", None  # type: ignore
        )

    def update_profile(self, profile: Profile) -> None:
        """Updates the profile"""
        assert mw is not None and self.config is not None
        if self.profile:
            self.profile = profile
            self.config = mw.addonManager.getConfig(__name__)
            self.controls_overlay = ControlsOverlay(
                mw, profile, self.config["Large Overlays"]
            )

    def register_icon(self, index: int, icon: ControlButton) -> None:
        """Registers an icon so that it will glow when pressed"""
        self.icons.register_icon(index, icon)

    def update_debug_info(self):
        """Updates the debug info. View by pressing help in the config dialog."""
        self._evalWithCallback("get_controller_info()", self._update_debug_info)

    def _update_debug_info(self, controllers: str):
        """Callback to receive the controller info from the JavaScript interface"""
        if controllers is None:
            self.debug_info = "No controllers detected"
        else:
            self.debug_info = [
                con.split("%") for con in controllers.split("%%%") if con
            ]
