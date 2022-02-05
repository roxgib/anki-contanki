from typing import Callable
from aqt import mw
from aqt.qt import QCoreApplication, QEvent, QMouseEvent, QPoint, QPointF, Qt
from aqt.qt import QKeyEvent as QKE
from aqt.utils import tooltip, current_window
from os.path import dirname, abspath, join


# Internal

def get_state() -> str:
    return mw.reviewer.state if mw.state == "review" else mw.state


def _pass() -> None:
    pass


def cdid() -> int:
    return mw.col.decks.get_current_id()


def build_mappings(mappings):
    states = {
            "startup":          mappings['startup'],
            "deckBrowser":      mappings['deckBrowser'],
            "overview":         mappings['overview'],
            "profileManager":   mappings['profileManager'],
            'question':         mappings['question'],
            'answer':           mappings['answer'],
            'browser':          mappings['browser'],
            'add':              mappings['add'],
            'edit':             mappings['edit'],
            'options':          mappings['options'],
            'preferences':      mappings['preferences'],
            'dialog':           mappings['dialog'],
        }

    for key, value in mappings['review'].items():
        if key not in states['question'] or states['question'][key] == '':
            states['question'][key] = value
        if key not in states['answer'] or states['answer'][key] == '':
            states['answer'][key] = value

    for key, value in mappings['dialog'].items():
        for d in ['add','edit','options','preferences']:
            if key not in states[d] or states[d][key] == '':
                states[d][key] = value

    for key, value in mappings['all'].items():
        for state, d in states.items():
            if key not in d or d[key] == '':
                states[state][key] = value

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
    
    

# Common

def keyPress(key: Qt.Key, mod: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier) -> None:
    QCoreApplication.sendEvent(mw.app.focusObject(), QKE(QKE.Type.KeyPress, key, mod))
    QCoreApplication.sendEvent(mw.app.focusObject(), QKE(QKE.Type.KeyRelease, key, mod))


def select() -> None:
    mw.web.eval("document.activeElement.click()")


def hideCursor() -> None:
    mw.cursor().setPos(QPoint(mw.app.primaryScreen().size().width(), mw.app.primaryScreen().size().height())),


