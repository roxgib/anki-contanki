import re
import subprocess
from typing import Callable, Dict
from functools import partial
from os.path import dirname, abspath, join, exists

from anki.decks import DeckId
from aqt import QPainter, mw
from aqt.deckoptions import display_options_for_deck_id
from aqt.qt import QCoreApplication, QKeySequence, QMouseEvent, QEvent, QPixmap, QPoint, QPointF, Qt
from aqt.qt import QKeyEvent as QKE
from aqt.utils import current_window

addon_path = dirname(abspath(__file__))


# Internal

def get_state() -> str:
    if focus := current_window():
        if focus.objectName() == 'MainWindow':
            return mw.reviewer.state if mw.state == "review" else mw.state
        elif focus.objectName() == 'Preferences':
            return 'dialog'
        else:
            return 'NoFocus'
    else:
        return 'NoFocus'


def _pass() -> None:
    pass


def quad_curve(value: float, factor: int = 5) -> float:
    return ((value * factor)**2) * value


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


def get_button_icon(controller: str, button: str, glow: bool = False) -> QPixmap:
    if 'Stick' in button and button.split(' ')[-1] in ['Left','Right','Up','Down','Horizontal','Vertical']:
        direction = button.split(' ')[-1]
        button = ' '.join(button.split(' ')[:-1])
        pixmap = QPixmap(join(addon_path, 'buttons', controller, button))
        dpixmap = QPixmap(join(addon_path, 'buttons', 'Arrows', direction))
        painter = QPainter()
        painter.begin(pixmap)
        painter.drawPixmap(pixmap.rect(), dpixmap, dpixmap.rect())
        painter.end()
    else:
        pixmap = QPixmap(join(addon_path, 'buttons', controller, button))

    if glow:
        gpixmap = QPixmap(join(addon_path, 'buttons', 'Other', 'glow'))
        painter = QPainter()
        painter.begin(pixmap)
        painter.drawPixmap(pixmap.rect(), gpixmap, gpixmap.rect())
        painter.end()

    return pixmap


def get_custom_actions() -> Dict[str, Callable]:
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


def get_file(file: str) -> str: # refactor this
    paths = [
        addon_path,
        join(addon_path, 'user_files'), 
        join(addon_path, 'profiles'), 
        join(addon_path, 'user_files', 'profiles'), 
    ]
    for path in paths:
        if exists(join(path, file)):
            with open(join(path, file)) as f:
                return f.read()


# Common

def keyPress(key: Qt.Key, mod: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier) -> None:
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
    speed = config['Scroll Speed'] / 10
    def scroll (x: float, y: float) -> None:
        mw.web.eval(f'window.scrollBy({quad_curve(x*speed)}, {quad_curve(y*speed)})')

    return scroll

scroll = scroll_build()

def move_mouse_build() -> Callable:
    config = mw.addonManager.getConfig(__name__)
    speed = config['Cursor Speed'] / 2
    accel = config['Cursor Acceleration'] / 5
    
    def move_mouse(x: float, y: float) -> None:
        if abs(x) + abs(y) < 0.05: return
        cursor = mw.cursor()
        pos = cursor.pos()
        geom = mw.screen().geometry()

        y = pos.y() + ((abs(y)*speed)**(accel+1))*y
        x = pos.x() + ((abs(x)*speed)**(accel+1))*x
        x, y = max(x, geom.x()), max(y, geom.y())
        x, y = min(x, geom.width()), min(y, geom.height())
        
        pos.setX(x)
        pos.setY(y)
        cursor.setPos(pos)
    
    return move_mouse


def hide_cursor() -> None:
    mw.cursor().setPos(
        QPoint(
            mw.app.primaryScreen().size().width(), 
            mw.app.primaryScreen().size().height()
        )
    )


