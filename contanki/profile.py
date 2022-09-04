from __future__ import annotations

from copy import deepcopy
from typing import Optional
from re import search
import os
from os.path import join, exists
import json

from aqt import mw
from aqt.utils import showInfo, tooltip
from aqt.qt import QMessageBox, QInputDialog

from .mappings import BUTTON_NAMES
from .actions import (
    button_actions,
    release_actions,
)
from .funcs import get_file, int_keys, move_mouse_build, scroll_build, get_custom_actions

addon_path = os.path.dirname(os.path.abspath(__file__))
user_files_path = join(addon_path, "user_files")
user_profile_path = join(user_files_path, "profiles")
default_profile_path = join(addon_path, "profiles")
controllers_path = join(addon_path, "controllers")


class Profile:
    """Stores control bindings and handles calling functions for them."""

    def __init__(self, profile: dict):
        print(profile)
        self.bindings = profile["bindings"]
        self.mods: list[int] = profile["mods"]
        self.name = profile["name"]
        self.len_buttons, self.len_axes = self.size = profile["size"]
        self.controller = profile["controller"]
        self.axes_bindings = profile["axes_bindings"]
        self.move_mouse = move_mouse_build()
        self.scroll = scroll_build()
        self.build_actions()

    def build_actions(self) -> dict:
        """Connects action names with functions."""
        bindings = self.get_inherited_bindings()
        bindings["NoFocus"] = {0: {0: "Focus Main Window"}}
        bindings["config"] = {0: {}}
        bindings["transition"] = {0: {}}
        for i in range(len(self.mods)):
            bindings["NoFocus"][i + 1] = dict()
            bindings["transition"][i + 1] = dict()
        actions = dict()
        actions.update(button_actions)
        actions.update(get_custom_actions())
        self.actions = dict()
        self.release_actions = dict()
        for state, state_dict in bindings.items():
            self.actions[state] = dict()
            self.release_actions[state] = dict()
            for mod, mod_dict in state_dict.items():
                self.actions[state][mod] = dict()
                self.release_actions[state][mod] = dict()
                for button, action in mod_dict.items():
                    if action in actions:
                        self.actions[state][mod][button] = actions[action]
                    if action in release_actions:
                        self.release_actions[state][mod][button] = release_actions[
                            action
                        ]

        return self.actions

    def get_inherited_bindings(self) -> dict:
        """Returns a dictionary of bindings with inherited actions added."""
        bindings = deepcopy(self.bindings)
        for state, sdict in bindings.items():
            for mod, mdict in sdict.items():
                if state == "question" or state == "answer":
                    for button, action in bindings["review"][mod].items():
                        if button not in mdict or mdict[button] == "":
                            mdict[button] = action
                if state != "all":
                    for button, action in bindings["all"][mod].items():
                        if button not in mdict or mdict[button] == "":
                            mdict[button] = action

        return bindings

    def do_action(self, state: str, mod: int, button: int) -> None:
        """Calls the appropriate function on button press."""
        if button in self.actions[state][mod]:
            try:
                self.actions[state][mod][button]()
            except Exception as err:  # pylint: disable=broad-except
                tooltip("Error: " + str(err))

    def do_release_action(self, state: str, mod: int, button: int) -> None:
        """Calls the appropriate function on button release."""
        if button in self.release_actions[state][mod]:
            try:
                self.release_actions[state][mod][button]()
            except Exception as err:  # pylint: disable=broad-except
                tooltip("Error: " + str(err))

    def do_axes_actions(self, state: str, mod: int, axes: list[float]) -> None:
        """Handles actions for axis movement."""
        mouse_x = mouse_y = scroll_x = scroll_y = 0
        for (axis, assignment), value in zip(self.axes_bindings.items(), axes):
            if assignment == "Unassigned":
                continue
            elif assignment == "Buttons":
                if abs(value) > 0.5:
                    if not mw.contanki.axes[axis]:
                        self.do_action(state, mod, axis * 2 + (value > 0) + 100)
                        mw.contanki.axes[axis] = True
                else:
                    mw.contanki.axes[axis] = False
            elif assignment == "Scroll Horizontal":
                scroll_x = value
            elif assignment == "Scroll Vertical":
                scroll_y = value
            elif assignment == "Cursor Horizontal":
                mouse_x = value
            elif assignment == "Cursor Vertical":
                mouse_y = value
        if mouse_x or mouse_y:
            try:
                self.move_mouse(mouse_x, mouse_y)
            except Exception as err: # pylint: disable=broad-except
                tooltip("Error: " + str(err))
        if scroll_x or scroll_y:
            try:
                self.scroll(scroll_x, scroll_y)
            except Exception as err: # pylint: disable=broad-except
                tooltip("Error: " + str(err))

    def update_binding(
        self, state: str, mod: int, button: int, action: str, build_actions: bool = True
    ) -> None:
        """Updates the binding for a button or axis."""
        if mod not in self.bindings[state]:
            self.bindings[state][mod] = dict()
        if button not in self.bindings[state][mod]:
            self.bindings[state][mod][button] = ""
        if action == "mod" or self.bindings[state][mod][button] == "mod":
            showInfo("Error: use Binding.updateMods to change the modifier keys")
        self.bindings[state][mod][button] = action
        if build_actions:
            self.build_actions()

    def change_mod(self, old_mod: int, new_mod: int) -> None:
        """Changes a modifier key."""
        if old_mod in self.mods:
            self.mods[self.mods.index(old_mod)] = new_mod

    def get_compatibility(self, controller):
        """To be implemented"""

    def save(self) -> None:
        """Saves the profile to a file."""
        self.name = "".join(
            [char for char in self.name if char.isalnum() or char in " ()-_"]
        )
        output = {
            "name": self.name,
            "size": self.size,
            "mods": self.mods,
            "bindings": self.bindings,
            "controller": self.controller,
            "axes_bindings": self.axes_bindings,
        }

        path = os.path.join(user_profile_path, self.name)
        with open(path, "w", encoding="utf8") as file:
            json.dump(output, file)

    def copy(self):
        """Returns a deep copy of the profile."""
        new_profile = {
            "name": deepcopy(self.name),
            "size": deepcopy(self.size),
            "mods": deepcopy(self.mods),
            "bindings": deepcopy(self.bindings),
            "controller": deepcopy(self.controller),
            "axes_bindings": deepcopy(self.axes_bindings),
        }

        return Profile(new_profile)