def click(
    button: Qt.MouseButton = Qt.MouseButton.LeftButton,
    mod: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    pos = mw.cursor().pos()
    pos_lf = QPointF(mw.mapFromGlobal(pos))

    QCoreApplication.postEvent(
        mw.app.widgetAt(pos),
        QMouseEvent(QEvent.Type.MouseButtonPress, pos_lf, button, button, mod),
    )

    QCoreApplication.postEvent(
        mw.app.widgetAt(pos),
        QMouseEvent(
            QEvent.Type.MouseButtonRelease, pos_lf, button, Qt.MouseButton.NoButton, mod
        ),
    )

    tooltip(f"Mouse Click {pos.x()}, {pos.y()}")


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
    if mw.state == "review":
        mw.reviewer.onOptions()
    elif mw.state == "deckBrowser":
        pass
    elif mw.state == "overview":
        pass


def _fullscreen() -> Callable:
    try:
        f = mw.on_toggle_fullscreen
        return f
    except:
        return lambda: tooltip('Not supported on this version of Anki')

fullscreen = _fullscreen()


### Review

def _cycle_flag() -> Callable:
    flags = mw.addonManager.getConfig(__name__)['options']["flags"]

    def cycle_flag():
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


func_map = {
    "": _pass,  # handle unmapped buttons
    
    # Common Function                                           
    "Sync":                 mw.onSync,                                          # Works
    "Overview":             lambda: mw.moveToState("overview"),                 # Works
    "Browser":              mw.onBrowse,                                        # Works
    "Statistics":           mw.onStats,                                         # Works
    "Main Screen":          lambda: mw.moveToState("deckBrowser"),              # Works
    "Review":               lambda: mw.moveToState("review"),                   # Works
    "Undo":                 mw.undo,                                            # Works
    "Redo":                 mw.redo,                                            # Works
    "Back":                 back,                                               # Works
    "Forward":              forward,                                            # Works
    "Enter":                on_enter,                                           # Needs Refactor
    "Fullscreen":           fullscreen,                                         # Not Tested
    "Volume Up":            lambda: keyPress(Qt.Key.Key_VolumeUp),              # Doesn't Work
    "Volume Down":          lambda: keyPress(Qt.Key.Key_VolumeDown),            # Doesn't Work
    "Menubar":              mw.menuWidget().setFocus,                           # Not Tested
    "Add":                  mw.onAddCard,                                       # Not Tested
    "About Anki":           mw.onAbout,                                         # Not Tested
    "Preferences":          mw.onPrefs,                                         # Not Tested
    "Quit":                 mw.close,                                           # Not Tested
    "Switch Profile":       mw.unloadProfileAndShowProfileManager,              # Not Tested
    "Hide Cursor":          hideCursor,                                         # Not Tested
    "Anki Help":            mw.onDocumentation,                                 # Not Tested
    
    
    # UI Functions
    "Click":                click,                                              # Buggy
    "Secondary Click":      lambda: click(button=Qt.MouseButton.RightButton),   # Buggy
    "Select Next":          lambda: keyPress(Qt.Key.Key_Tab),                   # Works
    "Select Previous":      lambda: keyPress(                                   # Works
                                        Qt.Key.Key_Tab, 
                                        Qt.KeyboardModifier.ShiftModifier
                                        ),
    "Select":               select,                                             # Works
    "Focus Main Window":    mw.setFocus,                                        # Not Tested
    "Switch Window":        mw.focusNextChild,                                  # Not Tested
    "Escape":               lambda:keyPress(Qt.Key.Key_Escape),                 # Not Tested
    "Up":                   lambda: keyPress(Qt.Key.Key_Up),                    # Not Tested
    "Down":                 lambda: keyPress(Qt.Key.Key_Down),                  # Not Tested
    'Scroll Up':            lambda: scroll(0, -50),                             # Not Tested
    'Scroll Down':          lambda: scroll(0, 50),                              # Not Tested
    
    # Deck Browser Functions
    "Next Deck":            lambda: choose_deck(True),                          # Works
    "Previous Deck":        lambda: choose_deck(False),                         # Works
    "Next Due Deck":        lambda: choose_deck(True, True),                    # Works
    "Previous Due Deck":    lambda: choose_deck(False, True),                   # Works
    "Collapse/Expand":      collapse_deck,                                      # Works
    "Filter":               mw.onCram,                                          # Not Tested
    "Rebuild":              lambda: mw.col.sched.rebuild_filtered_deck(cdid()), # Not Tested
    "Empty":                lambda: mw.col.sched.empty_filtered_deck(cdid()),   # Not Tested
    "Check Database":       mw.onCheckDB,                                       # Works
    "Check Media":          mw.on_check_media_db,                               # Works
    "Empty Cards":          mw.onEmptyCards,                                    # Works
    "Manage Note Types":    mw.onNoteTypes,                                     # Works
    "Study Deck":           mw.onStudyDeck,                                     # Works
    "Export":               mw.onExport,                                        # Not Tested
    "Import":               mw.onImport,                                        # Not Tested
    
    # Overview Functions
    "Custom Study":         lambda: keyPress(Qt.Key.Key_C),                     # Not Tested
    
    # Reviewer Functions
    "Again":                lambda: mw.reviewer._answerCard(1),                 # Works
    "Hard":                 lambda: mw.reviewer._answerCard(2),                 # Works
    "Good":                 lambda: mw.reviewer._answerCard(3),                 # Works
    "Easy":                 lambda: mw.reviewer._answerCard(4),                 # Works
    "Suspend Card":         mw.reviewer.suspend_current_card,                   # Works
    "Suspend Note":         mw.reviewer.suspend_current_note,                   # Works
    "Bury Card":            mw.reviewer.bury_current_card,                      # Works
    "Bury Note":            mw.reviewer.bury_current_note,                      # Works
    "Mark Note":            mw.reviewer.toggle_mark_on_current_note,            # Works
    "Delete Note":          mw.reviewer.delete_current_note,                    # Works
    "Record Voice":         mw.reviewer.onRecordVoice,                          # Not Tested
    "Replay Voice":         mw.reviewer.onReplayRecorded,                       # Not Tested
    "Card Info":            mw.reviewer.on_card_info,                           # Not Tested
    "Previous Card Info":   mw.reviewer.on_previous_card_info,                  # Not Tested
    "Pause Audio":          mw.reviewer.on_pause_audio,                         # Not Tested
    "Audio +5s":            mw.reviewer.on_seek_forward,                        # Not Tested
    "Audio -5s":            mw.reviewer.on_seek_backward,                       # Not Tested
    "Replay Audio":         mw.reviewer.replayAudio,                            # Works
    "Edit Note":            mw.onEditCurrent,                                   # Not Tested
    "Flip Card":            mw.reviewer.onEnterKey,                             # Works
    "Cycle Flag":           cycle_flag,                                         # Works
    "Set Due Date":         mw.reviewer.on_set_due,                             # Not Tested
}
