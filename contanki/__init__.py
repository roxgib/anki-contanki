"""An add-on for Anki, adding support for controllers and gamepads"""

from aqt import mw
from .contanki import Contanki

assert mw is not None

instance = Contanki(mw)
mw.contanki = instance # type: ignore
