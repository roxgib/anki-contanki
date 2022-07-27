from aqt import mw

from contanki.funcs import on_enter
from . import test
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
    profile = get_profile('Standard Gamepad (16 Buttons, 4 Axes)')
    assert profile.name == 'Standard Gamepad (16 Buttons, 4 Axes)'
    assert profile.buttons == 16
    assert profile.axes == 4
    assert profile.modes == [6, 7]

@test
def test_profile_bindings():
    profile = get_profile('Standard Gamepad (16 Buttons, 4 Axes)')
    assert profile.bindings["All"][0] == "Enter"
    assert profile.bindings["All"][1] == ""
    assert profile.bindings["deckBrowser"][0] == ""

@test
def test_profile_actions():
    profile = get_profile('Standard Gamepad (16 Buttons, 4 Axes)')
    assert profile.actions["All"][0] is on_enter
    assert profile.bindings["deckBrowser"][0] is on_enter

@test
def test_update_binding():
    profile = get_profile('Standard Gamepad (16 Buttons, 4 Axes)')
    profile.update_binding("All", 0, 0, "Sync", False)
    assert profile.bindings["All"][0] == "Sync"
    assert profile.actions["All"][0] is on_enter
    profile.update_binding("All", 0, 1, "Sync", True)
    assert profile.actions["All"][0] is mw.onSync
    assert profile.actions["All"][1] is mw.onSync

