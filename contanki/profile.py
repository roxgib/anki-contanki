"""The Profile class stores control bindings. Currently it does not store other user
settings, but this is planned. The Profile class is serializable to JSON for the
purpose of saving."""

# For ease of testing, this file should not import any Anki
# modules or Contanki modules other than mappings and utils.

from __future__ import annotations
from collections import defaultdict

from copy import deepcopy
from re import search
import os
from os.path import join, exists
import json

from .mappings import BUTTON_NAMES
from .utils import State, get_file, int_keys

addon_path = os.path.dirname(os.path.abspath(__file__))
user_files_path = join(addon_path, "user_files")
user_profile_path = join(user_files_path, "profiles")
default_profile_path = join(addon_path, "profiles")
controllers_path = join(addon_path, "controllers")


class Profile:
    """Stores control bindings and handles calling functions for them."""

    def __init__(self, profile: dict):
        if isinstance(profile["bindings"]['all'], dict):
            self.bindings: dict[tuple[str, int, int], str] = defaultdict(str)
            for state, state_dict in profile["bindings"].items():
                for mod, mod_dict in state_dict.items():
                    for button, action in mod_dict.items():
                        if action:
                            self.bindings[(state, mod, button)] = action
        else:
            self.bindings = profile["bindings"]
        self.mods: list[int] = profile["mods"]
        self.name: str = profile["name"]
        self.size: tuple[int, int] = profile["size"]
        self.len_buttons, self.len_axes = self.size
        self.controller: str = profile["controller"]
        self.axes_bindings: list[str] = profile["axes_bindings"]
        self.bindings[("NoFocus", 0, 0)] = "Focus Main Window"

    def get(self, state: State, mod: int, button: int) -> str:
        """Returns the action for a button or axis."""
        return (
            self.bindings[(state, mod, button)]
            or state in ("question", "answer")
            and self.bindings[("review", mod, button)]
            or self.bindings[("all", mod, button)]
        )

    def set(self, state: State, mod: int, button: int, action: str) -> None:
        """Updates the binding for a button or axis."""
        self.update_binding(state, mod, button, action)

    def get_inherited_bindings(self) -> dict[str, dict[int, dict[int, str]]]:
        """Returns a dictionary of bindings with inherited actions added."""
        states = ["deckBrowser", "overview", "question", "answer", "dialog", "config"]
        inherited_bindings: dict[str, dict[int, dict[int, str]]]
        inherited_bindings = defaultdict(lambda: defaultdict(dict))
        for state in states:
            for mod in self.mods:
                for button in range(self.len_buttons):
                    inherited_bindings[state][mod][button] = (
                        self.bindings[(state, mod, button)]
                        or state in ("question", "answer")
                        and self.bindings[("all", mod, button)]
                        or self.bindings[("all", mod, button)]
                    )

        return inherited_bindings

    def remove_binding(self, state: State, mod: int, button: int) -> None:
        """Removes a binding."""
        del self.bindings[(state, mod, button)]

    def update_binding(self, state: State, mod: int, button: int, action: str) -> None:
        """Updates the binding for a button or axis."""
        if action == "mod" or self.bindings[state, mod, button] == "mod":
            raise ValueError("Use Profile.change_mod to change the modifier keys")
        self.bindings[(state, mod, button)] = action

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

        bindings: dict[str, dict[int, dict[int, str]]] = dict()
        for (state, mod, button), action in self.bindings.items():
            if state not in bindings:
                bindings[state] = dict()
            if mod not in bindings[state]:
                bindings[state][mod] = dict()
            bindings[state][mod][button] = action

        output = {
            "name": self.name,
            "size": self.size,
            "mods": self.mods,
            "bindings": bindings,
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
    vendor_id_search = search(r"Vendor: (\w{4})", id_)
    device_id_search = search(r"Product: (\w{4})", id_)
    if vendor_id_search is not None and device_id_search is not None:
        vendor_id = vendor_id_search.group(1)
        device_id = device_id_search.group(1)

        controllers_file = get_file("controllerIDs.json")
        assert controllers_file is not None
        controller_ids = json.loads(controllers_file)

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


def get_controller_list() -> list[str]:
    """Returns a list of all supported controllers."""
    return list(BUTTON_NAMES)


def get_profile_list(compatibility: str = None, defaults: bool = True) -> list[str]:
    """Returns a list of all profiles."""
    profiles = list()
    for file_name in os.listdir(user_profile_path):
        if file_name not in ["placeholder", ".DS_Store"]:
            profiles.append(file_name)

    if defaults:
        for file_name in os.listdir(default_profile_path):
            if file_name == str(compatibility) or not compatibility:
                if file_name not in ["placeholder", ".DS_Store"]:
                    profiles.append(file_name)

    return sorted(profiles)


def get_profile(name: str) -> Profile | None:
    """Load a profile from a file."""
    path = join(default_profile_path, name)
    if not exists(path):
        path = join(user_profile_path, name)
        if not exists(path):
            return None

    with open(path, "r", encoding="utf8") as file:
        profile = Profile(json.load(file, object_hook=int_keys))

    return profile


def create_profile(old_name: str, new_name: str) -> Profile:
    """Create a new Profile object using an existing Profile as a template."""
    if exists(join(user_profile_path, new_name)):
        raise FileExistsError(f"Error: Profile name '{new_name}' already in use")
    if exists(join(default_profile_path, new_name)):
        raise FileExistsError(
            f"Error: Profile name '{new_name}' conflicts with built-in profile"
        )
    return copy_profile(old_name, new_name)


def delete_profile(name: str) -> None:
    """Delete a profile from disk."""
    path = join(default_profile_path, name)
    if exists(path):
        raise ValueError("Tried to delete built-in profile")
    path = join(user_profile_path, name)
    os.remove(path)


def copy_profile(name: str, new_name: str) -> Profile:
    """Copy a profile to a new name and save to disk."""
    profile = get_profile(name)
    if profile is None:
        raise FileNotFoundError(f"Tried to copy non-existent profile '{name}'")
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
        raise FileNotFoundError(
            f"Couldn't find profile '{con}'. Loading default profile instead."
        )
    default_profiles = os.listdir(default_profile_path)
    if controller in default_profiles:
        profile_to_copy = controller
    if f"Standard Gamepad ({len_buttons} Buttons, {len_axes} Axes)" in default_profiles:
        profile_to_copy = f"Standard Gamepad ({len_buttons} Buttons, {len_axes} Axes)"
    else:
        profile_to_copy = "Standard Gamepad (16 Buttons, 4 Axes)"

    profile = copy_profile(profile_to_copy, controller)
    update_controllers(controller, profile.name)
    if controller in BUTTON_NAMES:
        profile.controller = controller
        profile.save()
    return profile


def update_controllers(controller: str, profile: str):
    """Update the controllers file with the profile."""
    with open(join(user_files_path, "controllers"), "r", encoding="utf8") as file:
        controllers = json.load(file)
    controllers[controller] = profile
    with open(join(user_files_path, "controllers"), "w", encoding="utf8") as file:
        json.dump(controllers, file)
