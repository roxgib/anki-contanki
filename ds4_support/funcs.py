from aqt.operations.collection import undo, redo
from aqt.reviewer import replay_audio

func_map = {
    # Reviewer Functions
    "replay_audio": replay_audio
    "reviewer edit current": self.mw.onEditCurrent,
    "reviewer flip card": self.onEnterKey,
    "reviewer flip card 1": self.onEnterKey,
    "reviewer flip card 2": self.onEnterKey,
    "reviewer flip card 3": self.onEnterKey,
    "reviewer options menu": self.onOptions,
    "reviewer record voice": self.onRecordVoice,
    "reviewer play recorded voice": self.onReplayRecorded,
    "reviewer play recorded voice 1": self.onReplayRecorded,
    "reviewer play recorded voice 2": self.onReplayRecorded,
    "reviewer delete note": self.onDelete,
    "reviewer suspend card": self.onSuspendCard,
    "reviewer suspend note": self.onSuspend,
    "reviewer bury card": self.onBuryCard,
    "reviewer bury note": self.onBuryNote,
    "reviewer mark card": self.onMark,
    "reviewer set flag 1": lambda: self.setFlag(1),
    "reviewer set flag 2": lambda: self.setFlag(2),
    "reviewer set flag 3": lambda: self.setFlag(3),
    "reviewer set flag 4": lambda: self.setFlag(4),
    "reviewer set flag 0": lambda: self.setFlag(0),
    "reviewer replay audio": self.replayAudio,
    "reviewer choice 1": lambda: self._answerCard(1),
    "reviewer choice 2": lambda: self._answerCard(2),
    "reviewer choice 3": lambda: self._answerCard(3),
    "reviewer choice 4": lambda: self._answerCard(4),
    "editor card layout": self.onCardLayout, True),
    "editor bold": self.toggleBold,
    "editor italic": self.toggleItalic,
    "editor underline": self.toggleUnderline,
    "editor superscript": self.toggleSuper,
    "editor subscript": self.toggleSub,
    "editor remove format": self.removeFormat,
    "editor foreground": self.onForeground,
    "editor change col": self.onChangeCol,
    "editor cloze": self.onCloze,
    "editor cloze alt": self.onAltCloze,
    "editor add media": self.onAddMedia,
    "editor record sound": self.onRecSound,
    "editor insert latex": self.insertLatex,
    "editor insert latex equation": self.insertLatexEqn,
    "editor insert latex math environment": self.insertLatexMathEnv,
    "editor insert mathjax inline": self.insertMathjaxInline,
    "editor insert mathjax block": self.insertMathjaxBlock),
    "editor html edit": self.onHtmlEdit,
    "editor focus tags": self.onFocusTags,
    "editor _extras"]["paste custom text": self.customPaste
    }

}

config_map_reviewer_question = {

}

config_map_reviewer_answer = {

}

config_map_decks = {

}

config_map_overview = {

}

config_map_stats = {

}

state_map = {
    "startup": None,
    "deckBrowser":  config_map_decks,
    "overview": config_map_overview,
    "profileManager": None,
    ('review', 'question'): config_map_reviewer_question,
    ('review', 'answer'): config_map_reviewer_answer
}

### Reviewing

from aqt.operations.card import set_card_flag
from aqt.operations.scheduling import forget_cards
from aqt.operations.tag import add_tags_to_notes


def cycle_flag():
    
    set_card_flag(card_ids=Sequence, CardId=flag=int)


def tag():
    
    add_tags_to_notes(note_ids: Sequence, NoteId= space_separated_tags: str)


def forget():
    
    forget_cards(card_ids: Sequence[CardId]):

