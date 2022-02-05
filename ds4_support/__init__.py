from .controller import initialise
from aqt import gui_hooks
gui_hooks.main_window_did_init.append(initialise)