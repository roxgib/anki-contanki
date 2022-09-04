"""Contains various functions that are used in multiple places or as Anki actions."""

from __future__ import annotations

import re
import subprocess
from typing import Any, Callable
from functools import partial
from os.path import dirname, abspath, join, exists

from aqt import mw
from aqt.deckoptions import display_options_for_deck_id
from aqt.qt import (
    QCoreApplication,
    QKeySequence,
    QMouseEvent,
    QEvent,
    QPoint,
    QPointF,
    Qt,
)
from aqt.qt import QKeyEvent as QKE
from aqt.utils import current_window, tooltip, supportText
from anki.decks import DeckId

addon_path = dirname(abspath(__file__))

# Internal


def get_state() -> str:
    """
    Returns the current state of the Anki window. Possible values are:
    - 'deck_browser'
    - 'overview'
    - 'question'
    - 'answer'
    - 'dialog'
    - 'config'
    - 'NoFocus'
    Note that instead of 'review', 'question' or 'answer' is returned.
    """
    if focus := current_window():
        if focus.objectName() == "MainWindow":
            return mw.reviewer.state if mw.state == "review" else mw.state
        elif focus.objectName() == "Preferences":
            return "dialog"
        elif focus.objectName() == "Contanki Options":
            return "config"
        else:
            return "NoFocus"
    else:
        return "NoFocus"


def for_states(states: list[str]) -> Callable:
    """
    Decorates functions to be called only when Anki is in one of the given states.
    """

    def decorater(func: Callable) -> Callable:
        def wrapped(*args, **kwargs) -> Any:
            if get_state() in states:
                return func(*args, **kwargs)
            else:
                tooltip("Action not available on this screen")

        return wrapped

    return decorater


def _pass() -> None:
    pass


def quad_curve(value: float, factor: int = 5) -> float:
    """Used to calculate cursor and scroll acceleration."""
    return ((value * factor) ** 2) * value


def _get_dark_mode() -> Callable[[], bool]:
    """Gets the current Anki dark mode setting."""
    # pylint: disable=import-outside-toplevel
    try:
        from aqt.utils import is_mac, is_win
    except ImportError:
        return lambda: False
    if is_win:
        from aqt.theme import get_windows_dark_mode

        return get_windows_dark_mode
    elif is_mac:
        from aqt.theme import get_macos_dark_mode

        return get_macos_dark_mode
    else:
        try:
            from aqt.theme import get_linux_dark_mode

            return get_linux_dark_mode
        except ImportError:
            return lambda: False


get_dark_mode = _get_dark_mode()


def get_custom_actions() -> dict[str, Callable]:
    """Gets custom actions from the config file."""
    config = mw.addonManager.getConfig(__name__)["Custom Actions"]
    actions = dict()
    for action in config.keys():
        keys = QKeySequence(config[action])
        try:
            key = keys[0].key()
            modifier = keys[0].keyboardModifiers()
        except Exception: # pylint: disable=broad-except
            key = keys[0]
            modifier = Qt.KeyboardModifier.NoModifier

        func = partial(key_press, key, modifier)
        actions[action] = func

    return actions


def get_file(file: str) -> str:  # refactor this
    """Gets a file from the addon folder and returns the contents as a string."""
    paths = [
        addon_path,
        join(addon_path, "user_files"),
        join(addon_path, "profiles"),
        join(addon_path, "user_files", "profiles"),
    ]
    for path in paths:
        if exists(join(path, file)):
            with open(join(path, file), "r", encoding="utf8") as file:
                return file.read()


def int_keys(input_dict: dict) -> dict:
    """Converts the keys of a dict to ints when possible."""
    if not isinstance(input_dict, dict):
        return input_dict
    output_dict = dict()
    for key, value in input_dict.items():
        try:
            int(key)
        except ValueError:
            output_dict[key] = int_keys(value)
        else:
            output_dict[int(key)] = int_keys(value)
    return output_dict


# Common


def key_press(key: Qt.Key, mod: Qt.KeyboardModifier = None) -> None:
    """Simulates a key press and release."""
    if mod is None:
        mod = Qt.KeyboardModifier.NoModifier
    QCoreApplication.sendEvent(mw.app.focusObject(), QKE(QKE.Type.KeyPress, key, mod))
    QCoreApplication.sendEvent(mw.app.focusObject(), QKE(QKE.Type.KeyRelease, key, mod))


def select() -> None:
    """Clicks the selected webview UI element"""
    mw.web.eval("document.activeElement.click()")


def tab(value: float = 1) -> None:
    """Simulates pressing the tab key, or Shift-Tab."""
    if value < 0:
        key_press(Qt.Key.Key_Tab, Qt.KeyboardModifier.ShiftModifier)
    elif value > 0:
        key_press(Qt.Key.Key_Tab)


