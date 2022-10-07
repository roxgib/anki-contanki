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
from typing import Any
import shutil

from .utils import (
    State,
    get_file,
    int_keys,
    user_files_path,
    user_profile_path,
    default_profile_path,
)
from .controller import Controller, CONTROLLERS


class Profile:
    """Stores control bindings and handles calling functions for them."""

    def __init__(self, profile: Profile | dict):
        if isinstance(profile, Profile):
            profile = int_keys(profile.to_dict())
        bindings = profile["bindings"]
        if isinstance(list(bindings.values())[0], dict):
            self.bindings: dict[tuple[State, int], str] = defaultdict(str)
            for state, state_dict in int_keys(bindings).items():
                assert isinstance(state_dict, dict)
                assert isinstance(state, str)
                for button, action in state_dict.items():
                    if action:
                        self.bindings[(state, button)] = action
        else:
            self.bindings = bindings
        self.quick_select: dict[str, Any] = profile["quick_select"]
        self.name: str = profile["name"]
        self.size: tuple[int, int] = profile["size"]
        self.len_buttons, self.len_axes = self.size
        self.controller = profile["controller"]
        self.axes_bindings: dict[int, str] = profile["axes_bindings"]
        self.bindings[("NoFocus", 0)] = "Focus Main Window"

    @property
    def controller(self) -> Controller:
        """Returns the controller."""
        return self._controller

    @controller.setter
    def controller(self, controller: Controller | str):
        """Sets the controller."""
        if isinstance(controller, str):
            controller = Controller(controller)
        self._controller = controller

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = "".join(
            [char for char in name if char.isalnum() or char in " ()-_"]
        )

    def get(self, state: State, button: int) -> str:
        """Returns the action for a button or axis."""
        return (
            self.bindings[(state, button)]
            or state in ("question", "answer")
            and self.bindings[("review", button)]
            or self.bindings[("all", button)]
        )

    def set(self, state: State, button: int, action: str) -> None:
        """Updates the binding for a button or axis."""
        self.update_binding(state, button, action)

    def get_inherited_bindings(self) -> dict[str, dict[int, str]]:
        """Returns a dictionary of bindings with inherited actions added."""
        states = ["deckBrowser", "overview", "question", "answer", "dialog", "config"]
        inherited_bindings: dict[str, dict[int, str]]
        inherited_bindings = defaultdict(dict)
        for state in states:
            for button in range(self.len_buttons):
                inherited_bindings[state][button] = (
                    self.bindings[(state, button)]
                    or state in ("question", "answer")
                    and self.bindings[("all", button)]
                    or self.bindings[("all", button)]
                )

        return inherited_bindings

    def remove_binding(self, state: State, button: int) -> None:
        """Removes a binding."""
        del self.bindings[(state, button)]

    def update_binding(self, state: State, button: int, action: str) -> None:
        """Updates the binding for a button or axis."""
        self.bindings[(state, button)] = action

    def get_compatibility(self, controller):
        """To be implemented"""

    def to_dict(self) -> dict[str, Any]:
        """Copies the profile to a dict, with str keys for JSON compatibility."""
        bindings: dict[str, dict[str, str]] = dict()
        for (state, button), action in self.bindings.items():
            if state not in bindings:
                bindings[state] = dict()
            bindings[state][str(button)] = action

        return {
            "name": self.name,
            "size": self.size,
            "controller": self.controller.name,
            "quick_select": deepcopy(self.quick_select),
            "bindings": deepcopy(bindings),
            "axes_bindings": deepcopy(self.axes_bindings),
        }

    def __hash__(self) -> int:
        return hash(str(self.to_dict()))

    def __eq__(self, __o: object) -> bool:
        return self.to_dict() == __o.to_dict() if isinstance(__o, Profile) else False

    def save(self) -> None:
        """Saves the profile to a file."""
        path = os.path.join(user_profile_path, self.name)
        with open(path, "w", encoding="utf8") as file:
            json.dump(self.to_dict(), file)

    def copy(self):
        """Returns a deep copy of the profile."""
        return Profile(self.to_dict())


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
            if device_name in CONTROLLERS:
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


