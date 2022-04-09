from aqt import mw
from aqt.qt import Qt
from aqt.utils import tooltip

from .funcs import *
from .funcs import _pass

def rebuild_wrapper():
    if mw.col.decks.is_filtered(mw.col.decks.get_current_id()):
        mw.overview.rebuild_current_filtered_deck()
    else:
        tooltip("This action can only be done on filtered decks")

def empty_wrapper():
    if mw.col.decks.is_filtered(mw.col.decks.get_current_id()):
        mw.overview.empty_current_filtered_deck()
    else:
        tooltip("This action can only be done on filtered decks")

button_actions = {
    "":       _pass,  # handle unmapped buttons
    "mod":    _pass,  # For buttons used as modifiers
    

    # Common Function                                           
    "Sync":                 mw.onSync,                                  # Works
    "Overview":             lambda: mw.moveToState("overview"),         # Works
    "Browser":              mw.onBrowse,                                # Works
    "Statistics":           mw.onStats,                                 # Works
    "Main Screen":          lambda: mw.moveToState("deckBrowser"),      # Works
    "Review":               lambda: mw.moveToState("review"),           # Works
    "Undo":                 mw.undo,                                    # Works
    "Redo":                 mw.redo,                                    # Works
    "Back":                 back,                                       # Works
    "Forward":              forward,                                    # Works
    "Enter":                on_enter,                                   # Mostly Works
    "Fullscreen":           toggle_fullscreen,                          # Works
    "Volume Up":            change_volume,                              # Only works on Mac
    "Volume Down":          lambda: change_volume(False),               # Only works on Mac
    # "Menubar":              mw.menuWidget().setFocus,                   # Doesn't Work
    "Add":                  mw.onAddCard,                               # Works
    "Preferences":          mw.onPrefs,                                 # Works, but preferences dialog not controllable
    "Quit":                 mw.close,                                   # Works
    "Hide Cursor":          hide_cursor,                                # Works


    # UI Functions
    "Click":                click,                                              # Mostly works
    "Secondary Click":      lambda: click(button=Qt.MouseButton.RightButton),   # Mostly works
    "Select Next":          lambda: keyPress(Qt.Key.Key_Tab),                   # Works
    "Select Previous":      lambda: keyPress(                                   # Works
                                        Qt.Key.Key_Tab, 
                                        Qt.KeyboardModifier.ShiftModifier),
    "Select":               select,                                             # Works
    # "Focus Main Window":    mw.window().activateWindow,                         # Doesn't Work
    "Switch Window":        mw.focusNextChild,                                  # Not Tested
    "Escape":               lambda:keyPress(Qt.Key.Key_Escape),                 # Works
    "Up":                   lambda: keyPress(Qt.Key.Key_Up),                    # Works
    "Down":                 lambda: keyPress(Qt.Key.Key_Down),                  # Works
    "Up by 10":             lambda: keyPress(                                   # Works
                                Qt.Key.Key_Up, 
                                Qt.KeyboardModifier.ControlModifier),
    "Down by 10":           lambda: keyPress(                                   # Works
                                Qt.Key.Key_Down,
                                Qt.KeyboardModifier.ControlModifier),                  
    'Scroll Up':            lambda: scroll(0, -50),                             # Works
    'Scroll Down':          lambda: scroll(0, 50),                              # Works
    'Options':              on_options,                                         # Works, but deck options still exec

    
    # Deck Browser Functions
    "Next Deck":            lambda: choose_deck(True),                          # Works
    "Previous Deck":        lambda: choose_deck(False),                         # Works
    "Next Due Deck":        lambda: choose_deck(True, True),                    # Works
    "Previous Due Deck":    lambda: choose_deck(False, True),                   # Works
    "Collapse/Expand":      collapse_deck,                                      # Works
    "Filter":               mw.onCram,                                          # Works
    "Check Database":       mw.onCheckDB,                                       # Works
    "Check Media":          mw.on_check_media_db,                               # Works
    "Empty Cards":          mw.onEmptyCards,                                    # Works
    "Manage Note Types":    mw.onNoteTypes,                                     # Works
    "Study Deck":           mw.onStudyDeck,                                     # Works
    # "Export":               mw.onExport,                                        # Not Tested
    # "Import":               mw.onImport,                                        # Not Tested
    
    # Overview Functions
    "Custom Study":         lambda: keyPress(Qt.Key.Key_C),                     # Works
    "Rebuild":              rebuild_wrapper,                                    # Works
    "Empty":                empty_wrapper,                                      # Works

    # Reviewer Functions
    "Again":                lambda: mw.reviewer._answerCard(1),                 # Works
    "Hard":                 lambda: mw.reviewer._answerCard(2),                 # Works
    "Good":                 lambda: mw.reviewer._answerCard(3),                 # Works
    "Easy":                 lambda: mw.reviewer._answerCard(4),                 # Works
    "Suspend Card":         mw.reviewer.suspend_current_card,                   # Works
    "Suspend Note":         mw.reviewer.suspend_current_note,                   # Works
    "Bury Card":            mw.reviewer.bury_current_card,                      # Works
    "Bury Note":            mw.reviewer.bury_current_note,                      # Works
    "Flag":                 cycle_flag,                                         # Works
    "Mark Note":            mw.reviewer.toggle_mark_on_current_note,            # Works
    "Delete Note":          mw.reviewer.delete_current_note,                    # Works
    "Record Voice":         mw.reviewer.onRecordVoice,                          # Not Tested
    "Replay Voice":         mw.reviewer.onReplayRecorded,                       # Not Tested
    "Card Info":            card_info,                                          # Works
    "Previous Card Info":   previous_card_info,                                 # Works
    "Pause Audio":          mw.reviewer.on_pause_audio,                         # Works
    "Audio +5s":            mw.reviewer.on_seek_forward,                        # Works
    "Audio -5s":            mw.reviewer.on_seek_backward,                       # Works
    "Replay Audio":         mw.reviewer.replayAudio,                            # Works
    "Edit Note":            mw.onEditCurrent,                                   # Not Tested
    "Flip Card":            mw.reviewer.onEnterKey,                             # Works
    "Set Due Date":         mw.reviewer.on_set_due,                             # Works
}