def scroll_build() -> Callable[[float, float], None]:
    """Builds a function that simulates scrolling, accounting for user settings."""
    if mw is None:  # for out of anki profile tests
        return lambda x, y: None
    config = mw.addonManager.getConfig(__name__)
    speed = config["Scroll Speed"] / 10
    deadzone = config["Stick Deadzone"] / 100

    def _scroll(x: float, y: float) -> None:  # pylint: disable=invalid-name
        if abs(x) + abs(y) < deadzone:
            return
        mw.web.eval(f"window.scrollBy({quad_curve(x*speed)}, {quad_curve(y*speed)})")

    return _scroll


scroll = scroll_build()


def move_mouse_build() -> Callable[[float, float], None]:
    """Builds a function that moves the mouse, accounting for user settings."""
    if mw is None:  # for out of anki profile tests
        return lambda x, y: None
    config = mw.addonManager.getConfig(__name__)
    speed = config["Cursor Speed"] / 2
    accel = config["Cursor Acceleration"] / 5
    deadzone = config["Stick Deadzone"] / 100

    def move_mouse(x: float, y: float) -> None:  # pylint: disable=invalid-name
        if abs(x) + abs(y) < deadzone:
            return
        cursor = mw.cursor()
        pos = cursor.pos()
        geom = mw.screen().geometry()

        y = pos.y() + ((abs(y) * speed) ** (accel + 1)) * y
        x = pos.x() + ((abs(x) * speed) ** (accel + 1)) * x
        x, y = max(x, geom.x()), max(y, geom.y())
        x, y = min(x, geom.width()), min(y, geom.height())

        pos.setX(int(x))
        pos.setY(int(y))
        cursor.setPos(pos)

    return move_mouse


def hide_cursor() -> None:
    """Moves the cursor to the bottom left of the screen."""
    size = mw.screen().geometry()
    mw.cursor().setPos(QPoint(size.width(), size.height()))


def _click(
    button=Qt.MouseButton.LeftButton,
    mod=Qt.KeyboardModifier.NoModifier,
    release=False,
) -> None:
    """Simulates a mouse click."""
    pos = mw.cursor().pos()
    widget = mw.app.widgetAt(pos)
    if not widget:
        return

    widget_position = widget.mapToGlobal(QPoint(0, 0))
    local_pos = QPointF(pos.x() - widget_position.x(), pos.y() - widget_position.y())
    QCoreApplication.postEvent(
        widget,
        QMouseEvent(
            QEvent.Type.MouseButtonRelease if release else QEvent.Type.MouseButtonPress,
            local_pos,
            button,
            button,
            mod,
        ),
    )

    if not release:
        mw.web.eval('document.querySelectorAll( ":hover" )[0].click()')


def click(
    button=Qt.MouseButton.LeftButton,
    mod=Qt.KeyboardModifier.NoModifier,
) -> None:
    """Simulates a mouse click."""
    _click(button, mod)


def click_release(
    button=Qt.MouseButton.LeftButton,
    mod=Qt.KeyboardModifier.NoModifier,
) -> None:
    """Simulates a mouse click release."""
    _click(button, mod, True)


def on_enter() -> None:
    """Simulates pressing the enter button."""
    if mw.state == "deckBrowser" or mw.state == "overview":
        select()
    elif mw.state == "review":
        mw.reviewer.onEnterKey()
    else:
        key_press(Qt.Key.Key_Enter)


@for_states(["deckBrowser", "review", "overview", "question", "answer"])
def forward() -> None:
    """Takes the user from deck browser to overview to review"""
    if mw.state == "deckBrowser":
        mw.moveToState("overview")
    elif mw.state == "overview":
        mw.moveToState("review")


@for_states(["deckBrowser", "review", "overview", "question", "answer"])
def back() -> None:
    """Takes the user from review to overview to deckBrowser"""
    if mw.state == "review":
        mw.moveToState("overview")
    else:
        mw.moveToState("deckBrowser")


@for_states(["deckBrowser", "review", "overview", "question", "answer"])
def on_options() -> None:
    """Shows the deck options or main preferences depending on context."""

    def deck_options(did: str) -> None:
        try:
            display_options_for_deck_id(DeckId(int(did)))
        except Exception: # pylint: disable=broad-except
            mw.onPrefs()

    if mw.state == "review":
        mw.reviewer.onOptions()
    elif mw.state == "deckBrowser":
        mw.web.evalWithCallback(
            "document.activeElement.parentElement.parentElement.id", deck_options
        )
    elif mw.state == "overview":
        display_options_for_deck_id(mw.col.decks.get_current_id())


@for_states(["deckBrowser", "review", "overview", "question", "answer"])
def toggle_fullscreen() -> None:
    """Toggles the fullscreen mode."""
    if window := current_window().window():
        if window.isFullScreen():
            window.showNormal()
        else:
            window.showFullScreen()


def undo():
    """Triggers Anki's undo action."""
    if mw.undo_actions_info().can_undo:
        mw.undo()
    else:
        tooltip("Nothing to undo")


def redo():
    """Triggers Anki's redo action."""
    if mw.undo_actions_info().can_redo:
        mw.redo()
    else:
        tooltip("Nothing to redo")


