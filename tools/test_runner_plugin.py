#!/usr/bin/env python3
"""
Enhanced Test Runner Plugin for GoNoGo

Custom pytest plugin providing execution modes and test type filtering
for improved development workflow and debugging capabilities.

Related to: EP-00006 Test Logging and Reporting
User Story: US-00021 Enhanced test runner with execution modes

Usage:
    pytest --mode=silent --type=unit
    pytest --mode=verbose --type=integration
    pytest --mode=detailed --type=all
"""

import os
from pathlib import Path
from typing import List, Optional

import pytest


def pytest_addoption(parser):
    """Add custom command line options to pytest."""

    # Execution mode options
    parser.addoption(
        "--mode",
        action="store",
        default="standard",
        choices=["silent", "standard", "verbose", "detailed"],
        help="Test execution mode: silent (minimal output), standard (default), "
        "verbose (detailed output), detailed (maximum debugging info)",
    )

    # Test type filtering options
    parser.addoption(
        "--type",
        action="store",
        default="all",
        choices=["unit", "integration", "security", "e2e", "bdd", "all"],
        help="Test type to run: unit, integration, security, e2e, bdd, or all",
    )


def pytest_configure(config):
    """Configure pytest based on selected options."""
    mode = config.getoption("--mode")
    test_type = config.getoption("--type")

    # Configure verbosity based on mode
    if mode == "silent":
        config.option.verbose = 0
        config.option.quiet = 2
        config.option.tb = "no"
    elif mode == "verbose":
        config.option.verbose = 2
        config.option.tb = "short"
    elif mode == "detailed":
        config.option.verbose = 3
        config.option.tb = "long"
        config.option.showlocals = True
        config.option.capture = "no"  # Don't capture output for detailed mode

    # Set test paths based on type
    if test_type != "all":
        _configure_test_paths(config, test_type)


def _configure_test_paths(config, test_type: str):
    """Configure test collection paths based on test type."""
    project_root = Path(__file__).parent.parent
    test_dirs = {
        "unit": [project_root / "tests" / "unit"],
        "integration": [project_root / "tests" / "integration"],
        "security": [project_root / "tests" / "security"],
        "e2e": [project_root / "tests" / "e2e"],
        "bdd": [project_root / "tests" / "bdd"],
    }

    if test_type in test_dirs:
        # Override the args to only include the specific test directory
        test_path = test_dirs[test_type][0]
        if test_path.exists():
            config.args = [str(test_path)]
        else:
            # If the directory doesn't exist, show a warning but continue
            print(f"Warning: Test directory {test_path} does not exist")


def pytest_collection_modifyitems(config, items):
    """Modify collected test items based on configuration."""
    mode = config.getoption("--mode")
    test_type = config.getoption("--type")

    # Add mode and type information to test metadata
    for item in items:
        item.user_properties.append(("execution_mode", mode))
        item.user_properties.append(("test_type", test_type))

        # For detailed mode, add extra debugging markers
        if mode == "detailed":
            item.add_marker(pytest.mark.detailed)


def pytest_runtest_setup(item):
    """Setup for each test run."""
    mode = item.config.getoption("--mode")

    # For detailed mode, print test setup information
    if mode == "detailed":
        print(f"\n=== Setting up test: {item.name} ===")
        print(f"Test file: {item.fspath}")
        print(f"Test function: {item.function.__name__}")
        if hasattr(item.function, "__doc__") and item.function.__doc__:
            print(f"Description: {item.function.__doc__.strip()}")


def pytest_runtest_teardown(item, nextitem):
    """Teardown for each test run."""
    mode = item.config.getoption("--mode")

    # For detailed mode, print test teardown information
    if mode == "detailed":
        print(f"=== Finished test: {item.name} ===")


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """Called after the Session object has been created."""
    mode = session.config.getoption("--mode")
    test_type = session.config.getoption("--type")

    if mode != "silent":
        print(f"\nGoNoGo Test Runner - Mode: {mode}, Type: {test_type}")
        print("=" * 60)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished."""
    mode = session.config.getoption("--mode")
    test_type = session.config.getoption("--type")

    if mode != "silent":
        print("\n" + "=" * 60)
        print(f"Test run completed - Mode: {mode}, Type: {test_type}")

        # Print summary based on mode
        if mode in ["verbose", "detailed"]:
            _print_test_summary(session, exitstatus)


def _print_test_summary(session, exitstatus):
    """Print detailed test summary for verbose modes."""
    if hasattr(session, "testscollected"):
        total_tests = session.testscollected
        print(f"Total tests collected: {total_tests}")

    if hasattr(session, "testsfailed"):
        failed_tests = session.testsfailed
        if failed_tests > 0:
            print(f"Failed tests: {failed_tests}")

    exit_codes = {
        0: "All tests passed",
        1: "Some tests failed",
        2: "Test execution was interrupted",
        3: "Internal error occurred",
        4: "pytest command line usage error",
        5: "No tests collected",
    }

    status_message = exit_codes.get(exitstatus, f"Unknown exit code: {exitstatus}")
    print(f"Exit status: {status_message}")


# Plugin registration - remove this function as it's causing issues
# The plugin will be loaded via pyproject.toml addopts


# Marker definitions for use in tests
pytest_markers = [
    "detailed: marks tests for detailed debugging mode",
    "test_type: categorizes tests by type (unit, integration, etc.)",
]


if __name__ == "__main__":
    print("GoNoGo Test Runner Plugin")
    print("This is a pytest plugin, run with: pytest --mode=<mode> --type=<type>")
    print("\nAvailable modes: silent, standard, verbose, detailed")
    print("Available types: unit, integration, security, e2e, bdd, all")
