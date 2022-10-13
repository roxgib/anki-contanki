# pylint: disable=missing-docstring

from os.path import join

from ..controller import Controller
from ..utils import user_files_path
from . import test

# pylint: disable=unused-import
from ..profile import (
    Profile,
    get_profile,
    get_profile_list,
    copy_profile,
    find_profile,
    profile_is_valid,
    rename_profile,
    delete_profile,
    update_controllers,
)

@test
def test_get_profile():
    profile = get_profile("Standard Gamepad (16 Buttons 4 Axes)")
    assert profile.name == "Standard Gamepad (16 Buttons 4 Axes)"
    assert profile.len_buttons == 16
    assert profile.len_axes == 4
    assert isinstance(profile.quick_select, dict)
    assert isinstance(profile.quick_select["actions"]["review"], list)
    assert profile.quick_select["actions"]["review"] == [
        "Suspend Card",
        "Suspend Note",
        "Bury Card",
        "Bury Note",
        "Card Info"
    ]

@test
def test_delete_profile():
    profile = get_profile("Standard Gamepad (16 Buttons 4 Axes)")
    profile.name = "test"
    profile.save()
    profile = get_profile("test")
    delete_profile("test")
    assert get_profile("test") is None
    profile.save()
    delete_profile(profile)
    assert get_profile("test") is None

@test
def test_profile_bindings():
    profile = get_profile("Standard Gamepad (16 Buttons 4 Axes)")
    assert profile.get("all", 0) == "Enter"
    assert profile.get("deckBrowser", 0) == "Select"
    assert profile.get("all", 50) == ""


@test
def test_update_binding():
    profile = get_profile("Standard Gamepad (16 Buttons 4 Axes)")
    profile.update_binding("all", 0, "Sync")
    profile.update_binding("deckBrowser", 0, "")
    assert profile.get("all", 0) == "Sync"
    assert profile.get("deckBrowser", 0) == "Sync"


@test
def test_save():
    profile = get_profile("Standard Gamepad (16 Buttons 4 Axes)")
    profile.update_binding("All", 0, "Sync")
    profile.name = r"Test \/ % :"
    profile.save()
    profile = get_profile("Test")
    assert profile.get("All", 0) == "Sync"
    delete_profile("Test")

@test
def test_copy_profile():
    profile = get_profile("Standard Gamepad (16 Buttons 4 Axes)")
    profile.name = "test"
    profile.save()
    copy_profile(profile, "test2")
    assert get_profile("test2") is not None
    delete_profile("test2")


@test
def test_profile_controller():
    profile = get_profile("Standard Gamepad (16 Buttons 4 Axes)")
    assert profile.controller == Controller("DualShock 4")
    profile.controller = "Xbox 360"
    assert isinstance(profile.controller, Controller)
    assert profile.controller == Controller("Xbox 360")


@test
def test_rename_profile():
    profile = get_profile("Standard Gamepad (16 Buttons 4 Axes)")
    profile.name = "test"
    profile.save()
    rename_profile("test", "test2")
    assert get_profile("test") is None
    profile = get_profile("test2")
    assert profile is not None
    assert profile.name == "test2"
    delete_profile(profile)


@test
def test_find_profile():
    with open(join(user_files_path, "controllers"), "r", encoding="utf8") as file:
        controllers = file.read()
    profile = find_profile("DualShock 4", 18, 4)
    assert profile.name == "DualShock 4"
    profile.name = "test"
    profile.save()
    update_controllers("DualShock 4", "test")
    profile = find_profile("DualShock 4", 18, 4)
    assert profile.name == "test"
    delete_profile("test")
    try:
        profile = find_profile("DualShock 4", 18, 4)
        assert False # Should raise Exception
    except FileNotFoundError:
        profile = find_profile("DualShock 4", 18, 4) # Works the second time
    assert profile.name == "DualShock 4"
    delete_profile("DualShock 4")
    with open(join(user_files_path, "controllers"), "w", encoding="utf8") as file:
        file.write(controllers)

@test
def test_profile_is_valid():
    profile = get_profile("Standard Gamepad (16 Buttons 4 Axes)")
    profile.name = "test"
    profile.save()
    assert profile_is_valid("test")
    assert not profile_is_valid("test2")
    delete_profile("test")
