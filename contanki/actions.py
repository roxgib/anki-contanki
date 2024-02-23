"""
Maps states to available actions and actions to functions.
"""

from __future__ import annotations
from functools import partial
from typing import Any, Callable

from aqt import mw, Qt
from aqt.utils import tooltip

try:
    from anki.utils import is_mac
except ImportError:
    is_mac = False

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
    build_cycle_flag,
    collapse_deck,
    choose_deck,
    scroll_build,
    hide_cursor,
    select,
    click,
    on_options,
    _pass,
    Ctrl,
    Shift,
    RightButton,
    toggle_image_occlusion_masks,
)

assert mw is not None
SCROLL_FACTOR = 50 if is_mac else 5


def check_filter(func: Callable) -> Callable:
    """Wrapper/decorator to check that the current deck is filtered."""

    def wrapper(*args, **kwargs):
        assert mw is not None and mw.col is not None
        if mw.col.decks.is_filtered(mw.col.decks.get_current_id()):
            func(*args, **kwargs)
        else:
            tooltip("This action can only be done on filtered decks")

    return wrapper


# fmt: off
button_actions: dict[str, Callable[[], Any]] = {
    # pylint: disable=protected-access
    # pylint: disable=line-too-long
    "": _pass,  # handle unmapped buttons
    "Show Quick Select": _pass,
    "Toggle Quick Select": _pass,

    # Common
    "Sync":                     mw.onSync,
    "Go to Overview":           partial(mw.moveToState, "overview"),
    "Go to Main Screen":        partial(mw.moveToState, "deckBrowser"),
    "Go to Review":             partial(mw.moveToState, "review"),
    "Open Browser":             mw.onBrowse,
    "Open Statistics":          mw.onStats,
    "Undo":                     undo,
    "Redo":                     redo,
    "Back":                     back,
    "Forward":                  forward,
    "Enter":                    on_enter,                               # Mostly Works
    "Fullscreen":               toggle_fullscreen,
    "Volume Up":                partial(change_volume, True),           # Works on Mac
    "Volume Down":              partial(change_volume, False),          # Works on Mac
    "Add Notes":                mw.onAddCard,
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
    "Scroll Up":                partial(scroll_build(), 0, -SCROLL_FACTOR),
    "Scroll Down":              partial(scroll_build(), 0, SCROLL_FACTOR),
    "Options":                  on_options,

    # Deck Browser
    "Next Deck":                partial(choose_deck, True),
    "Previous Deck":            partial(choose_deck, False),
    "Next Due Deck":            partial(choose_deck, True, True),
    "Previous Due Deck":        partial(choose_deck, False, True),
    "Expand/Collapse":          collapse_deck,
    "Filter Deck":              mw.onCram,
    "Check Database":           mw.onCheckDB,
    "Check Media":              mw.on_check_media_db,
    "Empty Cards":              mw.onEmptyCards,
    "Manage Note Types":        mw.onNoteTypes,
    "Study Deck":               mw.onStudyDeck,
    # "Export":                   mw.onExport,                              # Not Tested
    # "Import":                   mw.onImport,                              # Not Tested

    # Overview
    "Custom Study":             partial(key_press, Qt.Key.Key_C),
    "Rebuild":                  check_filter(mw.overview.rebuild_current_filtered_deck),
    "Empty":                    check_filter(mw.overview.empty_current_filtered_deck),

    # Reviewer
    "Again":                    partial(mw.reviewer._answerCard, 1),
    "Hard":                     partial(mw.reviewer._answerCard, 2),
    "Good":                     partial(mw.reviewer._answerCard, 3),
    "Easy":                     partial(mw.reviewer._answerCard, 4),
    "Suspend Card":             mw.reviewer.suspend_current_card,
    "Suspend Note":             mw.reviewer.suspend_current_note,
    "Bury Card":                mw.reviewer.bury_current_card,
    "Bury Note":                mw.reviewer.bury_current_note,
    "Flag":                     build_cycle_flag(),
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
    "Edit Note":                mw.onEditCurrent,
    "Flip Card":                mw.reviewer.onEnterKey,
    "Set Due Date":             mw.reviewer.on_set_due,                     # Not Tested
    "Toggle IO Masks":          toggle_image_occlusion_masks,                
}