release_actions = {
    "": _pass,
    "Click":                click_release,
    "Secondary Click":      lambda: click_release(button=Qt.MouseButton.RightButton),
    "Select Next":          _pass,
    "Select Previous":      _pass,
    "Up":                   _pass,
    "Down":                 _pass,
    "Up by 10":             _pass,
    "Down by 10":           _pass,
    "Scroll Up":            _pass,
    "Scroll Down":          _pass,
    "Next Deck":            _pass,
    "Previous Deck":        _pass,
    "Next Due Deck":        _pass,
    "Previous Due Deck":    _pass,
}


state_actions = {
    "all": [
        "",

        # Common Function                                           
        "Sync",                 "Overview",             "Browser",              "Statistics",
        "Main Screen",          "Review",               "Undo",                 "Redo",
        "Back",                 "Forward",              "Enter",                "Fullscreen",
        "Volume Up",            "Volume Down",          "Add",                  "Hide Cursor",
        "About Anki",           "Preferences",          "Quit",

        # UI Functions  
        "Click",                "Secondary Click",      "Select Next",          "Select Previous",
        "Select",               "Scroll Up",            "Scroll Down",          "Options",

        # Deck Browser Functions    
        "Check Database",       "Check Media",          "Empty Cards",          "Manage Note Types",
        "Study Deck",
    ],  

    "deckBrowser": [    
        "",

        # Common Function                                               
        "Sync",                 "Overview",             "Browser",              "Statistics",
        "Main Screen",          "Review",               "Undo",                 "Redo",
        "Back",                 "Forward",              "Enter",                "Fullscreen",
        "Volume Up",            "Volume Down",          "Hide Cursor",          "Add",
        "Preferences",          "Quit",

        # UI Functions      
        "Click",                "Secondary Click",      "Select Next",          "Select Previous",
        "Select",               "Scroll Up",            "Scroll Down",          "Options",

        # Deck Browser Functions    
        "Next Deck",            "Previous Deck",        "Next Due Deck",        "Previous Due Deck",
        "Collapse/Expand",      "Study Deck",           "Empty Cards",          "Manage Note Types",
        "Check Database",       "Check Media",
        
    ],      

    "overview": [       
        "",   

        # Common Function                                                   
        "Sync",                 "Overview",             "Browser",              "Statistics",
        "Main Screen",          "Review",               "Undo",                 "Redo",
        "Back",                 "Forward",              "Enter",                "Fullscreen",
        "Volume Up",            "Volume Down",          "Add",                  "Hide Cursor",
        "Preferences",          "Quit",                 

        # UI Functions      
        "Click",                "Secondary Click",      "Select Next",          "Select Previous",
        "Select",               "Scroll Up",            "Scroll Down",          "Options",

        # Deck Browser Functions    
        "Next Deck",            "Previous Deck",        "Next Due Deck",        "Previous Due Deck",
        "Collapse/Expand",      "Filter",               "Rebuild",              "Empty",

        # Overview Functions        
        "Custom Study",     
    ],      

    "review": [     
        "",      

        # Common Function                                                   
        "Sync",                 "Overview",             "Browser",              "Statistics",
        "Main Screen",          "Review",               "Undo",                 "Redo",
        "Back",                 "Forward",              "Enter",                "Fullscreen",
        "Volume Up",            "Volume Down",          "Add",                  "Preferences",          
        "Quit",                 "Hide Cursor",

        # UI Functions      
        "Click",                "Secondary Click",      "Select Next",          "Select Previous",
        "Select",               "Scroll Up",            "Scroll Down",          "Options",

        # Reviewer Functions        
        "Again",                "Hard",                 "Good",                 "Easy",
        "Suspend Card",         "Suspend Note",         "Bury Card",            "Bury Note",
        "Mark Note",            "Delete Note",          "Record Voice",         "Replay Voice",
        "Card Info",            "Previous Card Info",   "Pause Audio",          "Audio +5s",
        "Audio -5s",            "Replay Audio",         "Edit Note",            "Flip Card",
        "Flag",                 "Set Due Date",
    ],      

    "question": [       
        "",      

        # Common Function                                                   
        "Sync",                 "Overview",             "Browser",              "Statistics",
        "Main Screen",          "Review",               "Undo",                 "Redo",
        "Back",                 "Forward",              "Enter",                "Fullscreen",
        "Volume Up",            "Volume Down",          "Add",                  "Preferences",
        "Quit",                 "Hide Cursor",

        # UI Functions      
        "Click",                "Secondary Click",      "Select Next",          "Select Previous",
        "Select",               "Scroll Up",            "Scroll Down",          "Options",

        # Reviewer Functions        
        "Again",                "Hard",                 "Good",                 "Easy",
        "Suspend Card",         "Suspend Note",         "Bury Card",            "Bury Note",
        "Mark Note",            "Delete Note",          "Record Voice",         "Replay Voice",
        "Card Info",            "Previous Card Info",   "Pause Audio",          "Audio +5s",
        "Audio -5s",            "Replay Audio",         "Edit Note",            "Flip Card",
        "Flag",                 "Set Due Date",
    ],      

    "answer": [     
        "",      

        # Common Function                                                   
        "Sync",                 "Overview",             "Browser",              "Statistics",
        "Main Screen",          "Review",               "Undo",                 "Redo",
        "Back",                 "Forward",              "Enter",                "Fullscreen",
        "Volume Up",            "Volume Down",          "Menubar",              "Add",
        "About Anki",           "Preferences",          "Quit",                 "Hide Cursor",

        # UI Functions      
        "Click",                "Secondary Click",      "Select Next",          "Select Previous",
        "Select",               "Scroll Up",            "Scroll Down",          "Options",

        # Reviewer Functions        
        "Again",                "Hard",                 "Good",                 "Easy",
        "Suspend Card",         "Suspend Note",         "Bury Card",            "Bury Note",
        "Mark Note",            "Delete Note",          "Record Voice",         "Replay Voice",
        "Card Info",            "Previous Card Info",   "Pause Audio",          "Audio +5s",
        "Audio -5s",            "Replay Audio",         "Edit Note",            "Flip Card",
        "Flag",                 "Set Due Date",
    ],      

    "dialog": [     
        "",

        # Common Function                                                   
        "Undo",                 "Redo",                 "Quit",                 "Menubar",
        "Back",                 "Forward",              "Enter",                "Hide Cursor",

        # UI Functions      
        "Click",                "Secondary Click",      "Select Next",          "Select Previous",
        "Select",               "Focus Main Window",    "Switch Window",        "Escape",
        "Up",                   "Down",                 "Up by 10",             "Down by 10",
        "Scroll Up",            "Scroll Down",         
    ],
}
