#!/usr/bin/env python3
"""
RTM Test Runner

Comprehensive test runner for RTM automation system.
Runs unit tests, integration tests, and generates coverage reports.

Related Issue: US-00017 - Comprehensive testing and extensibility framework
Epic: EP-00005 - RTM Automation

Usage:
    python tests/rtm_test_runner.py --all
    python tests/rtm_test_runner.py --unit
    python tests/rtm_test_runner.py --integration
    python tests/rtm_test_runner.py --coverage
"""

import argparse
import subprocess
import sys
from pathlib import Path


class RTMTestRunner:
    """RTM test runner with comprehensive test execution."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.src_dir = self.project_root / "src"

    def run_unit_tests(self) -> int:
        """Run unit tests for RTM automation."""
        print("🧪 Running RTM Unit Tests...")

        unit_test_files = ["tests/unit/shared/utils/test_rtm_link_generator.py"]

        return self._run_pytest(unit_test_files, "Unit Tests")

    def run_integration_tests(self) -> int:
        """Run integration tests for RTM automation."""
        print("🔧 Running RTM Integration Tests...")

        integration_test_files = [
            "tests/integration/rtm/test_rtm_end_to_end.py",
            "tests/integration/rtm/test_plugin_system.py",
        ]

        return self._run_pytest(integration_test_files, "Integration Tests")

    def run_all_tests(self) -> int:
        """Run all RTM tests."""
        print("🚀 Running All RTM Tests...")

        all_test_files = [
            "tests/unit/shared/utils/test_rtm_link_generator.py",
            "tests/integration/rtm/test_rtm_end_to_end.py",
            "tests/integration/rtm/test_plugin_system.py",
        ]

        return self._run_pytest(all_test_files, "All RTM Tests")

    def run_with_coverage(self) -> int:
        """Run tests with coverage reporting."""
        print("📊 Running RTM Tests with Coverage...")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit/shared/utils/test_rtm_link_generator.py",
            "tests/integration/rtm/",
            "--cov=src/shared/utils/rtm_link_generator",
            "--cov=src/shared/utils/rtm_plugins",
            "--cov-report=html:reports/coverage/rtm",
            "--cov-report=term-missing",
            "--cov-report=xml:reports/coverage/rtm-coverage.xml",
            "-v",
        ]

        # Create reports directory
        reports_dir = self.project_root / "reports" / "coverage"
        reports_dir.mkdir(parents=True, exist_ok=True)

        return self._run_command(cmd, "Coverage Tests")

    def run_performance_tests(self) -> int:
        """Run performance tests."""
        print("⚡ Running RTM Performance Tests...")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/rtm/test_rtm_end_to_end.py::TestRTMPerformance",
            "-v",
            "--durations=10",
        ]

        return self._run_command(cmd, "Performance Tests")

    def run_plugin_tests(self) -> int:
        """Run plugin system tests specifically."""
        print("🔌 Running RTM Plugin Tests...")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/rtm/test_plugin_system.py",
            "-v",
        ]

        return self._run_command(cmd, "Plugin Tests")

    def validate_test_environment(self) -> bool:
        """Validate test environment setup."""
        print("🔍 Validating Test Environment...")

        # Check required files exist
        required_files = [
            "src/shared/utils/rtm_link_generator.py",
            "src/shared/utils/rtm_plugins/__init__.py",
            "config/rtm-automation.yml",
            "tools/rtm-links-simple.py",
        ]

        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        if missing_files:
            print(f"❌ Missing required files: {missing_files}")
            return False

        # Check Python path can import RTM modules
        try:
            sys.path.insert(0, str(self.src_dir))
            from shared.utils.rtm_link_generator import RTMLinkGenerator
            from shared.utils.rtm_plugins import PluginManager

            # Mark imports as used - testing import capability
            _ = (RTMLinkGenerator, PluginManager)

            print("✅ RTM modules can be imported")
        except ImportError as e:
            print(f"❌ Cannot import RTM modules: {e}")
            return False

        # Check pytest is available
        try:
            subprocess.run(
                [sys.executable, "-m", "pytest", "--version"],
                capture_output=True,
                check=True,
            )
            print("✅ pytest is available")
        except subprocess.CalledProcessError:
            print("❌ pytest is not available")
            return False

        print("✅ Test environment validation passed")
        return True

    def generate_test_report(self) -> None:
        """Generate comprehensive test report."""
        print("📋 Generating Test Report...")

        report_file = self.project_root / "reports" / "rtm-test-report.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        # Run tests and collect results
        unit_result = self.run_unit_tests()
        integration_result = self.run_integration_tests()

        # Generate report
        report_content = f"""# RTM Automation Test Report