release_actions: dict[str, Callable[[], Any]] = {
    "": _pass,
    "Click": click_release,
    "Secondary Click": partial(click_release, button=RightButton),
    "Quick Select": _pass,
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

def update_actions():
    """Update funcs to account for config changes."""
    button_actions["Flag"] = build_cycle_flag()
    button_actions["Scroll Up"] = partial(scroll_build(), 0, -SCROLL_FACTOR)
    button_actions["Scroll Down"] = partial(scroll_build(), 0, SCROLL_FACTOR)
    button_actions["Scroll Up Smooth"] = partial(mw.contanki.smooth_scroll, True, True)  # type: ignore
    button_actions["Scroll Down Smooth"] = partial(mw.contanki.smooth_scroll, False, True)  # type: ignore
    release_actions["Scroll Up Smooth"] = partial(mw.contanki.smooth_scroll, True, False)  # type: ignore
    release_actions["Scroll Down Smooth"] = partial(mw.contanki.smooth_scroll, False, False)  # type: ignore

COMMON_ACTIONS = [
    "Undo",             "Redo",             "Hide Cursor",      "Sync",
    "Open Browser",     "Add Notes",        "Fullscreen",       "Study Deck",
    "Go to Main Screen","Go to Overview",   "Go to Review",     "Preferences",
    "Open Statistics",  "Options",          "Quit",
]

if is_mac:
    COMMON_ACTIONS.extend(["Volume Up", "Volume Down"])

UI_ACTIONS = [
    "Enter",            "Select",           "Select Next",      "Select Previous",
    "Forward",          "Back",             "Click",            "Secondary Click",
    "Scroll Up",        "Scroll Down",      "Hide Cursor",      "Show Quick Select",
    "Scroll Up Smooth", "Scroll Down Smooth",                   "Toggle Quick Select",
]

REVIEW_ACTIONS = [
    "Again",            "Hard",             "Good",             "Easy",
    "Flip Card",        "Flag",             "Mark Note",        "Delete Note",
    "Bury Card",        "Bury Note",        "Suspend Card",     "Suspend Note",
    "Replay Audio",     "Pause Audio",      "Audio -5s",        "Audio +5s",
    "Record Voice",     "Replay Voice",     "Edit Note",        "Set Due Date",
    "Card Info",        "Previous Card Info",                   "Toggle IO Masks",
]

STATE_ACTIONS = {
    "all": ["", *COMMON_ACTIONS, *UI_ACTIONS],
    "review":   ["", *REVIEW_ACTIONS, *COMMON_ACTIONS, *UI_ACTIONS],
    "question": ["", *REVIEW_ACTIONS, *COMMON_ACTIONS, *UI_ACTIONS],
    "answer":   ["", *REVIEW_ACTIONS, *COMMON_ACTIONS, *UI_ACTIONS],

    "deckBrowser": [
        "",                     "Next Deck",            "Previous Deck",
        "Expand/Collapse",      "Next Due Deck",        "Previous Due Deck",
        *COMMON_ACTIONS,        *UI_ACTIONS,
    ],

    "overview": [
        "",                     "Next Deck",            "Previous Deck",
        "Next Due Deck",        "Previous Due Deck",    "Empty",
        "Rebuild",              *COMMON_ACTIONS,        *UI_ACTIONS,
    ],

    "dialog": [
        "",                     *UI_ACTIONS,            "Fullscreen",
        "Undo",                 "Redo",                 "Escape",
        "Focus Main Window",    "Switch Window",        "Up",
        "Down",                 "Up by 10",             "Down by 10",
    ],
}

QUICK_SELECT_ACTIONS: dict[str, list[str]] = {
    "deckBrowser": [
        "Undo",             "Redo",             "Hide Cursor",      "Sync",
        "Fullscreen",       "Quit",
    ],

    "overview": [
        "Undo",             "Redo",             "Hide Cursor",      "Sync",
        "Fullscreen",       "Quit",
    ],

    "review": [
        "Undo",             "Redo",             "Hide Cursor",      "Sync",
        "Fullscreen",       "Quit",             "Card Info",        "Previous Card Info",
        "Mark Note",        "Edit Note",        "Delete Note",      "Set Due Date",
        "Bury Card",        "Bury Note",        "Suspend Card",     "Suspend Note",

    ],
}
