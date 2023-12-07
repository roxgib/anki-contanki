"""The Profile class stores control bindings. Currently it does not store other user
settings, but this is planned. The Profile class is serializable to JSON for the
purpose of saving."""

# For ease of testing, this file should not import any Anki
# modules or Contanki modules other than mappings and utils.

from __future__ import annotations
from collections import defaultdict

from copy import deepcopy
import os
from os.path import join, exists
import json
from typing import Any
import shutil

from .utils import (
    State,
    dbg,
    int_keys,
    user_files_path,
    user_profile_path,
    default_profile_path,
    slugify,
)
from .controller import Controller, get_updated_controller_list


class Profile:
    """Stores control bindings and handles calling functions for them."""

    states: list[State] = [
        "deckBrowser",
        "overview",
        "review",
        "question",
        "answer",
        "dialog",
        "config",
    ]

    def __init__(self, profile: Profile | dict):
        if isinstance(profile, Profile):
            profile = int_keys(profile.to_dict())
        bindings = profile["bindings"]
        if isinstance(list(bindings.values())[0], dict):
            self.bindings: dict[tuple[State, int], str] = defaultdict(str)
            for state, state_dict in int_keys(bindings).items():
                for button, action in state_dict.items():
                    if action and "inherit" not in action.lower():
                        self.bindings[(state, button)] = action
        else:
            self.bindings = bindings
        self.quick_select: dict[str, Any] = profile["quick_select"]
        self.name: str = profile["name"]
        self.size: tuple[int, int] = profile["size"]
        self.len_buttons, self.len_axes = self.size
        self.controller = profile["controller"]
        self.axes_bindings: dict[int, str] = defaultdict(str, profile["axes_bindings"])
        self.bindings[("NoFocus", 0)] = "Focus Main Window"
        self.invert_axis: dict[int, bool] = defaultdict(
            bool,
            profile["invert_axis"]
            if "invert_axis" in profile
            else {i: False for i in self.axes_bindings},
        )

    def __repr__(self) -> str:
        return f"Profile({self.name})"

    def __str__(self) -> str:
        return self.name

    @property
    def controller(self) -> Controller:
        """Returns the controller."""
        return self._controller

    @controller.setter
    def controller(self, controller: Controller | str):
        """Sets the controller."""
        if isinstance(controller, str):
            if controller in get_updated_controller_list():
                controller = Controller(controller)
            else:
                dbg(f"Controller {controller} not found.")
                return
        self._controller = controller

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
        """Returns a dictionary of bindings with inherited actions and duplicated buttons added."""
        bindings: dict[str, dict[int, str]] = defaultdict(dict)
        for state in self.states:
            for button in range(self.len_buttons):
                bindings[state][button] = self.bindings[("all", button)]
                if state in ("question", "answer"):
                    bindings[state][button] = self.bindings[("review", button)]
                if self.bindings[(state, button)]:
                    bindings[state][button] = self.bindings[(state, button)]
        return bindings

    def remove_binding(self, state: State, button: int) -> None:
        """Removes a binding."""
        del self.bindings[(state, button)]

    def update_binding(self, state: State, button: int, action: str) -> None:
        """Updates the binding for a button or axis."""
        if state not in getattr(State, "__args__"):
            raise ValueError(f"State {state} not valid.")
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
            "invert_axis": deepcopy(self.invert_axis),
        }

    def to_json(self) -> str:
        """Returns the profile as a JSON string."""
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str) -> Profile | None:
        """Loads the profile from a JSON string."""
        try:
            profile = json.loads(json_str, object_hook=int_keys)
        except json.JSONDecodeError as err:
            dbg(f"Profile '{json_str}' is not valid JSON")
            dbg(err)
            return None
        if not profile_is_valid(profile):
            dbg(f"Profile '{profile}' is not valid")
            return None
        return Profile(profile)

    def __hash__(self) -> int:
        return hash(str(self.to_dict()))

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Profile) and self.__hash__() == __o.__hash__()

    def save(self) -> None:
        """Saves the profile to a file."""
        path = os.path.join(user_profile_path, slugify(self.name))
        with open(dbg(path), "w", encoding="utf8") as file:
            json.dump(self.to_dict(), file)

    def copy(self):
        """Returns a deep copy of the profile."""
        return Profile(self.to_dict())


def get_profile_list(
    compatibility: str | None = None, defaults: bool = True
) -> list[str]:
    """Returns a list of all profiles."""
    files = os.listdir(user_profile_path)
    if defaults:
        files += os.listdir(default_profile_path)
    profiles = [get_profile(file) for file in files if profile_is_valid(file)]
    return sorted(profile.name for profile in profiles if profile is not None)


def _load_profile(name: str) -> str | None:
    """Loads a profile str from a file."""
    paths = (
        join(user_profile_path, slugify(name)),
        join(default_profile_path, slugify(name)),
        join(user_profile_path, name),
        join(default_profile_path, name),
    )
    for path in paths:
        if exists(path):
            with open(path, "r", encoding="utf8") as file:
                return file.read()
    return None


def get_profile(name: str) -> Profile | None:
    """Load a profile from a file."""
    if profile_is_valid(name):
        raw_profile = _load_profile(name)
        if raw_profile is None:
            return None
        return Profile(json.loads(raw_profile, object_hook=int_keys))
    return None


def create_profile(old_name: str, new_name: str) -> Profile:
    """Create a new Profile object using an existing Profile as a template."""
    if exists(join(user_profile_path, new_name)) or new_name in get_profile_list():
        raise FileExistsError(f"Error: Profile name '{new_name}' already in use")

    path = join(default_profile_path, new_name)
    if exists(path) or new_name in get_profile_list(defaults=True):
        raise FileExistsError(
            f"Error: Profile name '{new_name}' conflicts with built-in profile"
        )
    return copy_profile(old_name, new_name)


