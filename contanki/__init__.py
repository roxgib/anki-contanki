"""An add-on for Anki, adding support for controllers and gamepads"""

import os

from aqt import mw
from .utils import user_profile_path, user_controllers_path

from .contanki import Contanki

assert mw is not None

if not os.path.exists(user_profile_path):
    os.mkdir(user_profile_path)

if not os.path.exists(user_controllers_path):
    os.mkdir(user_controllers_path)

mw.contanki = Contanki(mw) # type: ignore
