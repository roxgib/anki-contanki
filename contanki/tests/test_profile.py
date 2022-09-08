# pylint: disable=missing-docstring
from aqt import mw

from contanki.funcs import on_enter
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
    profile = get_profile('Standard Gamepad (16 Buttons, 4 Axes)')
    assert profile.name == 'Standard Gamepad (16 Buttons, 4 Axes)'
    assert profile.len_buttons == 16
    assert profile.len_axes == 4
    assert profile.mods == [6, 7]


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

@test
def test_save():
    profile = get_profile('Standard Gamepad (16 Buttons, 4 Axes)')
    profile.update_binding("All", 0, 0, "Sync", False)
    profile.name = r"Test \/ % :"
    profile.save()
    profile = get_profile('Test')
    assert profile.bindings["All"][0][0] == "Sync"

@test
def test_delete():
    profile = get_profile('Standard Gamepad (16 Buttons, 4 Axes)')
    profile.name = "test"
    profile.save()
    profile = get_profile('test')
    delete_profile(profile)
    assert get_profile('test') is None

@test
def test_copy():
    profile = get_profile('Standard Gamepad (16 Buttons, 4 Axes)')
    profile.name = "test"
    profile.save()
    copy_profile(profile, "test2")
    assert get_profile('test2') is not None