#FIXME: this is terrible, find a better way
def change_volume(direction=True):
    """Changes the volume by a small amount. Only works on Mac"""
    try:
        from aqt.utils import is_mac  # pylint: disable=import-outside-toplevel
    except ImportError:
        return

    if is_mac:
        current_volume = re.search(
            r"volume:(\d\d)",
            subprocess.run(
                'osascript -e "get volume settings"',
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            ).stdout,
        )
        if current_volume:
            current_volume = int(current_volume.group(1)) / 14
            current_volume += -0.5 + int(direction)
            subprocess.run(
                f'osascript -e "set volume {current_volume}"',
                shell=True,
                check=False,
            )


### Review


def build_cycle_flag() -> Callable:
    """Builds a function that cycles through the configured flags."""
    flags = mw.addonManager.getConfig(__name__)["Flags"]

    @for_states(["question", "answer"])
    def _cycle_flag(flags):
        """Cycles through the configured flags."""
        flag = mw.reviewer.card.flags
        if flag == 0:
            mw.reviewer.setFlag(flags[0])
        elif flag not in flags:
            mw.reviewer.setFlag(0)
        elif flag == flags[-1]:
            mw.reviewer.setFlag(0)
        else:
            mw.reviewer.setFlag(flags[flags.index(flag) + 1])

    return lambda: _cycle_flag(flags)


cycle_flag = build_cycle_flag()


def build_previous_card_info():
    """Builds a function that returns the previous card's info."""
    try:
        _previous_card_info = mw.reviewer.on_previous_card_info
    except NameError:
        # for Anki <= 2.1.49
        return lambda: tooltip("This action is only available in Anki 2.1.50+")
    return for_states(["question", "answer"])(_previous_card_info)


card_info = for_states(["question", "answer"])(mw.reviewer.on_card_info)
previous_card_info = build_previous_card_info()


### Deck Browser


def _build_deck_list() -> tuple[list[int], list[bool]]:
    """
    Builds a list of deck ids and a list showing whether the decks have due cards.
    """
    def _build_node(node):
        decks = [
            (node.deck_id, node.review_count or node.learn_count or node.new_count)
        ]
        if node.children:
            if not node.collapsed:
                for child in node.children:
                    decks.extend(_build_node(child))
        return decks

    decks = list()
    for child in mw.col.sched.deck_due_tree().children:
        decks.extend(_build_node(child))

    decks, dues = zip(*decks)
    return decks, dues


def _select_deck(did) -> None:
    mw.web.eval(
        f"document.getElementById({did}).getElementsByClassName('deck')[0].focus()"
    )


def _choose_deck(c_deck: int, direction: bool, due: bool) -> None:
    c_deck = int(c_deck) if c_deck else None
    decks, dues = _build_deck_list()
    len_decks = len(decks)

    if not len_decks:
        return

    if due and not any(dues):
        return

    if c_deck == decks[-1]:
        c_deck_index = -1
    elif c_deck in decks:
        c_deck_index = decks.index(c_deck)
    else:
        c_deck_index = -direction

    c_deck_index += 1 if direction else -1
    while due and not dues[c_deck_index]:
        c_deck_index += 1 if direction else -1
        if c_deck_index == len_decks:
            c_deck_index = -1
        if decks[c_deck_index] == 1:
            c_deck_index += 1 if direction else -1

    if len_decks == 1:
        c_deck_index = 0

    if mw.state == "deckBrowser":
        _select_deck(decks[c_deck_index])
    else:
        mw.col.decks.select(decks[c_deck_index])
        mw.moveToState("overview")


@for_states(["deckBrowser", "overview"])
def choose_deck(direction: bool, due: bool = False) -> None:
    """Change the selected deck in either the deck browser or the overview."""
    mw.web.setFocus()

    if mw.state == "deckBrowser":
        mw.web.evalWithCallback(
            "document.activeElement.parentElement.parentElement.id",
            lambda c_deck: _choose_deck(c_deck, direction, due),
        )
    else:
        _choose_deck(mw.col.decks.get_current_id(), direction, due)


@for_states(["deckBrowser"])
def collapse_deck() -> None:
    """Collapses the currently selected deck."""
    mw.web.eval(
        "document.activeElement.parentElement.getElementsByClassName('collapse')[0].click()" # pylint: disable=line-too-long
    )


def get_debug_str() -> str:
    """Returns a string with debug information."""
    # pylint: disable=line-too-long
    result = """See the <a href="https://ankiweb.net/shared/info/1898790263">add-on page</a> for some tips on using Contanki. If you're having trouble or have found a bug you can post on the <a href="https://forums.ankiweb.net/t/contanki-official-support-thread/">official support thread</a> or the <a href="https://github.com/roxgib/anki-contanki/issues">GitHub issue tracker</a>. <br><br>Please copy and paste the following information into your post:<br><br>"""
    result += supportText().replace("\n", "<br>")
    num_controllers = len(mw.contanki.debug_info)
    result += f"<br>{num_controllers} controller{'' if num_controllers == 1 else 's'} detected{':' if num_controllers > 0 else '.'}<br>"
    for controller_id, num_buttons, num_axes in mw.contanki.debug_info:
        result += f"{controller_id}<br>Buttons: {num_buttons}<br>Axes: {num_axes}<br><br>"
    return result
