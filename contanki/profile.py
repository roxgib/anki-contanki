from copy import deepcopy
from curses.ascii import isdigit
from typing import Dict, List, Optional
from re import search
import os
import json

from aqt.utils import showInfo, tooltip
from aqt.qt import QMessageBox, QInputDialog

from .CONSTS import CONTROLLER_NAMES
from .actions import *

addon_path = os.path.dirname(os.path.abspath(__file__))
user_profile_path = os.path.join(addon_path, 'user_files', 'profiles')
user_files_path = os.path.join(addon_path, 'user_files')
default_profile_path = os.path.join(addon_path, 'profiles')


class Profile:
    def __init__(self, profile: dict):
        self.bindings = profile['bindings']
        self.mods = profile['mods']
        self.name = profile['name']
        self.size = profile['size']
        self.len_buttons = profile['size'][0]
        self.len_axes = profile['size'][1]
        self.axes_bindings = profile['axes_bindings']
        self.buildActions()

    def buildActions(self) -> None:
        bindings = deepcopy(self.bindings)

        for key, value in bindings['review'].items():
            if key not in bindings['question'] or bindings['question'][key] == '':
                bindings['question'][key] = value
            if key not in bindings['answer'] or bindings['answer'][key] == '':
                bindings['answer'][key] = value

        for key, value in bindings['all'].items():
            for state, d in bindings.items():
                if key not in d or d[key] == '':
                    bindings[state][key] = value

        bindings['NoFocus'] = {0: {0:'Focus Main Window'}}

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
                    if action in button_release_actions:
                        self.releaseActions[state][mod][button] = button_release_actions[action]


    def doAction(self, state: str, mod: int, button: int) -> None:
        if button in self.actions[state][mod]:
            self.actions[state][mod][button]()


    def doReleaseAction(self, state: str, mod: int, button: int) -> None:
        if button in self.releaseActions[state][mod]:
            self.releaseActions[state][mod][button]()


    def doAxesActions(self, state: str, mod: int, axes: List[float]) -> None:
        mx = my = sx = sy = 0
        for (axis, assignment), value in zip(self.axes_bindings.items(), axes):
            if value == 0 or assignment == "Unassigned":
                continue
            elif assignment == "Buttons":
                if value < 0:
                    self.doAction(state, mod, axis + self.len_buttons)
                if value > 0:
                    self.doAction(state, mod, axis + self.len_buttons + self.len_axes)
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
        try:
            if button:
                self.bindings[state][mod][button] = action
        except KeyError:
            showInfo("Error: couldn't update action. Perhaps the wrong controller type is selected")
        else:
            if build_actions:
                self.buildActions()


    def changeMod(self, old_mod: int, new_mod: int, axis: bool = False) -> None:
        if axis:
            new_mod += 100
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
        'axes_bindings'    : self.axes_bindings,
        }

        with open(path, 'w') as f:
                json.dump(output, f)


def identifyController(id: str) -> str:
    vendor_id = search(r'Vendor:\s([0-9a-fA-F]{4}?)', id)
    device_id = search(r'Product:\s([0-9a-fA-F]{4}?)', id)

    controllers = json.loads(get_file('./controllerIDs.json'))

    if vendor_id in controllers['vendors']:
        vendor_name = controllers['vendors'][vendor_id]
        if device_id in controllers['devices'][vendor_id]:
            device_name = controllers['vendors'][vendor_id]

    id = id.lower()

    if 'dualshock' in id or 'playstation' in id:
        if 'dualshock 4' in id:
            return 'DualShock4'
        elif 'dualshock 4' in id:
            return 'DualShock4'
        elif 'dualsense' in id:
            return 'DualSense'
    elif 'xbox' in id:
        if '360' in id:
            return 'Xbox306'
        elif 'one' in id:
            return 'XboxOne'
        elif 'elite' in id:
            return 'XboxElite'
        elif 'series' in id:
            return 'XboxSeries'
    elif 'joycon' in id or 'joy-con' in id:
        if 'left' in id:
            return 'JoyConLeft'
        if 'right' in id:
            return 'JoyConRight'
        else:
            return 'JoyCon'
    elif 'switch' in id:
        if 'pro' in id:
            return 'SwitchPro'
        else:
            if 'left' in id:
                return 'JoyConLeft'
            if 'right' in id:
                return 'JoyConRight'
            else:
                return 'JoyCon'
    elif 'wii' in id or 'joy-con' in id:
        if 'nunchuck' in id:
            return 'WiiNunchuck'
        else:
            return 'Wii'


def getControllerList(pretty = False):
    path = os.path.join(addon_path, 'controllers')
    if pretty:
        return sorted([getControllerName(controller) for controller in os.listdir(path) if getControllerName(controller)])
    else:
        return sorted([controller for controller in os.listdir(path) if getControllerName(controller)])


def getControllerName(controller: str) -> str:
    if controller in CONTROLLER_NAMES:
        return CONTROLLER_NAMES[controller]


def getProfileList(compatibility: Optional[str] = None, pretty: bool = False) -> List[str]:
    profiles = list()
    for file_name in os.listdir(user_profile_path):
        profiles.append(file_name)

    for file_name in os.listdir(default_profile_path):
        if file_name == str(compatibility) or not compatibility:
            profiles.append(file_name)

    if pretty:
        return sorted([getProfile(profile).name for profile in profiles])
    else:
        return sorted(profiles)


def getProfile(name: str) -> Profile:
    if not name: return
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

    with open(path, 'rt') as f:
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
    else:
        for p in os.listdir(default_profile_path):
            if getProfile(p).size == [len_buttons, len_axes]:
                controllers[controller] = p
                with open(os.path.join(user_files_path, 'controllers'), 'w') as f:
                    json.dump(controllers, f)
                profile = p
                break
        profile = 'Standard Gamepad (18 Button, 4 Axis)'
    copyProfile(profile, f'Controller ({len_buttons} Buttons, {len_axes} Axes)')
    controllers[controller] = f'Controller ({len_buttons} Buttons, {len_axes} Axes)'
    with open(os.path.join(user_files_path, 'controllers'), 'w') as f:
        json.dump(controllers, f)
    # showInfo("It seems your controller has an unusual configuration. You'll have to set up the controls yourself.")
    return getProfile(controllers[controller])