def get_profile_list(compatibility: str = None, defaults: bool = True) -> list[str]:
    """Returns a list of all profiles."""
    profiles = list()
    for file_name in os.listdir(user_profile_path):
        if file_name not in ["placeholder", ".DS_Store"] and profile_is_valid(
            file_name
        ):
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
        if profile_is_valid(profile_name := controllers[controller]):
            if (profile := get_profile(profile_name)) is not None:
                return profile
            raise FileNotFoundError(
                f"Couldn't find profile '{profile_name}'. Loading default profile instead."
            )
    if profile_is_valid(controller):
        return get_profile(controller)
    default_profiles = os.listdir(default_profile_path)
    if controller in default_profiles:
        profile_to_copy = controller
    if f"Standard Gamepad ({len_buttons} Buttons, {len_axes} Axes)" in default_profiles:
        profile_to_copy = f"Standard Gamepad ({len_buttons} Buttons, {len_axes} Axes)"
    else:
        profile_to_copy = "Standard Gamepad (16 Buttons, 4 Axes)"

    profile = copy_profile(profile_to_copy, controller)
    update_controllers(controller, profile.name)
    if controller in CONTROLLERS:
        profile.controller = Controller(controller)
        profile.save()
    return profile


def update_controllers(controller: Controller | str, profile: str):
    """Update the controllers file with the profile."""
    with open(join(user_files_path, "controllers"), "r", encoding="utf8") as file:
        controllers = json.load(file)
    controllers[str(controller)] = profile
    with open(join(user_files_path, "controllers"), "w", encoding="utf8") as file:
        json.dump(controllers, file)


def profile_is_valid(profile: Profile | dict | str) -> bool:
    """Checks that a profile is valid."""
    # try:
    if isinstance(profile, str):
        path = join(user_profile_path, profile)
        if not exists(path):
            return False
        if profile == "placeholder":
            return False
        with open(path, "r", encoding="utf8") as file:
            profile = json.load(file)
    if isinstance(profile, Profile):
        profile = profile.to_dict()
    if not (
        "name" in profile
        and "size" in profile
        and "controller" in profile
        and "quick_select" in profile
        and "bindings" in profile
        and "axes_bindings" in profile
    ):
        return False
    for state, value in profile["bindings"].items():
        if state not in State.__args__ or not isinstance(value, dict):
            return False
    Controller(profile["controller"])
    return True
    # except:
    #     return False


def convert_profiles() -> None:
    with open(join(user_files_path, "controllers"), "r", encoding="utf8") as file:
        controllers = json.load(file)
    for controller, profile in controllers.items():
        if controller in controllers:
            if profile_is_valid(profile):
                continue
            c = Controller(controller)
            shutil.copyfile(
                join(user_profile_path, profile), join(user_profile_path, profile + "_")
            )
            convert_profile(
                profile + "_", find_profile(controller, c.num_buttons, c.num_axes)
            )

    user_profiles = os.listdir(user_profile_path)
    for profile in user_profiles:
        if profile == "placeholder" or profile_is_valid(profile):
            continue
        with open(join(user_profile_path, profile), "r", encoding="utf8") as file:
            data = json.load(file)
            controller = data["controller"]
            num_buttons, num_axes = data["size"]
            shutil.copyfile(
                join(user_profile_path, profile), join(user_profile_path, profile + "_")
            )
            convert_profile(
                profile + "_", find_profile(controller, num_buttons, num_axes)
            )


def convert_profile(old_profile: str, new_profile: Profile) -> None:
    """Try to save the old profile before updating."""
    path = join(user_profile_path, old_profile)
    if not exists(path) or profile_is_valid(old_profile):
        return
    with open(path, "r", encoding="utf8") as file:
        profile = int_keys(json.load(file))
    bindings = profile["bindings"]
    bindings = {state: _bindings[0] for state, _bindings in bindings.items()}
    i = None
    for state in bindings:
        for index, action in bindings[state].items():
            if action == "mod":
                i = index
                bindings[state][index] = ""
    if i:
        bindings["all"][i] = "Toggle Quick Select"

    profile_dict = new_profile.to_dict()
    profile_dict["bindings"] = bindings
    profile_dict["name"] = (
        profile["name"][:-1] if profile["name"][-1] == "_" else profile["name"]
    )
    Profile(profile_dict).save()
    shutil.move(
        join(user_profile_path, profile["name"] + "_"),
        join(
            user_files_path,
            profile["name"][:-1] if profile["name"][-1] == "_" else profile["name"],
        ),
    )