def click(
    button: Qt.MouseButton = Qt.MouseButton.LeftButton,
    mod: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    pos = mw.cursor().pos()
    widget = mw.app.widgetAt(pos)
    if not widget: return
    widgetPostition = widget.mapToGlobal(QPoint(0,0))
    localPos = QPointF(pos.x() - widgetPostition.x(), pos.y() - widgetPostition.y())

    QCoreApplication.postEvent(widget, QMouseEvent(QEvent.Type.MouseButtonPress, localPos, button, button, mod))


def click_release(
    button: Qt.MouseButton = Qt.MouseButton.LeftButton,
    mod: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    pos = mw.cursor().pos()
    widget = mw.app.widgetAt(pos)
    if not widget: return
    widgetPostition = widget.mapToGlobal(QPoint(0,0))
    localPos = QPointF(pos.x() - widgetPostition.x(), pos.y() - widgetPostition.y())

    QCoreApplication.postEvent(
        widget,QMouseEvent(QEvent.Type.MouseButtonRelease, localPos, button, Qt.MouseButton.NoButton, mod)
        )


def on_enter() -> None:
    if mw.state == "review":
        mw.reviewer.onEnterKey()
    elif mw.state == "deckBrowser":
        select()
    elif mw.state == "overview":
        select()


def back() -> None:
    if mw.state == "review":
        mw.moveToState("overview")
    else:
        mw.moveToState("deckBrowser")


def forward() -> None:
    if mw.state == "deckBrowser":
        mw.moveToState("overview")
    elif mw.state == "overview":
        mw.moveToState("review")


def on_options() -> None:
    def deck_options(did: str) -> None:
        try: 
            display_options_for_deck_id(DeckId(int(did)))
        except:
            mw.onPrefs()
    if mw.state == "review":
        mw.reviewer.onOptions()
    elif mw.state == "deckBrowser":
        mw.web.evalWithCallback('document.activeElement.parentElement.parentElement.id', deck_options)
    elif mw.state == "overview":
        display_options_for_deck_id(mw.col.decks.get_current_id())


def toggle_fullscreen() -> None:
    if cw := current_window().window():
        if cw.isFullScreen():
            cw.showNormal()
        else:
            cw.showFullScreen()


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
            ).stdout
            )
        if current_volume:
            current_volume = int(current_volume.group(1)) / 14
            current_volume += -0.5 + int(direction)
            subprocess.run(f'osascript -e "set volume {current_volume}"', shell=True)


### Review

def _cycle_flag() -> Callable:
    flags = mw.addonManager.getConfig(__name__)["Flags"]

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


def _previous_card_info():
    try:
        f = mw.reviewer.on_previous_card_info
        return f
    except:
        return _pass

previous_card_info = _previous_card_info()


### Deck Browser

def _build_deck_list(due: bool = False) -> list:
    
    def _build_node(node, due: bool):
        if due:
            if not (node.review_count or node.learn_count or node.new_count):
                return []
        
        decks = [node.deck_id]
        if node.children:
            if not node.collapsed:
                for child in node.children:
                    decks.extend(_build_node(child, due))
        
        return decks

    decks = list()
    for child in mw.col.sched.deck_due_tree().children:
        decks.extend(_build_node(child, due))

    return decks


def _select_deck(did) -> None:
    mw.web.eval(f"document.getElementById({did}).getElementsByClassName('deck')[0].focus()")


def _choose_deck(c_deck: int, decks: list, direction: bool) -> None:
    c_deck = int(c_deck) if c_deck else None

    if c_deck == decks[-1]:
        c_deck_index = -1
    elif c_deck in decks:
        c_deck_index = decks.index(c_deck)
    else:
        c_deck_index = -direction

    c_deck_index += (1 if direction else -1)

    if decks[c_deck_index] == 1:
        c_deck_index += (1 if direction else -1)
    
    if mw.state == 'deckBrowser':
        _select_deck(decks[c_deck_index])
    else:
        mw.col.decks.select(decks[c_deck_index])
        mw.moveToState("overview")


def choose_deck(direction: bool, due: bool = False) -> None:
    decks = _build_deck_list(due)
    mw.web.setFocus()

    if len(decks) == 0:
        return

    if mw.state == 'deckBrowser':
        mw.web.evalWithCallback(
            'document.activeElement.parentElement.parentElement.id', 
            lambda c_deck: _choose_deck(c_deck, decks, direction)
            )
    else:
        _choose_deck(mw.col.decks.get_current_id(), decks, direction)


def collapse_deck() -> None:
    if get_state() != 'deckBrowser': return
    mw.web.eval("document.activeElement.parentElement.getElementsByClassName('collapse')[0].click()")