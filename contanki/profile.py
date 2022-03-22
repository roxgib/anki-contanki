from copy import deepcopy
from typing import Dict, List, Optional
from re import search
import os
import json

from aqt.utils import showInfo, tooltip
from aqt.qt import QMessageBox, QInputDialog

from .CONSTS import BUTTON_NAMES
from .actions import *
from .svg import CONTROLLER_IMAGE_MAPS

addon_path = os.path.dirname(os.path.abspath(__file__))
user_files_path = os.path.join(addon_path, 'user_files')
user_profile_path = os.path.join(user_files_path, 'profiles')
default_profile_path = os.path.join(addon_path, 'profiles')
controllers_path = os.path.join(addon_path, 'controllers')


class Profile:
    def __init__(self, profile: dict):
        self.bindings = profile['bindings']
        self.mods = profile['mods']
        self.name = profile['name']
        self.len_buttons, self.len_axes = self.size = profile['size']
        self.controller = profile['controller']
        self.axes_bindings = profile['axes_bindings']
        self.buildActions()

    def buildActions(self) -> dict:
        bindings = self.getInheritedBindings()
        bindings['NoFocus'] = {0: {0:'Focus Main Window'}}
        bindings['transition'] = {0: {}}
        for i in range(len(self.mods)):
            bindings['NoFocus'][i + 1] = dict()
            bindings['transition'][i + 1] = dict()
        self.actions = dict()
        self.releaseActions = dict()
        for state, a in bindings.items():
            self.actions[state] = dict()
            self.releaseActions[state] = dict()
            for mod, b in a.items():
                self.actions[state][mod] =  dict()
                self.releaseActions[state][mod] = dict()
                for button, action in b.items():
                    if action in button_actions:
                        self.actions[state][mod][button] = button_actions[action]
                    if action in release_actions:
                        self.releaseActions[state][mod][button] = release_actions[action]
        
        return self.actions

    def getInheritedBindings(self) -> dict:
        bindings = deepcopy(self.bindings)
        for state, sdict in bindings.items():
            for mod, mdict in sdict.items():
                if state == 'question' or state == 'answer':
                    for button, action in bindings['review'][mod].items():
                        if button not in mdict or mdict[button] == "":
                            mdict[button] = action
                if state != 'all':
                    for button, action in bindings['all'][mod].items():
                        if button not in mdict or mdict[button] == "":
                            mdict[button] = action

        return bindings

    def doAction(self, state: str, mod: int, button: int) -> None:
        if button in self.actions[state][mod]:
            self.actions[state][mod][button]()

    def doReleaseAction(self, state: str, mod: int, button: int) -> None:
        if button in self.releaseActions[state][mod]:
            self.releaseActions[state][mod][button]()

    def doAxesActions(self, state: str, mod: int, axes: List[float]) -> None:
        mx = my = sx = sy = 0
        for (axis, assignment), value in zip(self.axes_bindings.items(), axes):
            if assignment == "Unassigned":
                continue
            elif assignment == "Buttons":
                if value < -0.3:
                    if not mw.contanki.axes[axis]:
                        self.doAction(state, mod, axis * 2 + 100)
                        mw.contanki.axes[axis] = True
                elif value > 0.3:
                    if not mw.contanki.axes[axis]:
                        self.doAction(state, mod, axis * 2 + 1 + 100)
                        mw.contanki.axes[axis] = True
                else:
                    mw.contanki.axes[axis] = False
            elif assignment == "Scroll Horizontal":
                sx = value
            elif assignment == "Scroll Vertical":
                sy = value
            elif assignment == "Cursor Horizontal":
                mx = value
            elif assignment == "Cursor Vertical":
                my = value
        if mx or my:
            moveMouse(mx, my)
        if sx or sy:
            scroll(sx, sy)

    def updateBinding(
        self, 
        state: str,
        mod: int,
        button: int,
        action: str,
        build_actions: bool = True
    ) -> None:
        if mod not in self.bindings[state]:
            self.bindings[state][mod] = dict()
        if button not in self.bindings[state][mod]:
            self.bindings[state][mod][button] = ""
        if action == 'mod' or self.bindings[state][mod][button] == 'mod':
            showInfo('Error: use Binding.updateMods to change the modifier keys')
        self.bindings[state][mod][button] = action
        if build_actions:
            self.buildActions()

    def changeMod(self, old_mod: int, new_mod: int) -> None:
        if old_mod in self.mods:
            self.mods[self.mods.index(old_mod)] = new_mod
        for state in self.bindings:
            for mod in state:
                self.bindings[state][mod][old_mod] = ""
                self.bindings[state][mod][new_mod] = "mod"

    def getCompatibility(self, controller):
        pass

    def save(self) -> None:
        path = os.path.join(user_profile_path, self.name)

        output =  {
        'name'             : self.name,
        'size'             : self.size,
        'mods'             : self.mods,
        'bindings'         : self.bindings,
        'controller'         : self.controller,
        'axes_bindings'    : self.axes_bindings,
        }

        with open(path, 'w') as f:
                json.dump(output, f)


