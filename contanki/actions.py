"""
Maps states to available actions and actions to functions.
"""

from __future__ import annotations
from functools import partial
from typing import Any, Callable

from aqt import mw, Qt
from aqt.utils import tooltip, is_mac

from .funcs import (
    undo,
    redo,
    back,
    forward,
    on_enter,
    toggle_fullscreen,
    change_volume,
    key_press,
    click_release,
    previous_card_info,
    card_info,
    cycle_flag,
    collapse_deck,
    choose_deck,
    scroll,
    hide_cursor,
    select,
    click,
    on_options,
    _pass,
    Ctrl,
    Shift,
    RightButton
)

assert mw is not None
SCROLL_FACTOR = 50 if is_mac else 5


def rebuild_wrapper():
    """Ensures that the current deck is filtered before rebuilding"""
    if mw.col.decks.is_filtered(mw.col.decks.get_current_id()):
        mw.overview.rebuild_current_filtered_deck()
    else:
        tooltip("This action can only be done on filtered decks")


def empty_wrapper():
    """Ensures that the current deck is filtered before emptying"""
    if mw.col.decks.is_filtered(mw.col.decks.get_current_id()):
        mw.overview.empty_current_filtered_deck()
    else:
        tooltip("This action can only be done on filtered decks")


# fmt: off
button_actions: dict[str, Callable[[], Any]] = {
    # pylint: disable=protected-access
    # pylint: disable=line-too-long
    "": _pass,  # handle unmapped buttons
    "mod": _pass,  # For buttons used as modifiers

    # Common
    "Sync":                     mw.onSync,
    "Overview":                 partial(mw.moveToState, "overview"),
    "Browser":                  mw.onBrowse,
    "Statistics":               mw.onStats,
    "Main Screen":              partial(mw.moveToState, "deckBrowser"),
    "Review":                   partial(mw.moveToState, "review"),
    "Undo":                     undo,
    "Redo":                     redo,
    "Back":                     back,
    "Forward":                  forward,
    "Enter":                    on_enter,                               # Mostly Works
    "Fullscreen":               toggle_fullscreen,
    "Volume Up":                partial(change_volume, True),           # Works on Mac
    "Volume Down":              partial(change_volume, False),          # Works on Mac
    "Add":                      mw.onAddCard,
    "Preferences":              mw.onPrefs,
    "Quit":                     mw.close,
    "Hide Cursor":              hide_cursor,

    # UI
    # "Menubar":                  mw.menuWidget().setFocus,               # Doesn't Work
    # "Focus Main Window":        mw.window().activateWindow,             # Doesn't Work
    "Click":                    click,                                    # Mostly works
    "Secondary Click":          partial(click, button=RightButton),
    "Select Next":              partial(key_press, Qt.Key.Key_Tab),
    "Select Previous":          partial(key_press, Qt.Key.Key_Tab, Shift),
    "Select":                   select,
    "Switch Window":            mw.focusNextChild,                        # Not Tested
    "Escape":                   partial(key_press, Qt.Key.Key_Escape),
    "Up":                       partial(key_press, Qt.Key.Key_Up),
    "Down":                     partial(key_press, Qt.Key.Key_Down),
    "Up by 10":                 partial(key_press, Qt.Key.Key_Up, Ctrl),
    "Down by 10":               partial(key_press, Qt.Key.Key_Down, Ctrl),
    "Scroll Up":                partial(scroll, 0, -SCROLL_FACTOR),
    "Scroll Down":              partial(scroll, 0, SCROLL_FACTOR),
    "Options":                  on_options,

    # Deck Browser
    "Next Deck":                partial(choose_deck, True),
    "Previous Deck":            partial(choose_deck, False),
    "Next Due Deck":            partial(choose_deck, True, True),
    "Previous Due Deck":        partial( choose_deck, False, True),
    "Collapse/Expand":          collapse_deck,
    "Filter":                   mw.onCram,
    "Check Database":           mw.onCheckDB,
    "Check Media":              mw.on_check_media_db,
    "Empty Cards":              mw.onEmptyCards,
    "Manage Note Types":        mw.onNoteTypes,
    "Study Deck":               mw.onStudyDeck,
    # "Export":                   mw.onExport,                              # Not Tested
    # "Import":                   mw.onImport,                              # Not Tested

    # Overview
    "Custom Study":             partial(key_press, Qt.Key.Key_C),
    "Rebuild":                  rebuild_wrapper,
    "Empty":                    empty_wrapper,

    # Reviewer
    "Again":                    partial(mw.reviewer._answerCard, 1),
    "Hard":                     partial(mw.reviewer._answerCard, 2),
    "Good":                     partial(mw.reviewer._answerCard, 3),
    "Easy":                     partial(mw.reviewer._answerCard, 4),
    "Suspend Card":             mw.reviewer.suspend_current_card,
    "Suspend Note":             mw.reviewer.suspend_current_note,
    "Bury Card":                mw.reviewer.bury_current_card,
    "Bury Note":                mw.reviewer.bury_current_note,
    "Flag":                     cycle_flag,
    "Mark Note":                mw.reviewer.toggle_mark_on_current_note,
    "Delete Note":              mw.reviewer.delete_current_note,
    "Record Voice":             mw.reviewer.onRecordVoice,                  # Not Tested
    "Replay Voice":             mw.reviewer.onReplayRecorded,               # Not Tested
    "Card Info":                card_info,
    "Previous Card Info":       previous_card_info,
    "Pause Audio":              mw.reviewer.on_pause_audio,
    "Audio +5s":                mw.reviewer.on_seek_forward,
    "Audio -5s":                mw.reviewer.on_seek_backward,
    "Replay Audio":             mw.reviewer.replayAudio,
    "Edit Note":                mw.onEditCurrent,                           # Not Tested
    "Flip Card":                mw.reviewer.onEnterKey,
    "Set Due Date":             mw.reviewer.on_set_due,
}

