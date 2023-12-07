from typing import Callable
from traceback import format_list, extract_tb
import sys
tests: dict[str, Callable] = {}


def test(_test: Callable) -> Callable:
    """Register a test function to be run on startup."""
    tests[_test.__name__] = _test
    return _test


def run_tests():
    """Run all registered tests."""
    assertions_checked = False
    assert (assertions_checked := True)
    if not assertions_checked:
        print("WARNING: assertions are not enabled, tests will not run")
        return

    from . import test_controller, test_profile, test_utils, test_icons
    passed = list()
    failed = list()
    for key, _test in tests.items():
        try:
            _test()
        except Exception as err:
            stack = format_list(extract_tb(sys.exc_info()[2]))
            stack.pop(0)
            failed.append((key, repr(err), stack))
        else:
            passed.append(key)

    print()
    print()
    print(f"Running {len(tests)} test{'s' if len(tests) > 1 else ''}...")
    if failed:
        print(f"{len(failed)} test{'s' if len(failed) > 1 else ''} failed:")
        for key, error, stack in failed:
            print()
            print(f"\t{key}: {error}")
            for line in stack:
                print(line)

        print(f"{len(passed)} test{'s' if len(passed) > 1 else ''} passed")
    else:
        print("All tests passed.")
    print()
