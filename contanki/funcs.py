from typing import Callable
import subprocess

from anki.decks import DeckId
from aqt import mw
from aqt.deckoptions import display_options_for_deck_id
from aqt.qt import QCoreApplication, QEvent, QMouseEvent, QPoint, QPointF, Qt
from aqt.qt import QKeyEvent as QKE
from aqt.utils import current_window
from os.path import dirname, abspath, join

# Internal

def get_state() -> str:
    if focus := current_window():
        if focus.objectName() == 'MainWindow':
            return mw.reviewer.state if mw.state == "review" else mw.state
        elif focus.objectName() == '':
            return 'NoFocus'
        else:
            return focus.objectName().lower()
    else:
        return 'NoFocus'


def _pass() -> None:
    pass


def cdid() -> DeckId:
    return mw.col.decks.get_current_id()


def build_mappings(mappings):
    states = {
            "startup":          mappings['startup'],
            "deckBrowser":      mappings['deckBrowser'],
            "overview":         mappings['overview'],
            "profileManager":   mappings['profileManager'],
            'question':         mappings['question'],
            'answer':           mappings['answer'],
            'dialog':           mappings['dialog'],
        }

    for key, value in mappings['review'].items():
        if key not in states['question'] or states['question'][key] == '':
            states['question'][key] = value
        if key not in states['answer'] or states['answer'][key] == '':
            states['answer'][key] = value

    for key, value in mappings['all'].items():
        for state, d in states.items():
            if key not in d or d[key] == '':
                states[state][key] = value

    states['NoFocus'] = {'Pad':'Focus Main Window'}

    return states


def quadCurve(value, factor = 5):
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


def get_file(file: str) -> str:
    addon_path = dirname(abspath(__file__))

    import os.path

    if os.path.exists(join(addon_path, file)):
        with open(join(addon_path, file)) as f:
            return f.read()
    elif os.path.exists(join(addon_path, 'controllers', file)):
        with open(join(addon_path, 'controllers', file)) as f:
            return f.read()
    elif os.path.exists(join(addon_path, 'user_files', file)):
        with open(join(addon_path, 'controllers', file)) as f:
            return f.read()


# Common

def keyPress(key: Qt.Key, mod: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier) -> None:
    QCoreApplication.sendEvent(mw.app.focusObject(), QKE(QKE.Type.KeyPress, key, mod))
    QCoreApplication.sendEvent(mw.app.focusObject(), QKE(QKE.Type.KeyRelease, key, mod))


def select() -> None:
    mw.web.eval("document.activeElement.click()")


def scroll(value: float) -> None:
        if max(abs(value)) < 0.08: return
        mw.web.eval(f'window.scrollBy({quadCurve(x)}, {quadCurve(y)})')


def tab(value: float):
    if value < 0:
        keyPress(Qt.Key.Key_Tab, Qt.KeyboardModifier.ShiftModifier)
    elif value > 0:
        keyPress(Qt.Key.Key_Tab)


def hideCursor() -> None:
    mw.cursor().setPos(
        QPoint(
            mw.app.primaryScreen().size().width(), 
            mw.app.primaryScreen().size().height()
        )
    ),


def moveMouse(x: float, y: float) -> None:
    if abs(x) + abs(y) < 0.05: return
    cursor = mw.cursor()
    pos = cursor.pos()
    geom = mw.screen().geometry()

    x = pos.x() + quadCurve(x, 8)
    y = pos.y() + quadCurve(y, 8)
    x, y = max(x, geom.x()), max(y, geom.y())
    x, y = min(x, geom.width()), min(y, geom.height())
    
    pos.setX(x)
    pos.setY(y)
    cursor.setPos(pos)


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


def scroll(x, y) -> None:
    mw.web.eval(f'window.scrollBy({x}, {y})')


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


def onOptions() -> None:
    def deckOptions(did: str) -> None:
        try: 
            display_options_for_deck_id(DeckId(int(did)))
        except:
            mw.onPrefs
    if mw.state == "review":
        mw.reviewer.onOptions()
    elif mw.state == "deckBrowser":
        mw.web.evalWithCallback('document.activeElement.parentElement.parentElement.id', deckOptions)
    elif mw.state == "overview":
        display_options_for_deck_id(cdid())


def toggle_fullscreen():
    if cw := current_window().window():
        if cw.isFullScreen():
            cw.showNormal()
        else:
            cw.showFullScreen()

def changeVolume(direction=True):
    try:
        from aqt.utils import is_mac
    except:
        return
        
    if is_mac:
        current_volume = subprocess.run(
            'osascript -e "get volume settings"', 
            shell=True,
            capture_output=True,
            text=True
        ).stdout.split(',')[0].split[':'][1] / 14
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
        _choose_deck(cdid(), decks, direction)


def collapse_deck() -> None:
    if get_state() != 'deckBrowser': return
    mw.web.eval("document.activeElement.parentElement.getElementsByClassName('collapse')[0].click()")