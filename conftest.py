"""
Global pytest configuration and fixtures.
Automatically saves test output to quality/logs when running pytest.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import pytest


class TestOutputCapture:
    """Captures and saves pytest console output automatically."""

    def __init__(self):
        self.original_stdout = None
        self.original_stderr = None
        self.log_file = None
        self.log_path = None

    def start_capture(self, config=None):
        """Start capturing console output."""
        # Create logs directory if it doesn't exist
        log_dir = Path("quality/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Determine test type from command line arguments
        test_type = self._determine_test_type(config)

        # Create timestamped log file with test type
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path = log_dir / f"pytest_{test_type}_output_{timestamp}.log"

        # Open log file with proper encoding for Windows
        self.log_file = open(self.log_path, 'w', encoding='utf-8', errors='replace', newline='')

        # Save original streams
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Create tee-like behavior
        sys.stdout = TeeWriter(self.original_stdout, self.log_file)
        sys.stderr = TeeWriter(self.original_stderr, self.log_file)

        print(f"[PYTEST] Test output being saved to: {self.log_path}")

    def _determine_test_type(self, config):
        """Determine the test type based on command line arguments or test paths."""
        if config is None:
            return "all"

        # Get the test paths from config
        test_args = config.getoption('file_or_dir', default=[])

        # Check for specific test directories
        for arg in test_args:
            arg_str = str(arg).lower()
            if 'tests/unit' in arg_str or 'tests\\unit' in arg_str:
                return "unit"
            elif 'tests/integration' in arg_str or 'tests\\integration' in arg_str:
                return "integration"
            elif 'tests/security' in arg_str or 'tests\\security' in arg_str:
                return "security"
            elif 'tests/e2e' in arg_str or 'tests\\e2e' in arg_str:
                return "e2e"
            elif 'tests/bdd' in arg_str or 'tests\\bdd' in arg_str:
                return "bdd"

        # Check for specific test markers or keywords
        if config.getoption('keyword', default=''):
            keyword = config.getoption('keyword', default='').lower()
            if 'unit' in keyword:
                return "unit"
            elif 'integration' in keyword:
                return "integration"
            elif 'security' in keyword:
                return "security"
            elif 'e2e' in keyword:
                return "e2e"

        # Default fallback
        return "all"

    def stop_capture(self):
        """Stop capturing and restore original streams."""
        if self.original_stdout:
            sys.stdout = self.original_stdout
        if self.original_stderr:
            sys.stderr = self.original_stderr
        if self.log_file:
            self.log_file.close()
            print(f"[PYTEST] Test output saved to: {self.log_path}")

            # Auto-process the log file to prioritize failures
            self._auto_process_log()

    def _auto_process_log(self):
        """Automatically process the log file to show failures first."""
        try:
            # Import here to avoid circular imports
            import subprocess
            import sys

            # Run the post-processor
            result = subprocess.run([
                sys.executable,
                "tools/process_test_logs.py",
                str(self.log_path)
            ], capture_output=True, text=True, encoding='utf-8', errors='replace')

            if result.returncode == 0:
                # Check the output for failure count
                if "[FAILURES]" in result.stdout:
                    failures_line = [line for line in result.stdout.split('\n') if '[FAILURES]' in line]
                    if failures_line:
                        print(f"[PYTEST] {failures_line[0]} - Processed log created")
                    else:
                        print(f"[PYTEST] Failures found - Processed log created")
                else:
                    print(f"[PYTEST] No failures found - Processed log created")
            else:
                print(f"[PYTEST] Note: Post-processing failed")
                if result.stderr:
                    print(f"[PYTEST] Error: {result.stderr}")

        except Exception as e:
            print(f"[PYTEST] Note: Auto-processing skipped ({str(e)})")


class TeeWriter:
    """Write to both console and file."""

    def __init__(self, console, file):
        self.console = console
        self.file = file

    def write(self, text):
        # Write to console normally
        self.console.write(text)

        # Clean and write to file
        try:
            # Remove ANSI escape sequences and problematic Unicode characters
            import re
            clean_text = re.sub(r'\x1b\[[0-9;]*m', '', text)  # Remove ANSI color codes
            clean_text = clean_text.encode('ascii', errors='ignore').decode('ascii')  # Keep only ASCII
            self.file.write(clean_text)
        except Exception:
            # Final fallback - write basic text only
            try:
                simple_text = ''.join(c for c in text if ord(c) < 128)
                self.file.write(simple_text)
            except Exception:
                self.file.write('[encoding error]\n')

        self.file.flush()  # Ensure immediate write

    def flush(self):
        self.console.flush()
        self.file.flush()

    def __getattr__(self, name):
        return getattr(self.console, name)


# Global capture instance
_capture = TestOutputCapture()


def pytest_configure(config):
    """Called when pytest starts."""
    # Only capture if running with real tests (not just collection)
    if not config.getoption("--collect-only"):
        _capture.start_capture(config)


def pytest_unconfigure(config):
    """Called when pytest finishes."""
    _capture.stop_capture()


# Make sure the capture works for session scope
@pytest.fixture(scope="session", autouse=True)
def ensure_output_capture():
    """Ensure output capture is working for the entire session."""
    yield
    # Cleanup handled by pytest_unconfigure