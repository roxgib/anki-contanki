"""An add-on for Anki, adding support for controllers and gamepads"""

from __future__ import annotations

from functools import partial
from typing import Any, Callable
from collections import defaultdict

from aqt import gui_hooks
from aqt.qt import QAction, qconnect
from aqt.utils import current_window, tooltip
from aqt.webview import AnkiWebView

from .quick import QuickSelectMenu
from .icons import IconHighlighter
from .config import ContankiConfig
from .funcs import (
    get_config,
    get_custom_actions,
    get_state,
    move_mouse_build,
    scroll_build,
)
from .utils import State, get_file, DEBUG, dbg
from .overlay import ControlsOverlay
from .controller import identify_controller
from .profile import (
    Profile,
    get_profile,
    find_profile,
)
from .actions import button_actions, release_actions, update_actions

from aqt import mw as _mw

assert _mw is not None
mw = _mw

move_mouse = move_mouse_build()
scroll = scroll_build()


class Contanki(AnkiWebView):
    """Main add-on object. The webview contains JavaScript code that interfaces with
    the controller, and this classes functions handle translating the controller's
    input into actions and handling other aspects of the add-on"""

    connected = False
    config = get_config()
    overlay = None
    quick_select = QuickSelectMenu(None, {})
    buttons: list[bool] = []
    axes: list[bool] = []
    len_buttons = 0
    len_axes = 0
    icons = IconHighlighter()
    controllers: list[QAction] = list()
    debug_info: list[list[str]] = []
    custom_actions = get_custom_actions()
    script: str = get_file("controller.js")

    def __init__(self, parent):
        super().__init__(parent=parent)
        mw.addonManager.setConfigAction(__name__, self.on_config)
        self.menu_item = QAction("Controller Options", mw)
        qconnect(self.menu_item.triggered, self.on_config)
        gui_hooks.webview_did_receive_js_message.append(self.on_receive_message)
        gui_hooks.profile_will_close.append(self.suspend)
        gui_hooks.profile_did_open.append(self.resume)
        self.resume()
        self.update_debug_info()
        self.profile = None

        if DEBUG:
            self.setFixedSize(10, 10)
            from .tests import run_tests  # pylint: disable=import-outside-toplevel

            run_tests()
        else:
            self.setFixedSize(0, 0)

    def suspend(self):
        """Suspends JS execution. Necessary to prevent crash when Anki exits."""
        self.stdHtml("")

    def resume(self):
        """Resumes the add-on"""
        self.stdHtml(f"""<script type="text/javascript">\n{self.script}\n</script>""")

    @property
    def profile(self) -> Profile | None:
        """Returns the profile object"""
        return self._profile

    @profile.setter
    def profile(self, profile: Profile | str | None) -> None:
        """Sets the profile object"""
        self.config = get_config()
        if isinstance(profile, str):
            profile = get_profile(profile)
        self._profile = profile
        if profile is None:
            return
        if self.overlay is not None:
            self.overlay.close()
        if self.quick_select is not None:
            self.hide_quick_select()
        self.overlay = ControlsOverlay(mw, profile)
        self.quick_select = QuickSelectMenu(self, profile.quick_select)
        self.quick_select.update_icon(profile.controller)
        update_actions()
        globals()["move_mouse"] = move_mouse_build()
        globals()["scroll"] = scroll_build()
        self.custom_actions = get_custom_actions()

    def on_config(self) -> None:
        """Opens the config dialog"""
        if focus := current_window():
            ContankiConfig(focus, self.profile)

    def on_receive_message(
        self, handled: tuple[bool, Any], message: str, _
    ) -> tuple[bool, Any]:
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

    def on_error(self, _error: str) -> None:
        """Reinitialises the controller when an error occurs."""
        self.eval("on_controller_disconnect()")

    def if_connected(func: Callable) -> Callable:  # pylint: disable=no-self-argument
        """Checks if the controller is connected before running a function."""

        def if_connected_wrapper(self, *args, **kwargs):
            if self.connected:
                func(self, *args, **kwargs)
            else:
                dbg(f"Function '{func}' blocked, controller not connected")

        return if_connected_wrapper

    @if_connected
    def poll(self, input_buttons: str, input_axes: str) -> None:
        """Handles the polling of the controller"""
        state = get_state()
        if state == "NoFocus":
            return
        if self.profile is None:
            self.on_error("No profile")
            return

        buttons = [button == "true" for button in input_buttons.split(",")]
        axes = [float(axis) for axis in input_axes.split(",")]

        if not buttons:
            self.on_error("No buttons")
            return

        if state == "config":
            for i, value in enumerate(buttons):
                if self.buttons[i] != value:
                    self.buttons[i] = value
                    self.icons.set_highlight(i, value)
            for i, axis in enumerate(axes):
                self.icons.set_highlight(i * 2 + 101, axis > 0.5)
                self.icons.set_highlight(i * 2 + 100, axis < -0.5)
            return

        self.update_quick_select(state, buttons, axes)

        for i, value in enumerate(buttons):
            if len(self.buttons) > i and value == self.buttons[i]:
                continue
            if len(self.buttons) <= i:
                self.buttons.append(value)
            else:
                self.buttons[i] = value
            if value:
                self.do_action(state, i)
            else:
                self.do_release_action(state, i)

        if any(axes) and not self.quick_select.is_shown:
            self.do_axes_actions(state, axes)

        assert self.overlay is not None
        if self.config["Overlays Always On"]:
            self.overlay.appear(state)

    @if_connected
    def update_quick_select(
        self, state: State, buttons: list[bool], axes: list[float]
    ) -> None:
        """Update the quick select menu."""
        assert self.profile is not None
        assert self.overlay is not None
        if not self.quick_select.is_shown:
            return

        if (
            self.quick_select.settings["Select with D-Pad"]
            and self.profile.controller.dpad_buttons is not None
            and any(buttons[index] for index in self.profile.controller.dpad_buttons)
        ):
            up, down, left, right = self.profile.controller.dpad_buttons
            dpad_status = buttons[up], buttons[down], buttons[left], buttons[right]
            self.quick_select.dpad_select(state, dpad_status)
            for index in self.profile.controller.dpad_buttons:
                self.buttons[index] = buttons[index]
        elif self.profile.controller.has_stick:
            self.quick_select.stick_select(state, axes[0], axes[1])

        if (
            (stick_button := self.profile.controller.stick_button) is not None
            and self.quick_select.settings["Do Action on Stick Press"]
            and buttons[stick_button]
        ):
            self.quick_select.disappear(True)
            self.buttons[stick_button] = buttons[stick_button]
        elif buttons[0]:
            self.quick_select.disappear(True)
            self.buttons[0] = buttons[0]

    @if_connected
    def show_quick_select(self, state: State) -> None:
        """Shows the quick select menu"""
        if not self.quick_select.is_shown:
            self.quick_select.appear(state)
        if (
            self.overlay is not None
            and self.config["Enable Control Overlays"]
            and self.config["Overlays in Quick Select"]
        ):
            self.overlay.appear(state)

    @if_connected
    def hide_quick_select(self) -> None:
        """Hides the quick select menu and the overlays if they are shown."""
        self.quick_select.disappear()
        self.axes = [True] * self.len_axes
        if self.overlay is not None:
            self.overlay.disappear()

    @if_connected
    def toggle_quick_select(self, state: State) -> None:
        """Toggles the quick select menu and overlays."""
        if self.quick_select.is_shown or (
            self.overlay is not None
            and self.overlay.is_shown
            and not self.config["Overlays Always On"]
        ):
            self.hide_quick_select()
        else:
            self.show_quick_select(state)

    @if_connected
    def do_action(self, state: State, button: int) -> None:
        """Calls the appropriate function on button press."""
        if self.profile is None:
            self.on_error("No profile")
            return
        action = self.profile.get(state, button)
        if action == "Toggle Quick Select":
            self.toggle_quick_select(state)
        elif action == "Show Quick Select":
            self.show_quick_select(state)
        else:
            try:
                if action in button_actions:
                    button_actions[action]()
                elif action in self.custom_actions:
                    self.custom_actions[action]()
            except Exception as err:  # pylint: disable=broad-except
                tooltip("Error: " + repr(err))

    @if_connected
    def do_release_action(self, state: State, button: int) -> None:
        """Calls the appropriate function on button release."""
        if self.profile is None:
            self.on_error("No profile")
            return
        action = self.profile.get(state, button)
        if action == "Show Quick Select":
            self.hide_quick_select()
        elif (action := self.profile.get(state, button)) in release_actions:
            try:
                release_actions[action]()
            except Exception as err:  # pylint: disable=broad-except
                tooltip("Error: " + repr(err))

    @if_connected
    def do_axes_actions(self, state: State, axes: list[float]) -> None:
        """Handles actions for axis movement."""
        movements = defaultdict(float)
        for axis, assignment in self.profile.axes_bindings.items():
            if axis >= len(axes):
                continue
            value = axes[axis]
            if assignment == "Buttons":
                if abs(value) > 0.5 and not self.axes[axis]:
                    self.do_action(state, axis * 2 + (value > 0) + 100)
                self.axes[axis] = abs(value) > 0.5
            else:
                movements[assignment] = value * (-1 if self.profile.invert_axis[axis] else 1)
        try:
            move_mouse(movements["Cursor Horizontal"], movements["Cursor Vertical"])
            scroll(movements["Scroll Horizontal"], movements["Scroll Vertical"])
        except Exception as err:  # pylint: disable=broad-except
            tooltip("Error: " + str(err))

    def on_connect(self, buttons: str | int, axes: str | int, *con: str) -> None:
        """Called when a controller connects through the JavaScript interface"""
        self.reset_controller()
        controller_id = "::".join(con)
        buttons, axes = int(buttons), int(axes)

        _controller = identify_controller(
            controller_id,
            buttons,
            axes,
            self.config["Detect 8BitDo Controllers"],
        )
        if _controller is None:
            return
        else:
            controller = _controller[0]

        if controller:
            profile = find_profile(controller, self.len_buttons, self.len_axes)
            tooltip(f"{controller} Connected")
        else:
            profile = find_profile(controller_id, self.len_buttons, self.len_axes)
            tooltip("Unknown Controller Connected: " + controller_id)
        self.profile = get_profile(profile)

        self.len_buttons, self.len_axes = buttons, axes
        self.buttons = [False] * self.len_buttons
        self.axes = [False] * self.len_axes

        mw.form.menuTools.addAction(self.menu_item)
        self.update_debug_info()
        self.connected = True

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
        self.connected = False

    def reset_controller(self) -> None:
        """Clears the current controller"""
        if self.overlay:
            self.overlay.disappear()
        self.quick_select.disappear()
        mw.form.menuTools.removeAction(self.menu_item)
        self.buttons = []
        self.axes = []
        self.profile = None
        self.update_debug_info()

    def register_controllers(self, *controllers) -> None:
        """
        When multiple controllers are detected, this function adds them to the menu.
        """
        assert mw is not None
        for controller_action in self.controllers:
            mw.form.menuTools.removeAction(controller_action)
        self.controllers.clear()
        for i, controller in enumerate(controllers):
            con = identify_controller(
                *(controller.split("%%%")), self.config["Detect 8BitDo Controllers"]
            )
            if con is None:
                continue
            self.controllers.append(QAction(con[0], mw))
            qconnect(self.controllers[-1].triggered, partial(self.change_controller, i))
        if len(self.controllers) <= 1:
            return
        for controller in self.controllers:
            mw.form.menuTools.addAction(controller)
        tooltip(
            f"{len(self.controllers)} controllers detected - select from the Tools menu."
        )

    @if_connected
    def change_controller(self, index: int, _) -> None:
        """Calls JavaScript to change the controller"""
        self._evalWithCallback(
            f"connect_controller(indices[{index}]);", None  # type: ignore
        )

    def update_debug_info(self):
        """Updates the debug info. View by pressing help in the config dialog."""
        self._evalWithCallback("get_controller_info()", self._update_debug_info)

    def _update_debug_info(self, controllers: str) -> None:
        """Callback to receive the controller info from the JavaScript interface"""
        if controllers is None:
            self.debug_info: list[list[str]] = []
        else:
            self.debug_info = [
                con.split("%") for con in controllers.split("%%%") if con
            ]
        dbg(self.debug_info)
