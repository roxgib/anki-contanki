# pylint: disable=missing-docstring

from ..controller import Controller
from . import test

# pylint: disable=unused-import
from ..profile import (
    Profile,
    get_profile,
    get_profile_list,
    copy_profile,
    find_profile,
    delete_profile,
)


@test
def test_get_profile():
    profile = get_profile("Standard Gamepad (16 Buttons, 4 Axes)")
    assert profile.name == "Standard Gamepad (16 Buttons, 4 Axes)"
    assert profile.len_buttons == 16
    assert profile.len_axes == 4
    assert isinstance(profile.quick_select, dict)
    assert isinstance(profile.quick_select["actions"]["review"], list)
    assert profile.quick_select["actions"]["deckBrowser"] == [
        "Undo",
        "Redo",
        "Sync",
        "Fullscreen",
        "Quit",
    ]


@test
def test_profile_bindings():
    profile = get_profile("Standard Gamepad (16 Buttons, 4 Axes)")
    assert profile.bindings["All"][0] == "Enter"
    assert profile.bindings["All"][1] == ""
    assert profile.bindings["deckBrowser"][0] == ""
    assert profile.get("All", 0) == "Enter"
    assert profile.get("deckBrowser", 0) == "Enter"
    assert profile.get("All", 50) == ""


@test
def test_update_binding():
    profile = get_profile("Standard Gamepad (16 Buttons, 4 Axes)")
    profile.update_binding("All", 0, "Sync")
    assert profile.get("All", 0) == "Sync"
    assert profile.get("deckBrowser", 0) == "Sync"


@test
def test_save():
    profile = get_profile("Standard Gamepad (16 Buttons, 4 Axes)")
    profile.update_binding("All", 0, "Sync")
    profile.name = r"Test \/ % :"
    profile.save()
    profile = get_profile("Test")
    assert profile.get("All", 0) == "Sync"


@test
def test_delete():
    profile = get_profile("Standard Gamepad (16 Buttons, 4 Axes)")
    profile.name = "test"
    profile.save()
    profile = get_profile("test")
    delete_profile(profile)
    assert get_profile("test") is None


@test
def test_copy():
    profile = get_profile("Standard Gamepad (16 Buttons, 4 Axes)")
    profile.name = "test"
    profile.save()
    copy_profile(profile, "test2")
    assert get_profile("test2") is not None

@test
def test_profile_controller():
    profile = get_profile("Standard Gamepad (16 Buttons, 4 Axes)")
    assert profile.controller == Controller("DualShock 4")
    profile.controller = "Xbox 360"
    assert profile.controller == Controller("Xbox 360")
