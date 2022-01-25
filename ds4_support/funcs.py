from aqt import mw

def cycle_flag():
    flag = mw.reviewer.card.flags
    mw.reviewer.setFlag(flag+1)

### Deck Browser

def select_deck(direction: bool, due:bool = False) -> None:
    decks = mw.col.decks.all_names_and_ids() # Inefficient to call each time?
    decks = [deck for deck in decks if all(not d['collapsed'] for d in mw.col.decks.parents(deck['id']))]
    decks = sorted([deck['id'] for deck in decks], key = lambda deck: deck['name'])

    c_deck_index = decks.index(mw.col.decks.get_current_id())

    if direction:
        mw.col.decks.select(decks[c_deck_index - 1])
    else:
        mw.col.decks.select(decks[c_deck_index + 1])

    mw.refresh()

def _pass():
    pass

func_map = {
    # Common Function
    "Sync": mw.onSync,
    "Overview": lambda: mw.onOverview,
    "Browser": mw.onBrowse,
    "Stats": mw.onStats,
    "Study Deck": mw.onStudyDeck,
    "Main Screen": lambda: mw.moveToState("deckBrowser"),
    "Review": lambda: mw.moveToState("review"),
    "Undo": mw.undo,
    "Redo": mw.redo,

    "": _pass,
    
    # Deck Browser Functions

    "Select Next Deck": lambda: select_deck(True),
    "Select Previous Deck": lambda: select_deck(False),
    "Collapse/Expand Deck": lambda: mw.deckBrowser._collapse(mw.col.decks.get_current_id()),

    # Reviewer Functions
    
    "Answer 1": lambda: mw.reviewer._answerCard(1),
    "Answer 2": lambda: mw.reviewer._answerCard(2),
    "Answer 3": lambda: mw.reviewer._answerCard(3),
    "Answer 4": lambda: mw.reviewer._answerCard(4),

    "Suspend Card": mw.reviewer.suspend_current_card,
    "Suspend Note": mw.reviewer.suspend_current_note,
    "Bury Card": mw.reviewer.bury_current_card,
    "Bury Note": mw.reviewer.bury_current_note,
    "Mark Note": mw.reviewer.toggle_mark_on_current_note,
    "Delete Note": mw.reviewer.delete_current_note,

    "Replay Audio": mw.reviewer.replayAudio,
    "Edit Note": mw.onEditCurrent,
    "Options Menu": mw.reviewer.onOptions,
    "Flip Card": mw.reviewer.onEnterKey,
    "Cycle Flag": cycle_flag,
}