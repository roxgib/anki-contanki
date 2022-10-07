"""An add-on for Anki, adding support for controllers and gamepads"""

from aqt import mw as _mw
assert _mw is not None
mw = _mw
from .contanki import Contanki

mw.contanki = Contanki(mw)
