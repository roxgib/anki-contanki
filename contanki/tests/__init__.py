from typing import Callable

tests = []

def test(_test: Callable) -> Callable:
    """Register a test function to be run on startup."""
    tests.append(_test)
    return _test

def run_tests():
    """Run all registered tests."""
    from . import test_controller, test_profile, test_utils, test_icons
    for _test in tests:
        _test()
