from typing import Callable

tests = []

def test(test: Callable) -> Callable:
    """Register a test function to be run on startup."""
    tests.append(test)
    return test

def run_tests():
    """Run all registered tests."""
    from . import test_buttons, test_icons
    for test in tests:
        test()