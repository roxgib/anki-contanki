from .controller import initialise

from aqt import mw
from aqt import gui_hooks
from aqt.utils import qconnect, QAction, tooltip

def on_test():
    pass

test = QAction(f"DS4 Test", mw)
qconnect(test.triggered, on_test)
mw.form.menuTools.addAction(test)

gui_hooks.main_window_did_init.append(initialise)