def identifyController(id: str, len_buttons: int, len_axes: int) -> str:
    vendor_id = search(r'Vendor:\s([0-9a-fA-F]{4}?)', id)
    device_id = search(r'Product:\s([0-9a-fA-F]{4}?)', id)

    controllers = json.loads(get_file('controllerIDs.json'))

    if vendor_id in controllers['vendors']:
        vendor_name = controllers['vendors'][vendor_id]
        if device_id in controllers['devices'][vendor_id]:
            device_name = controllers['vendors'][vendor_id][device_id]
            controllers = getControllerList()
            if device_name in controllers:
                return device_name

    id = id.lower()

    if 'dualshock' in id or 'playstation' or 'sony' in id:
        if len_axes == 0:
            return "PlayStation Controller"
        elif len_buttons == 17:
            return 'DualShock 3'
        elif len_buttons == 18:
            return 'DualShock 4'
        elif 'DualSense' in id or len_buttons == 19:
            return 'DualSense'

    if 'xbox' in id:
        if '360' in id:
            return 'Xbox 360 Controller'
        elif 'one' in id:
            return 'Xbox One Controller'
        elif 'elite' in id:
            return 'Xbox Elite Controller'
        elif 'series' in id:
            return 'Xbox Series Controller'
        elif 'adaptive' in id:
            return 'Xbox Adaptive Controller'
        elif len_buttons == 16:
            return 'Xbox 360 Controller'
        elif len_buttons == 17:
            return 'Xbox Series Controller'

    if 'joycon' in id or 'joy-con' in id:
        if 'left' in id:
            return 'JoyCon Left'
        if 'right' in id:
            return 'JoyCon Right'
        else:
            return 'JoyCon'

    if 'switch' in id:
        if 'pro' in id:
            return 'Switch Pro Controller'
        else:
            if 'left' in id:
                return 'JoyConLeft'
            if 'right' in id:
                return 'JoyConRight'
            else:
                return 'JoyCon'

    if 'wii' in id:
        if 'nunchuck' in id:
            return 'Wii Nunchuck'
        else:
            return 'Wii Remote'

    if 'steam' in id or 'valve' in id:
        return 'Steam Controller'

    return None


def getControllerList():
    return list(BUTTON_NAMES.keys())


def getProfileList(compatibility: Optional[str] = None, include_defaults: bool = True) -> List[str]:
    profiles = list()
    for file_name in os.listdir(user_profile_path):
        if file_name not in ['placeholder', ".DS_Store"]:
            profiles.append(file_name)

    if include_defaults:
        for file_name in os.listdir(default_profile_path):
            if file_name == str(compatibility) or not compatibility:
                if file_name not in ['placeholder', ".DS_Store"]:
                    profiles.append(file_name)

    return sorted(profiles)


def getProfile(name: str) -> Profile:
    path = os.path.join(default_profile_path, name)
    if not os.path.exists(path):
        path = os.path.join(user_profile_path, name)
        if not os.path.exists(path):
            showInfo(f"Couldn't find profile '{name}'")
            return

    def intKeys(d: dict) -> dict:
        if not isinstance(d, dict): return d
        e = dict()
        for k, v in d.items():
            try: 
                e[int(k)] = v
            except:
                e[k] = v
        return e

    with open(path) as f:
        profile = Profile(json.load(f, object_hook=intKeys))

    return profile


def createProfile(controller: str = None) -> Profile:
    old, okay1 = QInputDialog().getItem(
        mw, 
        'Create New Profile', 
        'Select an existing profile to copy:', 
        getProfileList(),
        editable = False,
    )
    if not okay1 or not old: return
    name, okay2 = QInputDialog().getText(mw, 'Create New Profile', 'Enter the new profile name:')
    if not name or not okay2: return

    if os.path.exists(os.path.join(user_profile_path, name)):
        showInfo(f"Error: Profile name '{name}' already in use")
        return
    if os.path.exists(os.path.join(default_profile_path, name)):
        showInfo(f"Error: Profile name '{name}' already in use")
        return

    copyProfile(old, name)
    return getProfile(name)


def deleteProfile(name: str) -> None:
    path = os.path.join(default_profile_path, name)
    if os.path.exists(path):
        tooltip('Cannot delete built-in profiles.')

    path = os.path.join(user_profile_path, name)
    def delete():
        os.remove(path)
    
    if os.path.exists(path):
        confirm = QMessageBox()
        confirm.setText(f"This will delete the profile '{name}'.")
        confirm.setWindowTitle("Overwrite Profile")
        confirm.buttonClicked.connect(delete)
        confirm.open()


def copyProfile(name: str, new_name: str) -> None:
    if not os.path.exists(os.path.join(default_profile_path, name)):
        if not os.path.exists(os.path.join(user_profile_path, name)):
            tooltip(f"Error: profile '{name}' does not exist")
            return

    profile = getProfile(name)
    profile.name = new_name
    profile.save()


def findProfile(controller: str, len_buttons: int, len_axes: int) -> Profile:
    with open(os.path.join(user_files_path, 'controllers'), 'r') as f:
        controllers = json.load(f)
    if controller in controllers:
        return getProfile(controllers[controller])
    if (n := f'Standard Gamepad ({len_buttons} Buttons, {len_axes} Axes)') in os.listdir(default_profile_path):
        profile_to_copy = n
    else:
        profile_to_copy = 'Blank'
    copyProfile(profile_to_copy, controller)
    updateControllers(controller, controller)
    profile = getProfile(controller)
    if controller in CONTROLLER_IMAGE_MAPS:
        profile.controller = controller
        profile.save()
    return profile


def updateControllers(controller, profile):
    with open(os.path.join(user_files_path, 'controllers'), 'r') as f:
        controllers = json.load(f)
    controllers[controller] = profile
    with open(os.path.join(user_files_path, 'controllers'), 'w') as f:
        json.dump(controllers, f)