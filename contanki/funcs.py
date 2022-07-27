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
    QPixmap,
    QPoint,
    QPointF,
    Qt,
    QPainter,
)
from aqt.qt import QKeyEvent as QKE
from aqt.utils import current_window, tooltip
from anki.decks import DeckId

addon_path = dirname(abspath(__file__))

# Internal

def get_state() -> str:
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
    return ((value * factor) ** 2) * value


def _get_dark_mode() -> Callable:
    try:
        from aqt.utils import is_mac, is_win
    except:
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
        except:
            return lambda: False


get_dark_mode = _get_dark_mode()


def get_custom_actions() -> dict[str, Callable]:
    config = mw.addonManager.getConfig(__name__)["Custom Actions"]
    actions = dict()
    for action in config.keys():
        keys = QKeySequence(config[action])
        try:
            key = keys[0].key()
            modifier = keys[0].keyboardModifiers()
        except:
            key = keys[0]
            modifier = Qt.KeyboardModifier.NoModifier

        func = partial(keyPress, key, modifier)
        actions[action] = func

    return actions


def get_file(file: str) -> str:  # refactor this
    paths = [
        addon_path,
        join(addon_path, "user_files"),
        join(addon_path, "profiles"),
        join(addon_path, "user_files", "profiles"),
    ]
    for path in paths:
        if exists(join(path, file)):
            with open(join(path, file)) as f:
                return f.read()


# Common


def keyPress(
    key: Qt.Key, mod: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier
) -> None:
    QCoreApplication.sendEvent(mw.app.focusObject(), QKE(QKE.Type.KeyPress, key, mod))
    QCoreApplication.sendEvent(mw.app.focusObject(), QKE(QKE.Type.KeyRelease, key, mod))


def select() -> None:
    mw.web.eval("document.activeElement.click()")


def tab(value: float = 1) -> None:
    if value < 0:
        keyPress(Qt.Key.Key_Tab, Qt.KeyboardModifier.ShiftModifier)
    elif value > 0:
        keyPress(Qt.Key.Key_Tab)


def scroll_build() -> Callable:
    config = mw.addonManager.getConfig(__name__)
    speed = config["Scroll Speed"] / 10
    deadzone = config["Stick Deadzone"] / 100

    def scroll(x: float, y: float) -> None:
        if abs(x) + abs(y) < deadzone:
            return
        mw.web.eval(f"window.scrollBy({quad_curve(x*speed)}, {quad_curve(y*speed)})")

    return scroll


scroll = scroll_build()


def move_mouse_build() -> Callable:
    config = mw.addonManager.getConfig(__name__)
    speed = config["Cursor Speed"] / 2
    accel = config["Cursor Acceleration"] / 5
    deadzone = config["Stick Deadzone"] / 100

    def move_mouse(x: float, y: float) -> None:
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
    size = mw.screen().geometry()
    mw.cursor().setPos(QPoint(size.width(), size.height()))


def click(
    button: Qt.MouseButton = Qt.MouseButton.LeftButton,
    mod: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    pos = mw.cursor().pos()
    widget = mw.app.widgetAt(pos)
    if not widget:
        return

    widgetPostition = widget.mapToGlobal(QPoint(0, 0))
    localPos = QPointF(pos.x() - widgetPostition.x(), pos.y() - widgetPostition.y())
    QCoreApplication.postEvent(
        widget, QMouseEvent(QEvent.Type.MouseButtonPress, localPos, button, button, mod)
    )

    mw.web.eval('document.querySelectorAll( ":hover" )[0].click()')


def click_release(
    button: Qt.MouseButton = Qt.MouseButton.LeftButton,
    mod: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    pos = mw.cursor().pos()
    widget = mw.app.widgetAt(pos)
    if not widget:
        return
    widgetPostition = widget.mapToGlobal(QPoint(0, 0))
    localPos = QPointF(pos.x() - widgetPostition.x(), pos.y() - widgetPostition.y())

    QCoreApplication.postEvent(
        widget,
        QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            localPos,
            button,
            Qt.MouseButton.NoButton,
            mod,
        ),
    )


def on_enter() -> None:
    if mw.state == "deckBrowser" or mw.state == "overview":
        select()
    elif mw.state == "review":
        mw.reviewer.onEnterKey()
    else:
        keyPress(Qt.Key.Key_Enter)


@for_states(["deckBrowser", "review", "overview", "question", "answer"])
def back() -> None:
    if mw.state == "review":
        mw.moveToState("overview")
    else:
        mw.moveToState("deckBrowser")


@for_states(["deckBrowser", "review", "overview", "question", "answer"])
def forward() -> None:
    if mw.state == "deckBrowser":
        mw.moveToState("overview")
    elif mw.state == "overview":
        mw.moveToState("review")


@for_states(["deckBrowser", "review", "overview", "question", "answer"])
def on_options() -> None:
    def deck_options(did: str) -> None:
        try:
            display_options_for_deck_id(DeckId(int(did)))
        except:
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
    if cw := current_window().window():
        if cw.isFullScreen():
            cw.showNormal()
        else:
            cw.showFullScreen()


def undo():
    if mw.undo_actions_info().can_undo:
        mw.undo()
    else:
        tooltip("Nothing to undo")


def redo():
    if mw.undo_actions_info().can_redo:
        mw.redo()
    else:
        tooltip("Nothing to redo")


def change_volume(direction=True):
    try:
        from aqt.utils import is_mac
    except:
        return

    if is_mac:
        current_volume = re.search(
            r"volume:(\d\d)",
            subprocess.run(
                'osascript -e "get volume settings"',
                shell=True,
                capture_output=True,
                text=True,
            ).stdout,
        )
        if current_volume:
            current_volume = int(current_volume.group(1)) / 14
            current_volume += -0.5 + int(direction)
            subprocess.run(f'osascript -e "set volume {current_volume}"', shell=True)


### Review


def _cycle_flag() -> Callable:
    flags = mw.addonManager.getConfig(__name__)["Flags"]

    @for_states(["question", "answer"])
    def cycle_flag(flags):
        flag = mw.reviewer.card.flags
        if flag == 0:
            mw.reviewer.setFlag(flags[0])
        elif flag not in flags:
            mw.reviewer.setFlag(0)
        elif flag == flags[-1]:
            mw.reviewer.setFlag(0)
        else:
            mw.reviewer.setFlag(flags[flags.index(flag) + 1])

    return lambda: cycle_flag(flags)


cycle_flag = _cycle_flag()


@for_states(["question", "answer"])
def card_info():
    mw.reviewer.on_card_info()


def _previous_card_info():
    try:
        f = mw.reviewer.on_previous_card_info
    except:
        return _pass
    return for_states(["question", "answer"])(f)


previous_card_info = _previous_card_info()


### Deck Browser


def _build_deck_list() -> list[tuple[int, bool]]:
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

    return decks


def _select_deck(did) -> None:
    mw.web.eval(
        f"document.getElementById({did}).getElementsByClassName('deck')[0].focus()"
    )


def _choose_deck(c_deck: int, direction: bool, due: bool) -> None:
    c_deck = int(c_deck) if c_deck else None
    decks, dues = zip(*_build_deck_list())
    len_decks = len(decks)

    if not len_decks:
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
    mw.web.eval(
        "document.activeElement.parentElement.getElementsByClassName('collapse')[0].click()"
    )
