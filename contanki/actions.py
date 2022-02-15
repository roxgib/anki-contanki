from aqt import mw
from aqt.qt import Qt

from .funcs import *
from .funcs import _pass

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
    "Enter":                on_enter,                                           # Mostly Works
    "Fullscreen":           toggle_fullscreen,                                  # Works
    "Volume Up":            changeVolume,                                       # Not Tested
    "Volume Down":          lambda: changeVolume(False),                        # Not Tested
    "Menubar":              mw.menuWidget().setFocus,                           # Doesn't Work
    "Add":                  mw.onAddCard,                                       # Not Tested
    "About Anki":           mw.onAbout,                                         # Not Tested
    "Preferences":          mw.onPrefs,                                         # Not Tested
    "Quit":                 mw.close,                                           # Works
    "Switch Profile":       mw.unloadProfileAndShowProfileManager,              # Not Tested
    "Hide Cursor":          hideCursor,                                         # Works
    "Anki Help":            mw.onDocumentation,                                 # Not Tested
    
    
    # UI Functions
    "Click":                click,                                              # Mostly works
    "Secondary Click":      lambda: click(button=Qt.MouseButton.RightButton),   # Mostly works
    "Select Next":          lambda: keyPress(Qt.Key.Key_Tab),                   # Works
    "Select Previous":      lambda: keyPress(                                   # Works
                                        Qt.Key.Key_Tab, 
                                        Qt.KeyboardModifier.ShiftModifier
                                        ),
    "Select":               select,                                             # Works
    "Focus Main Window":    mw.window().activateWindow,                         # Doesn't Work
    "Switch Window":        mw.focusNextChild,                                  # Not Tested
    "Escape":               lambda:keyPress(Qt.Key.Key_Escape),                 # Works
    "Up":                   lambda: keyPress(Qt.Key.Key_Up),                    # Works
    "Down":                 lambda: keyPress(Qt.Key.Key_Down),                  # Works
    "Up by 10":             lambda: keyPress(Qt.Key.Key_Up, Qt.Key.Key_Control),# Works
    "Down by 10":           lambda: keyPress(                                   # Works
                                Qt.Key.Key_Down,
                                Qt.Key.Key_Control),                  
    'Scroll Up':            lambda: scroll(0, -50),                             # Not Tested
    'Scroll Down':          lambda: scroll(0, 50),                              # Not Tested
    'Options':              onOptions,                                          # Works in some screens

    
    # Deck Browser Functions
    "Next Deck":            lambda: choose_deck(True),                          # Works
    "Previous Deck":        lambda: choose_deck(False),                         # Works
    "Next Due Deck":        lambda: choose_deck(True, True),                    # Works
    "Previous Due Deck":    lambda: choose_deck(False, True),                   # Works
    "Collapse/Expand":      collapse_deck,                                      # Works
    "Filter":               mw.onCram,                                          # Works but opens dialog
    "Rebuild":              lambda: mw.col.sched.rebuild_filtered_deck(cdid()), # Works
    "Empty":                lambda: mw.col.sched.empty_filtered_deck(cdid()),   # Works
    "Check Database":       mw.onCheckDB,                                       # Works
    "Check Media":          mw.on_check_media_db,                               # Works but opens dialog
    "Empty Cards":          mw.onEmptyCards,                                    # Works but opens dialog
    "Manage Note Types":    mw.onNoteTypes,                                     # Works but opens dialog
    "Study Deck":           mw.onStudyDeck,                                     # Works but opens dialog
    "Export":               mw.onExport,                                        # Not Tested
    "Import":               mw.onImport,                                        # Not Tested
    
    # Overview Functions
    "Custom Study":         lambda: keyPress(Qt.Key.Key_C),                     # Works but opens dialog
    
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
    "Card Info":            mw.reviewer.on_card_info,                           # Works but opens dialog
    "Previous Card Info":   previous_card_info,                                 # Works but opens dialog
    "Pause Audio":          mw.reviewer.on_pause_audio,                         # Works
    "Audio +5s":            mw.reviewer.on_seek_forward,                        # Not Tested
    "Audio -5s":            mw.reviewer.on_seek_backward,                       # Not Tested
    "Replay Audio":         mw.reviewer.replayAudio,                            # Works
    "Edit Note":            mw.onEditCurrent,                                   # Not Tested
    "Flip Card":            mw.reviewer.onEnterKey,                             # Works
    "Flag":           cycle_flag,                                               # Works
    "Set Due Date":         mw.reviewer.on_set_due,                             # Works but opens dialog
    "Show Hint":            _pass,                                              # Not Implemented

    # Other
    "":                     _pass,                                              # For unassigned buttons
    "mod":                  _pass,                                              # For buttons used as modifiers
}