def delete_profile(profile: str | Profile) -> None:
    """Delete a profile from disk."""
    name = profile.name if isinstance(profile, Profile) else profile
    name = slugify(name)
    path = join(user_profile_path, name)
    if exists(path):
        dbg(f"Deleting profile {name} from {path}")
        os.remove(path)
    else:
        dbg(f"Tried to delete profile {name}, but not found at {path}")
        path = join(default_profile_path, name)
        if exists(path):
            dbg(f"Tried to delete built-in profile {name} from {path}")
            raise ValueError("Tried to delete built-in profile")


def copy_profile(profile: str | Profile, new_name: str) -> Profile:
    """Copy a profile to a new name and save to disk."""
    new_profile = get_profile(profile) if isinstance(profile, str) else profile.copy()
    if new_profile is None:
        raise FileNotFoundError(f"Tried to copy non-existent profile '{profile}'")
    dbg(f"Copying profile {new_profile.name} to {new_name}")
    new_profile.name = new_name
    new_profile.save()
    return new_profile


def rename_profile(profile: str | Profile, new_name: str) -> None:
    """Rename a profile saved to disk."""
    if isinstance(profile, str):
        name = profile
        _profile = get_profile(profile)
        if _profile is None:
            raise FileNotFoundError(f"Tried to rename non-existent profile '{name}'")
        else:
            profile = _profile  # Keep mypy happy
    name = profile.name
    profile.name = new_name
    profile.save()
    delete_profile(name)


def find_profile(controller: str, buttons: int, axes: int) -> str:
    """Find a profile that matches the controller."""
    dbg(f"Finding profile for {controller} with {buttons} buttons and {axes} axes")

    # Check if a profile is already assigned to this controller
    profile = get_assigned_profile(controller)
    if profile is not None:
        dbg(f"Found profile {profile.name} for {controller}")
        return str(profile)

    # Check if a profile named after the controller exists
    user_profiles = get_profile_list(defaults=False)
    if controller in user_profiles:
        dbg(f"Found profile {controller} for {controller}")
        update_assigned_profiles(controller, controller)
        return controller

    # No profile found, create a default profile for the controller
    default_profiles = get_profile_list(defaults=True)
    if controller in default_profiles:
        profile_to_copy = controller
    elif f"Standard Gamepad ({buttons} Buttons {axes} Axes)" in default_profiles:
        profile_to_copy = f"Standard Gamepad ({buttons} Buttons {axes} Axes)"
    else:
        profile_to_copy = "Standard Gamepad (18 Buttons 4 Axes)"
    profile = copy_profile(profile_to_copy, controller)
    update_assigned_profiles(controller, profile.name)

    if controller in get_updated_controller_list():
        profile.controller = Controller(controller)
        profile.save()
    return profile.name


def update_assigned_profiles(controller: Controller | str, profile: Profile | str):
    """Update the controllers file with the profile."""
    profile = str(profile)
    controller = str(controller)
    with open(join(user_files_path, "controllers"), "r", encoding="utf8") as file:
        controllers = json.load(file)
    if profile:
        controllers[controller] = profile
    else:
        del controllers[controller]
    with open(join(user_files_path, "controllers"), "w", encoding="utf8") as file:
        json.dump(controllers, file)


def get_assigned_profile(controller: Controller | str) -> Profile | None:
    """Get a list of profiles assigned to controllers."""
    controller = str(controller)
    assigned_profiles = get_assigned_profiles()
    if controller in assigned_profiles:
        return get_profile(assigned_profiles[controller])
    return None


def get_assigned_profiles() -> dict[str, str]:
    """Get a list of profiles assigned to controllers."""
    with open(join(user_files_path, "controllers"), "r", encoding="utf8") as file:
        return json.load(file)


def profile_is_valid(profile: Profile | dict | str | None) -> bool:
    """Checks that a profile is valid."""
    if isinstance(profile, str):
        if profile is None:
            return False
        if profile == "placeholder":
            return False
        try:
            profile = _load_profile(profile)
        except (UnicodeDecodeError, UnicodeError) as err:
            dbg(f"Error loading '{profile}': {err}")
            return False
        if profile is None:
            dbg(f"Profile '{profile}' not found")
            return False
        try:
            profile = json.loads(profile, object_hook=int_keys)
        except json.JSONDecodeError:
            dbg(f"Profile '{profile}' is not valid JSON")
            return False
    elif isinstance(profile, Profile):
        try:
            profile = profile.to_dict()
        except (AttributeError, TypeError, ValueError) as err:
            dbg(err)
            return False

    if not isinstance(profile, dict):
        dbg(dbg(f"Profile '{profile}' not of type dict"))
        return False

    profile = int_keys(profile)

    for key in [
        "name",
        "size",
        "controller",
        "quick_select",
        "bindings",
        "axes_bindings",
    ]:
        if key not in profile:
            dbg(f"Profile '{profile['name']}' is missing required key {key}")
            return False
    for state, value in profile["bindings"].items():
        if state not in getattr(State, "__args__"):
            dbg(f"Profile '{profile['name']}' has invalid state '{state}'")
            return False
        if not isinstance(value, dict):
            dbg(f"Profile '{profile['name']}' has invalid value {value} for '{state}'")
            return False
    try:
        Controller(profile["controller"])
    except ValueError as err:
        dbg(err)
        return False
    try:
        profile = Profile(profile)
    except Exception as err:
        dbg(f"Profile '{profile}' returned error: {err}")
        return False
    return True