# FIXME: this is a mess
def identify_controller(
    id_: str,
    len_buttons: int | str,
    len_axes: int | str,
) -> tuple[str, str] | None:
    """Identifies a controller based on the ID name and number of buttons and axes."""
    len_buttons, len_axes = int(len_buttons), int(len_axes)
    device_name = id_
    vendor_id = search(r"Vendor: (\w{4})", id_)
    device_id = search(r"Product: (\w{4})", id_)
    if vendor_id is not None and device_id is not None:
        vendor_id = vendor_id.group(1)
        device_id = device_id.group(1)

        controller_ids = json.loads(get_file("controllerIDs.json"))

        if (
            vendor_id in controller_ids["vendors"]
            and device_id in controller_ids["devices"][vendor_id]
        ):
            device_name = controller_ids["devices"][vendor_id][device_id]
            if device_name == "invalid":
                return None
            if device_name in BUTTON_NAMES:
                return device_name, device_name + f" ({len_buttons} buttons)"

    id_ = id_.lower()

    # this would be a good place to use case match
    if "dualshock" in id_ or "playstation" or "sony" in id_:
        if len_axes == 0:
            device_name = "PlayStation Controller"
        elif len_buttons == 17:
            device_name = "DualShock 3"
        elif "DualSense" in id_:
            device_name = "DualSense"
        elif len_buttons == 18:
            device_name = "DualShock 4"
    elif "xbox" in id_:
        if "360" in id_:
            device_name = "Xbox 360"
        elif "one" in id_:
            device_name = "Xbox One"
        elif "elite" in id_:
            device_name = "Xbox Series"
        elif "series" in id_:
            device_name = "Xbox Series"
        elif "adaptive" in id_:
            device_name = "Xbox 360"
        elif len_buttons == 16:
            device_name = "Xbox 360"
        elif len_buttons > 16:
            device_name = "Xbox Series"
    elif "joycon" in id_ or "joy-con" in id_ or "switch" in id_:
        if "pro" in id_:
            device_name = "Switch Pro"
        if "left" in id_:
            device_name = "Joy-Con Left"
        if "right" in id_:
            device_name = "Joy-Con Right"
        else:
            device_name = "Joy-Con"
    elif "wii" in id_:
        if "nunchuck" in id_:
            device_name = "Wii Nunchuck"
        else:
            device_name = "Wii Remote"
    elif "steam" in id_ or "valve" in id_:
        device_name = "Steam Controller"

    if "8bitdo" in id_:
        if "zero" in id_:
            device_name = "8Bitdo Zero"
        else:
            device_name = "8Bitdo Lite"

    return device_name, device_name + f" ({len_buttons} buttons)"


