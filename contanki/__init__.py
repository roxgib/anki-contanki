"""An add-on for Anki, adding support for controllers and gamepads"""

from aqt import mw
from .contanki import Contanki

mw.contanki = Contanki(mw)
