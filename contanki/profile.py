from __future__ import annotations

from copy import deepcopy
from typing import List, Optional, Tuple
from re import search
import os
import json

from aqt.utils import showInfo, tooltip
from aqt.qt import QMessageBox, QInputDialog

from .buttons import BUTTON_NAMES
from .actions import *

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
        self.move_mouse = move_mouse_build()
        self.scroll = scroll_build()
        self.buildActions()

    def buildActions(self) -> dict:
        bindings = self.getInheritedBindings()
        bindings['NoFocus'] = {0: {0:'Focus Main Window'}}
        bindings['config'] = {0: {}}
        bindings['transition'] = {0: {}}
        for i in range(len(self.mods)):
            bindings['NoFocus'][i + 1] = dict()
            bindings['transition'][i + 1] = dict()
        actions = dict()
        actions.update(button_actions)
        actions.update(get_custom_actions())
        self.actions = dict()
        self.releaseActions = dict()
        for state, a in bindings.items():
            self.actions[state] = dict()
            self.releaseActions[state] = dict()
            for mod, b in a.items():
                self.actions[state][mod] =  dict()
                self.releaseActions[state][mod] = dict()
                for button, action in b.items():
                    if action in actions:
                        self.actions[state][mod][button] = actions[action]
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
            try:
                self.actions[state][mod][button]()
            except Exception as err:
                tooltip("Error: " + str(err))

    def doReleaseAction(self, state: str, mod: int, button: int) -> None:
        if button in self.releaseActions[state][mod]:
            try:
                self.releaseActions[state][mod][button]()
            except Exception as err:
                tooltip("Error: " + str(err))

    def doAxesActions(self, state: str, mod: int, axes: List[float]) -> None:
        mx = my = sx = sy = 0
        for (axis, assignment), value in zip(self.axes_bindings.items(), axes):
            if assignment == "Unassigned":
                continue
            elif assignment == "Buttons":
                if value < -0.5:
                    if not mw.contanki.axes[axis]:
                        self.doAction(state, mod, axis * 2 + 100)
                        mw.contanki.axes[axis] = True
                    if axis + 100 in mw.contanki.icons:
                        for f in mw.contanki.icons[100 + axis*2]:
                            f[0]()
                elif value > 0.5:
                    if not mw.contanki.axes[axis]:
                        self.doAction(state, mod, axis * 2 + 1 + 100)
                        mw.contanki.axes[axis] = True
                        if axis + 100 in mw.contanki.icons:
                            for f in mw.contanki.icons[100 + axis*2 + 1]:
                                f[0]()
                else:
                    mw.contanki.axes[axis] = False
                    if axis + 100 in mw.contanki.icons:
                        for f in mw.contanki.icons[100 + axis*2]:
                            f[1]()
                        for f in mw.contanki.icons[100 + axis*2 + 1]:
                            f[1]()
            elif assignment == "Scroll Horizontal":
                sx = value
            elif assignment == "Scroll Vertical":
                sy = value
            elif assignment == "Cursor Horizontal":
                mx = value
            elif assignment == "Cursor Vertical":
                my = value
        if mx or my:
            try:
                self.move_mouse(mx, my)
            except Exception as err:
                tooltip("Error: " + str(err))
        if sx or sy:
            try:
                self.scroll(sx, sy)
            except Exception as err:
                tooltip("Error: " + str(err))

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

    def getCompatibility(self, controller):
        pass

    def save(self) -> None:
        output =  {
        'name'             : self.name,
        'size'             : self.size,
        'mods'             : self.mods,
        'bindings'         : self.bindings,
        'controller'       : self.controller,
        'axes_bindings'    : self.axes_bindings,
        }

        path = os.path.join(user_profile_path, self.name)
        with open(path, 'w') as f:
            json.dump(output, f)

    def copy(self):
        new_profile =  {
            'name'             : deepcopy(self.name),
            'size'             : deepcopy(self.size),
            'mods'             : deepcopy(self.mods),
            'bindings'         : deepcopy(self.bindings),
            'controller'       : deepcopy(self.controller),
            'axes_bindings'    : deepcopy(self.axes_bindings),
            }

        return Profile(new_profile)