def get_controller_list():
    """Returns a list of all supported controllers."""
    return list(BUTTON_NAMES.keys())


def get_profile_list(
    compatibility: Optional[str] = None, include_defaults: bool = True
) -> list[str]:
    """Returns a list of all profiles."""
    profiles = list()
    for file_name in os.listdir(user_profile_path):
        if file_name not in ["placeholder", ".DS_Store"]:
            profiles.append(file_name)

    if include_defaults:
        for file_name in os.listdir(default_profile_path):
            if file_name == str(compatibility) or not compatibility:
                if file_name not in ["placeholder", ".DS_Store"]:
                    profiles.append(file_name)

    return sorted(profiles)


def get_profile(name: str) -> Profile:
    """Load a profile from a file."""
    path = join(default_profile_path, name)
    if not exists(path):
        path = join(user_profile_path, name)
        if not exists(path):
            return

    with open(path, "r", encoding="utf8") as file:
        profile = Profile(json.load(file, object_hook=int_keys))

    return profile


def create_profile(controller: str = None) -> Profile:
    """Create a new Profile object."""
    old, okay1 = QInputDialog().getItem(
        mw,
        "Create New Profile",
        "Select an existing profile to copy:",
        get_profile_list(),
        editable=False,
    )
    if not (okay1 and old):
        return
    name, okay2 = QInputDialog().getText(
        mw, "Create New Profile", "Enter the new profile name:"
    )
    if not (name and okay2):
        return

    if exists(join(user_profile_path, name)):
        showInfo(f"Error: Profile name '{name}' already in use")
        return
    if exists(join(default_profile_path, name)):
        showInfo(f"Error: Profile name '{name}' already in use")
        return

    return copy_profile(old, name)


def delete_profile(name: str, confirm: bool = True) -> None:
    """Delete a profile from disk."""
    path = join(default_profile_path, name)
    if exists(path):
        raise ValueError("Tried to delete built-in profile")

    path = join(user_profile_path, name)

    def delete():
        os.remove(path)

    if exists(path):
        if confirm:
            confirm_dialog = QMessageBox()
            confirm_dialog.setText(f"This will delete the profile '{name}'.")
            confirm_dialog.setWindowTitle("Overwrite Profile")
            confirm_dialog.clickedButton.connect(delete)
            confirm_dialog.open()
        else:
            delete()


def copy_profile(name: str, new_name: str) -> None:
    """Copy a profile to a new name and save to disk."""
    if not (
        exists(join(default_profile_path, name))
        or exists(join(user_profile_path, name))
    ):
        raise FileNotFoundError("Tried to copy non-existent profile")

    profile = get_profile(name).copy()
    profile.name = new_name
    profile.save()

    return profile


def find_profile(controller: str, len_buttons: int, len_axes: int) -> Profile:
    """Find a profile that matches the controller."""
    with open(join(user_files_path, "controllers"), "r", encoding="utf8") as file:
        controllers = json.load(file)
    if controller in controllers:
        if (profile := get_profile(con := controllers[controller])) is not None:
            return profile
        showInfo(
            f"Couldn't find profile '{con}'. Loading default profile instead."
        )
    default_profiles = os.listdir(default_profile_path)
    if controller in default_profiles:
        profile_to_copy = controller
    if (
        profile := f"Standard Gamepad ({len_buttons} Buttons, {len_axes} Axes)"
    ) in default_profiles:
        profile_to_copy = profile
    else:
        profile_to_copy = "Standard Gamepad (16 Buttons, 4 Axes)"

    copy_profile(profile_to_copy, controller)
    update_controllers(controller, controller)
    profile = get_profile(controller)
    if controller in BUTTON_NAMES:
        profile.controller = controller
        profile.save()
    return profile


def update_controllers(controller, profile):
    """Update the controllers file with the profile."""
    with open(join(user_files_path, "controllers"), "r", encoding="utf8") as file:
        controllers = json.load(file)
    controllers[controller] = profile
    with open(join(user_files_path, "controllers"), "w", encoding="utf8") as file:
        json.dump(controllers, file)
