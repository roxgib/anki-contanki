from aqt import mw

# Internal

def _get_state():
    return mw.reviewer.state if mw.state == 'review' else mw.state

### Review

def _cycle_flag(flags: list):
    flag = mw.reviewer.card.flags
    if flag == 0:
        mw.reviewer.setFlag(flags[0])
    elif flag not in flags:
        mw.reviewer.setFlag(0)
    elif flag == flags[-1]:
        mw.reviewer.setFlag(0)
    else:
        mw.reviewer.setFlag(flags[flags.index(flag)+1])

flags = mw.addonManager.getConfig(__name__)['flags']
cycle_flag = lambda: _cycle_flag(flags)

### Deck Browser

def select_deck(direction: bool, due:bool = False) -> None:
    decks = mw.col.decks.all_names_and_ids()
    decks = [deck for deck in decks if not any(d['collapsed'] for d in mw.col.decks.parents(deck.id))]
    decks = [deck.id for deck in sorted(decks, key = lambda deck: deck.name)]

    if due: decks = [deck for deck in decks if len(mw.col.find_cards(f'"deck:{deck}" is:due')) > 0]
    
    if len(decks) == 0: return 
    
    if (c_deck := mw.col.decks.get_current_id()) in decks:
        c_deck_index = decks.index(c_deck)
    else:
        c_deck_index = len(decks)
    
    if direction:
        if len(decks) == c_deck_index + 1:
            c_deck_index = -1
        mw.col.decks.select(decks[c_deck_index + 1])
    else:
        mw.col.decks.select(decks[c_deck_index - 1])

    mw.reset()

def back():
    if mw.state == 'review':
        mw.moveToState("overview")
    else:
        mw.moveToState("deckBrowser")

def forward():
    if mw.state == "deckBrowser":
        mw.moveToState("overview")
    elif mw.state == "overview":
        mw.moveToState("review")

# Common

def on_enter():
    if mw.state == 'review':
        mw.reviewer.onEnterKey()
    elif mw.state == 'deckBrowser':
        mw.moveToState("overview")
    elif mw.state == "overview":
        mw.moveToState("review")

def scroll_up():
    mw.web.eval(f"window.scrollBy(0, -80);")

def scroll_down():
    mw.web.eval(f"window.scrollBy(0, 80);")

def onOptions():
    if mw.state == 'review':
        mw.reviewer.onOptions()
    elif mw.state == 'deckBrowser':
        pass
    elif mw.state == "overview":
        pass

def _pass():
    pass


func_map = {
    # Common Function
    "Sync": mw.onSync,
    "Overview": lambda: mw.moveToState("overview"),
    "Browser": mw.onBrowse,
    "Statistics": mw.onStats,
    "Study Deck": mw.onOverview,
    "Main Screen": lambda: mw.moveToState("deckBrowser"),
    "Review": lambda: mw.moveToState("review"),
    "Undo": mw.undo,
    "Redo": mw.redo,
    "Back": back,
    "Forward": forward,
    "Enter": on_enter,

    "Fullscreen": mw.on_toggle_fullscreen,
    "Volume Up": _pass,
    "Volume Down": _pass,

    "Menubar": _pass,
    "Add": _pass,
    "About Anki": mw.onAbout,
    "Preferences": mw.onPrefs,
    "Quit": mw.close,
    "Switch Profile": mw.unloadProfileAndShowProfileManager,
    "Hide Cursor": _pass,
    "Donate": _pass,
    "Anki Help": mw.onDocumentation,
    "Help": _pass,
    
    
    # Deck Browser Functions

    "Next Deck": lambda: select_deck(True),
    "Previous Deck": lambda: select_deck(False),
    "Next Due Deck": lambda: select_deck(True, True),
    "Previous Due Deck": lambda: select_deck(False, True),
    "Collapse/Expand": lambda: mw.deckBrowser._collapse(mw.col.decks.get_current_id()),
    "Filter": mw.onCram,
    "Rebuild": _pass,
    "Empty": _pass,
    
    "Check Database": mw.onCheckDB,
    "Check Media": mw.on_check_media_db,
    "Empty Cards": mw.onEmptyCards,
    "Manage Note Types": mw.onNoteTypes,
    "Study Deck": mw.onStudyDeck,
    "Export": mw.onExport,
    "Import": mw.onImport,

    # Reviewer Functions
    
    "Again": lambda: mw.reviewer._answerCard(1),
    "Hard": lambda: mw.reviewer._answerCard(2),
    "Good": lambda: mw.reviewer._answerCard(3),
    "Easy": lambda: mw.reviewer._answerCard(4),

    "Suspend Card": mw.reviewer.suspend_current_card,
    "Suspend Note": mw.reviewer.suspend_current_note,
    "Bury Card": mw.reviewer.bury_current_card,
    "Bury Note": mw.reviewer.bury_current_note,
    "Mark Note": mw.reviewer.toggle_mark_on_current_note,
    "Delete Note": mw.reviewer.delete_current_note,
    
    "Record Voice": _pass,
    "Replay Voice": _pass,
    "Card Info": _pass,
    "Previous Card Info": _pass,
    "Pause Audio": _pass,
    "Audio +5s": _pass,
    "Audio -5s": _pass,


    "Replay Audio": mw.reviewer.replayAudio,
    "Edit Note": mw.onEditCurrent,
    "Flip Card": mw.reviewer.onEnterKey,
    "Cycle Flag": cycle_flag,
    "Set Due Date": _pass,
}