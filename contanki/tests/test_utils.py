# pylint: disable=missing-docstring

from ..utils import get_file, int_keys
from . import test


@test
def test_get_file():
    assert get_file("does_not_exist") is None
    file = get_file("controller.js")
    assert file is not None
    assert file.split("\n")[0] == "let polling, connected_index, indices, ready, mock_index;"
    file = get_file("Joy-Con Left")
    assert file is not None
    assert file.split("\n")[1] == '    "name": "Joy-Con Left",'


def test_int_keys():
    assert int_keys({"1": "one", "2": "two"}) == {1: "one", 2: "two"}
    assert int_keys({"1": {"2": "two"}}) == {1: {2: "two"}}
    assert int_keys({"1": {"2": {"3": "three"}}}) == {1: {2: {3: "three"}}}
    assert int_keys({"1": {"2": "two"}, 3: "three", "four": 4}) == {
        1: {2: "two"},
        3: "three",
        "four": 4,
    }
