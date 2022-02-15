from typing import Dict, List, Optional
import os
import json

from aqt.utils import showInfo, tooltip
from aqt.qt import QMessageBox, QInputDialog

from .CONSTS import CONTROLLER_NAMES
from .actions import *

addon_path = os.path.dirname(os.path.abspath(__file__))
user_profile_path = os.path.join(addon_path, 'user_files', 'profiles')
default_profile_path = os.path.join(addon_path, 'profiles')

class Binding:
    compatibility = {
        (17,4): ['DualShock4', 'DualSense', 'XboxOne'],
        (16,4): ['DualShock3', 'XBox360', 'XboxOne']
    }

    def __init__(self, profile: dict):
        self.binding = profile['binding']
        self.mods = profile['mods']
        self.controller = profile['controller']
        self.buildActions()

    def buildActions(self):
        self.actions = dict()
        for state, a in self.bindings.items():
            self.actions[state] = dict()
            for mod, b in a:
                self.actions[state][mod] =  dict()
                for button, action in b:
                    if button in func_map:
                        self.actions[state][mod][button] = func_map[action]

    def doAction(self, state, mod, button = None, axis = None):
        try:
            if button:
                self.actions[state][mod][button]()
            elif axis:
                self.actions[state][mod][axis + 100]()
        except KeyError:
            tooltip('Error: not mapped')
        
    def updateBinding(self, state: str, mod: int, button: int = None, axis: int = None, action = "") -> None:
        if action == 'mod':
            showInfo('Error: use Binding.updateMods to change the modifier keys')
        try:
            if button:
                self.binding[state][mod][button] = action
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
        for state in self.binding:
            for mod in state:
                self.binding[state][mod][old_mod] = ""
                self.binding[state][mod][new_mod] = "mod"

    def getCompatibility(self, controller):
        if type(controller) == str:
            for key, item in self.compatibility.items():
                if controller in item:
                    return item
        elif type(controller) == tuple:
            if controller in self.compatibility:
                return self.compatibility[controller]

    def save(self) -> dict:
        return {
        'controller' : self.controller,
        'mods'       : self.mods,
        'binding'    : self.binding,
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


def getProfileList(controller: Optional[str] = None, pretty: bool = False) -> List[str]:
    profiles = list()
    for file_name in os.listdir(user_profile_path):
        if controller:
            with open(user_profile_path + file_name) as f:
                if controller in json.load(f)['controller']:
                    profiles.append(file_name)
        else:
            profiles.append(file_name)

    for file_name in os.listdir(default_profile_path):
        if file_name == controller or not controller:
            profiles.append(file_name)

    if pretty:
        return sorted([CONTROLLER_NAMES[profile] for profile in profiles])
    else:
        return sorted(profiles)


def getProfile(name: str) -> Binding:
    if os.path.exists(user_profile_path + name):
        file = user_profile_path + name
    elif os.path.exists(default_profile_path + name):
        file = default_profile_path + name
    else:
        showInfo(f"Couldn't fine profile '{name}'")
        return

    with open(file) as f:
        return Binding(json.load(f.read()))


def createProfile(controller: str = None) -> Binding:
    old, okay1 = QInputDialog().getItem(mw, 'Select a profile as the base', '', getProfileList(controller))
    name, okay2 = QInputDialog().getText(mw, 'Select a profile as the base','')
    
    if os.path.exists(user_profile_path + name):
        showInfo(f"Error: Profile name '{name}' already in use")
    elif os.path.exists(default_profile_path + name):
        showInfo(f"Error: Profile name '{name}' already in use")

    copyProfile(old, name)

    return getProfile(name)


def saveProfile(name: str, profile: Binding) -> None:
    path = os.path.join(default_profile_path, name)
    if os.exists(path):
        tooltip('Cannot overwrite built-in profiles.')
    path = os.path.join(user_profile_path, name)
    
    def save():
        with open(path, 'w') as f:
            json.dump(profile.save(), f)
    
    if os.exists(path):
        confirm = QMessageBox()
        confirm.setText("This will overwrite the existing profile.")
        confirm.setWindowTitle("Overwrite Profile")
        confirm.buttonClicked.connect(save)
        confirm.open()
    else:
        save()


def deleteProfile(name: str) -> None:
    path = os.path.join(default_profile_path, name)
    if os.exists(path):
        tooltip('Cannot delete built-in profiles.')

    path = os.path.join(user_profile_path, name)
    def delete():
        os.remove(path)
    
    if os.exists(path):
        confirm = QMessageBox()
        confirm.setText(f"This will delete the profile '{name}'.")
        confirm.setWindowTitle("Overwrite Profile")
        confirm.buttonClicked.connect(delete)
        confirm.open()


def copyProfile(name: str, new_name: str) -> None:
    if not os.exists(path := os.path.join(default_profile_path, name)):
        if not os.exists(path := os.path.join(user_profile_path, name)):
            tooltip(f"Error: profile '{name}' does not exist")
            return

    with open(path) as f:
        profile = f.read()

    with open(os.path.join(user_profile_path, new_name), 'w') as f:
       f.write(profile)