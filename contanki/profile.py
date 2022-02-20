from typing import Dict, List, Optional
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
        self.controller = profile['controller']
        self.buildActions()


    def buildActions(self):
        self.actions = dict()
        self.releaseActions = dict()
        for state, a in self.bindings.items():
            self.actions[state] = dict()
            for mod, b in a.items():
                self.actions[state][mod] =  dict()
                for button, action in b.items():
                    if action in button_actions:
                        self.actions[state][mod][button] = button_actions[action]
                    if action in button_release_actions:
                        self.releaseActions[state][mod][button] = button_release_actions[action]


    def doAction(self, state, mod, button = None, axis = None, value = None):
        try:
            if button:
                self.actions[state][mod][button]()
            elif axis:
                self.actions[state][mod][axis + 100](value)
        except KeyError:
            tooltip('Error: not mapped')

    
    def doReleaseAction(self, state, mod, button = None, axis = None, value = None):
        try:
            if button:
                self.actions[state][mod][button]()
            elif axis:
                self.actions[state][mod][axis + 100](value)
        except KeyError:
            tooltip('Error: not mapped')

        
    def updateBinding(self, state: str, mod: int, button: int = None, axis: int = None, action = "") -> None:
        if action == 'mod':
            showInfo('Error: use Binding.updateMods to change the modifier keys')
        try:
            if button:
                self.bindings[state][mod][button] = action
            elif axis:
                self.actions[state][mod][axis + 100] = action
        except KeyError:
            showInfo("Error: couldn't update action. Perhaps the wrong controller type is selected")
        else:
            self.buildActions()

    def updateMods(self, old_mod: int, new_mod: int, axis: bool = False) -> None:
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

    def save(self) -> dict:
        return {
        'name'      : self.name,
        'size'      : self.size,
        'controller': self.controller,
        'mods'      : self.mods,
        'bindings'  : self.bindings,
        }

def identifyController(id: str) -> str:
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

    with open(path, 'rt') as f:
        out = Profile(json.load(f))

    return out


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


def saveProfile(profile: Profile) -> None:
    path = os.path.join(default_profile_path, profile.name)
    if os.path.exists(path):
        tooltip('Cannot overwrite built-in profiles.')
        return
    path = os.path.join(user_profile_path, profile.name)

    with open(path, 'w') as f:
            json.dump(profile.save(), f)

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

    saveProfile(profile)


def findProfile(controller: str, len_buttons, len_axes) -> Profile:
    if controller:
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
                    return getProfile(p)
    copyProfile('default', f'Controller ({len_buttons} Buttons, {len_axes} Axes)')
    controllers[controller] = f'Controller ({len_buttons} Buttons, {len_axes} Axes)'
    with open(os.path.join(user_files_path, 'controllers'), 'w') as f:
        json.dump(controllers, f)
    showInfo("It seems your controller has an unusual configuration. You'll have to set up the controls yourself.")
    return getProfile(controllers[controller])