release_actions: dict[str, Callable[[], Any]] = {
    "": _pass,
    "Click": click_release,
    "Secondary Click": partial(click_release, button=RightButton),
    "Select Next": _pass,
    "Select Previous": _pass,
    "Up": _pass,
    "Down": _pass,
    "Up by 10": _pass,
    "Down by 10": _pass,
    "Scroll Up": _pass,
    "Scroll Down": _pass,
    "Next Deck": _pass,
    "Previous Deck": _pass,
    "Next Due Deck": _pass,
    "Previous Due Deck": _pass,
}

common_actions = [
    "Add",              "Back",             "Browser",          "Enter",
    "Forward",          "Fullscreen",       "Hide Cursor",      "Main Screen",
    "Overview",         "Preferences",      "Quit",             "Redo",
    "Review",           "Statistics",       "Sync",             "Undo",
    "Volume Down",      "Volume Up",        "Click",            "Secondary Click",
    "Options",          "Scroll Down",      "Scroll Up",        "Select Next",
    "Select Previous",  "Select",
]

review_actions = [
    "Again",            "Audio -5s",        "Audio +5s",        "Bury Card",
    "Bury Note",        "Card Info",        "Delete Note",      "Easy",
    "Edit Note",        "Flag",             "Flip Card",        "Good", "Hard",
    "Mark Note",        "Pause Audio",      "Record Voice",     "Previous Card Info",
    "Replay Audio",     "Replay Voice",     "Set Due Date",     "Suspend Card",
    "Suspend Note",
]

state_actions = {
    "all": [
        "",                     *common_actions,            "Check Database",
        "Check Media",          "Empty Cards",              "Manage Note Types",
        "Study Deck",
    ],
    "deckBrowser": [
        "",                     *common_actions,            "Check Database",
        "Check Media",          "Collapse/Expand",          "Empty Cards",
        "Manage Note Types",    "Next Deck",                "Next Due Deck",
        "Previous Deck",        "Previous Due Deck",        "Study Deck",
    ],
    "overview": [
        "",                     *common_actions,            "Empty",
        "Rebuild",              "Filter",                   "Custom Study",
        "Next Deck",            "Previous Deck",            "Next Due Deck",
        "Previous Due Deck",
    ],
    "dialog": [
        "",                     "Enter",                    "Fullscreen",
        "Undo",                 "Redo",                     "Escape",
        "Volume Down",          "Volume Up",                "Focus Main Window",
        "Click",                "Secondary Click",          "Hide Cursor",
        "Select",               "Select Next",              "Select Previous",
        "Scroll Up",            "Scroll Down",              "Switch Window",
        "Up",                   "Down",                     "Quit",
        "Up by 10",             "Down by 10",
    ],
    "review":   ["", *common_actions, *review_actions],
    "question": ["", *common_actions, *review_actions],
    "answer":   ["", *common_actions, *review_actions],
}