**Generated**: {self._get_timestamp()}
**Project**: GoNoGo RTM Automation
**Epic**: EP-00005

## Test Results Summary

| Test Suite | Status | Exit Code |
|------------|--------|-----------|
| Unit Tests | {'✅ PASS' if unit_result == 0 else '❌ FAIL'} | {unit_result} |
| Integration Tests | {'✅ PASS' if integration_result == 0 else '❌ FAIL'} | {integration_result} |

## Test Coverage

Run `python tests/rtm_test_runner.py --coverage` to generate coverage report.

## Test Files

### Unit Tests
- `tests/unit/shared/utils/test_rtm_link_generator.py` - Core RTM functionality

### Integration Tests
- `tests/integration/rtm/test_rtm_end_to_end.py` - End-to-end workflows
- `tests/integration/rtm/test_plugin_system.py` - Plugin system

## Quick Commands

```bash
# Run all tests
python tests/rtm_test_runner.py --all

# Run with coverage
python tests/rtm_test_runner.py --coverage

# Run specific test suite
python tests/rtm_test_runner.py --unit
python tests/rtm_test_runner.py --integration
```

## Environment Validation

Test environment should pass all validation checks:

```bash
python tests/rtm_test_runner.py --validate
```

---
Generated by RTM Test Runner
"""

        with open(report_file, "w") as f:
            f.write(report_content)

        print(f"✅ Test report generated: {report_file}")

    def _run_pytest(self, test_files: list, description: str) -> int:
        """Run pytest on specified test files."""
        cmd = [sys.executable, "-m", "pytest"] + test_files + ["-v"]
        return self._run_command(cmd, description)

    def _run_command(self, cmd: list, description: str) -> int:
        """Run command and return exit code."""
        print(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            if result.returncode == 0:
                print(f"✅ {description} completed successfully")
            else:
                print(f"❌ {description} failed with exit code {result.returncode}")
            return result.returncode
        except Exception as e:
            print(f"❌ Error running {description}: {e}")
            return 1

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="RTM Test Runner")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage"
    )
    parser.add_argument(
        "--performance", action="store_true", help="Run performance tests"
    )
    parser.add_argument("--plugins", action="store_true", help="Run plugin tests")
    parser.add_argument(
        "--validate", action="store_true", help="Validate test environment"
    )
    parser.add_argument("--report", action="store_true", help="Generate test report")

    args = parser.parse_args()

    runner = RTMTestRunner()

    # Default to all tests if no specific option
    if not any(
        [
            args.all,
            args.unit,
            args.integration,
            args.coverage,
            args.performance,
            args.plugins,
            args.validate,
            args.report,
        ]
    ):
        args.all = True

    exit_code = 0

    if args.validate:
        if not runner.validate_test_environment():
            return 1

    if args.unit:
        exit_code = max(exit_code, runner.run_unit_tests())

    if args.integration:
        exit_code = max(exit_code, runner.run_integration_tests())

    if args.all:
        exit_code = max(exit_code, runner.run_all_tests())

    if args.coverage:
        exit_code = max(exit_code, runner.run_with_coverage())

    if args.performance:
        exit_code = max(exit_code, runner.run_performance_tests())

    if args.plugins:
        exit_code = max(exit_code, runner.run_plugin_tests())

    if args.report:
        runner.generate_test_report()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