def identifyController(id: str, len_buttons: int|str, len_axes: int|str) -> Tuple[str, str] | None:
    len_buttons, len_axes = int(len_buttons), int(len_axes)
    device_name = id
    vendor_id = search(r'Vendor: (\w{4})', id)
    device_id = search(r'Product: (\w{4})', id)
    if vendor_id is not None and device_id is not None:
        vendor_id = vendor_id.group(1)
        device_id = device_id.group(1)

        controller_ids = json.loads(get_file('controllerIDs.json'))

        if (vendor_id in controller_ids['vendors'] 
            and device_id in controller_ids['devices'][vendor_id]):
            device_name = controller_ids['devices'][vendor_id][device_id]
            if device_name == 'invalid':
                return None
            if device_name in BUTTON_NAMES:
                return device_name, device_name + f' ({len_buttons} buttons)'

    id = id.lower()

    # this would be a good place to use case match
    if 'dualshock' in id or 'playstation' or 'sony' in id: 
        if len_axes == 0:
            device_name = "PlayStation Controller"
        elif len_buttons == 17:
            device_name = 'DualShock 3'
        elif 'DualSense' in id:
            device_name = 'DualSense'
        elif len_buttons == 18:
            device_name = 'DualShock 4'

    if 'xbox' in id:
        if '360' in id:
            device_name = 'Xbox 360'
        elif 'one' in id:
            device_name = 'Xbox One'
        elif 'elite' in id:
            device_name = 'Xbox Series'
        elif 'series' in id:
            device_name = 'Xbox Series'
        elif 'adaptive' in id:
            device_name = 'Xbox 360'
        elif len_buttons == 16:
            device_name = 'Xbox 360'
        elif len_buttons > 16:
            device_name = 'Xbox Series'

    if 'joycon' in id or 'joy-con' in id:
        if 'left' in id:
            device_name = 'Joy-Con Left'
        if 'right' in id:
            device_name = 'Joy-Con Right'
        else:
            device_name = 'Joy-Con'

    if 'switch' in id:
        if 'pro' in id:
            device_name = 'Switch Pro'
        else:
            if 'left' in id:
                device_name = 'Joy-Con Left'
            if 'right' in id:
                device_name = 'Joy-Con Right'
            else:
                device_name = 'Joy-Con'

    if 'wii' in id:
        if 'nunchuck' in id:
            device_name = 'Wii Nunchuck'
        else:
            device_name = 'Wii Remote'

    if 'steam' in id or 'valve' in id:
        device_name = 'Steam Controller'

    return device_name, device_name + f' ({len_buttons} buttons)'


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
    if not (okay1 and old): return
    name, okay2 = QInputDialog().getText(mw, 'Create New Profile', 'Enter the new profile name:')
    if not (name and okay2): return

    if os.path.exists(os.path.join(user_profile_path, name)):
        showInfo(f"Error: Profile name '{name}' already in use")
        return
    if os.path.exists(os.path.join(default_profile_path, name)):
        showInfo(f"Error: Profile name '{name}' already in use")
        return

    return copyProfile(old, name)


def deleteProfile(name: str, confirm: bool = True) -> None:
    path = os.path.join(default_profile_path, name)
    if os.path.exists(path):
        raise ValueError('Tried to delete built-in profile')

    path = os.path.join(user_profile_path, name)

    def delete():
        os.remove(path)
    
    if os.path.exists(path):
        if confirm:
            confirm_dialog = QMessageBox()
            confirm_dialog.setText(f"This will delete the profile '{name}'.")
            confirm_dialog.setWindowTitle("Overwrite Profile")
            confirm_dialog.clickedButton.connect(delete)
            confirm_dialog.open()
        else:
            delete()


def copyProfile(name: str, new_name: str) -> None:
    if not os.path.exists(os.path.join(default_profile_path, name)):
        if not os.path.exists(os.path.join(user_profile_path, name)):
            raise FileNotFoundError

    profile = getProfile(name).copy()
    profile.name = new_name
    profile.save()

    return profile


def findProfile(controller: str, len_buttons: int, len_axes: int) -> Profile:
    with open(os.path.join(user_files_path, 'controllers'), 'r') as f:
        controllers = json.load(f)
    if controller in controllers:
        return getProfile(controllers[controller])
    default_profiles = os.listdir(default_profile_path)
    if controller in default_profiles:
        profile_to_copy = controller
    if (n := f'Standard Gamepad ({len_buttons} Buttons, {len_axes} Axes)') in default_profiles:
        profile_to_copy = n
    else:
        profile_to_copy = 'Standard Gamepad (16 Buttons, 4 Axes)'

    copyProfile(profile_to_copy, controller)
    updateControllers(controller, controller)
    profile = getProfile(controller)
    if controller in BUTTON_NAMES:
        profile.controller = controller
        profile.save()
    return profile


def updateControllers(controller, profile):
    with open(os.path.join(user_files_path, 'controllers'), 'r') as f:
        controllers = json.load(f)
    controllers[controller] = profile
    with open(os.path.join(user_files_path, 'controllers'), 'w') as f:
        json.dump(controllers, f)