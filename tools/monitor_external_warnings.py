#!/usr/bin/env python3
"""
External Dependency Warning Monitor

Tracks external dependency warnings over time to detect when dependencies
fix their deprecation warnings, allowing us to remove our warning filters.

Usage:
    python tools/monitor_external_warnings.py --baseline    # Create baseline
    python tools/monitor_external_warnings.py --check       # Check for changes
    python tools/monitor_external_warnings.py --report      # Generate report
"""

import json
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Any
import argparse

# Configuration
BASELINE_FILE = Path("quality/monitoring/external_warnings_baseline.json")
REPORT_DIR = Path("quality/monitoring/reports")
TEMP_LOG = Path("/tmp/claude/external_warning_test.log")

# Known external dependencies we monitor
EXTERNAL_DEPENDENCIES = {
    "sqlalchemy": {
        "package": "sqlalchemy",
        "warning_patterns": [
            "datetime.datetime.utcnow() is deprecated",
            "datetime.utcnow() is deprecated",
        ],
        "test_command": [
            "python",
            "-c",
            "import sqlalchemy; from sqlalchemy import create_engine; engine = \
            create_engine('sqlite:///:memory:'); print('Test complete')",
        ],
    },
    "pytest_asyncio": {
        "package": "pytest-asyncio",
        "warning_patterns": [
            "asyncio_default_fixture_loop_scope",
            "The configuration option",
            "PytestDeprecationWarning",
        ],
        "test_command": [
            "python",
            "-m",
            "pytest",
            "tests/unit/security/test_gdpr_compliance.py::TestGDPRSecurity::test_ip_address_anonymization_security",
            "-v",
        ],
    },
}


class ExternalWarningMonitor:
    """Monitor external dependency warnings and track changes over time."""

    def __init__(self):
        self.baseline_file = BASELINE_FILE
        self.report_dir = REPORT_DIR
        self.temp_log = TEMP_LOG

        # Ensure directories exist
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.temp_log.parent.mkdir(parents=True, exist_ok=True)

    def get_package_version(self, package_name: str) -> str:
        """Get installed version of a package."""
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"import {package_name}; print({package_name}.__version__)",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                # Try pip show as fallback
                result = subprocess.run(
                    ["pip", "show", package_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        return line.split(":", 1)[1].strip()
        except Exception as e:
            print(f"Warning: Could not get version for {package_name}: {e}")
        return "unknown"

    def capture_external_warnings(
        self, dependency: str, config: Dict[str, Any]
    ) -> List[str]:
        """Capture warnings from a specific external dependency."""
        warnings_found = []

        try:
            # Run test command with warning capture
            env = {"PYTHONWARNINGS": "always"}
            result = subprocess.run(
                config["test_command"],
                capture_output=True,
                text=True,
                timeout=30,
                env={**subprocess.os.environ, **env},
            )

            # Check both stdout and stderr for warnings
            output = result.stdout + result.stderr

            # Look for warning patterns
            for pattern in config["warning_patterns"]:
                if pattern.lower() in output.lower():
                    # Extract the warning line
                    for line in output.split("\n"):
                        if pattern.lower() in line.lower():
                            warnings_found.append(line.strip())

        except subprocess.TimeoutExpired:
            print(f"Warning: Timeout testing {dependency}")
        except Exception as e:
            print(f"Warning: Error testing {dependency}: {e}")

        return warnings_found

    def create_baseline(self) -> Dict[str, Any]:
        """Create baseline of current external warnings."""
        print("Creating external warning baseline...")

        baseline = {"created_at": datetime.now(UTC).isoformat(), "dependencies": {}}

        for dep_name, dep_config in EXTERNAL_DEPENDENCIES.items():
            print(f"  Checking {dep_name}...")

            version = self.get_package_version(dep_config["package"])
            warnings_found = self.capture_external_warnings(dep_name, dep_config)

            baseline["dependencies"][dep_name] = {
                "package": dep_config["package"],
                "version": version,
                "warning_count": len(warnings_found),
                "warnings": warnings_found,
                "patterns_monitored": dep_config["warning_patterns"],
            }

            print(f"    Version: {version}")
            print(f"    Warnings found: {len(warnings_found)}")

        # Save baseline
        with open(self.baseline_file, "w") as f:
            json.dump(baseline, f, indent=2)

        print(f"Baseline saved to: {self.baseline_file}")
        return baseline

    def check_for_changes(self) -> Dict[str, Any]:
        """Check current warnings against baseline."""
        if not self.baseline_file.exists():
            print("No baseline found. Creating one...")
            return self.create_baseline()

        print("Checking for external warning changes...")

        # Load baseline
        with open(self.baseline_file, "r") as f:
            baseline = json.load(f)

        # Get current state
        current = {"checked_at": datetime.now(UTC).isoformat(), "dependencies": {}}

        changes_detected = []

        for dep_name, dep_config in EXTERNAL_DEPENDENCIES.items():
            print(f"  Checking {dep_name}...")

            version = self.get_package_version(dep_config["package"])
            warnings_found = self.capture_external_warnings(dep_name, dep_config)

            current["dependencies"][dep_name] = {
                "package": dep_config["package"],
                "version": version,
                "warning_count": len(warnings_found),
                "warnings": warnings_found,
                "patterns_monitored": dep_config["warning_patterns"],
            }

            # Compare with baseline
            if dep_name in baseline["dependencies"]:
                baseline_data = baseline["dependencies"][dep_name]
                baseline_count = baseline_data["warning_count"]
                current_count = len(warnings_found)
                baseline_version = baseline_data["version"]

                print(f"    Version: {baseline_version} -> {version}")
                print(f"    Warnings: {baseline_count} -> {current_count}")

                # Detect changes
                if version != baseline_version:
                    changes_detected.append(
                        {
                            "dependency": dep_name,
                            "type": "version_change",
                            "old_version": baseline_version,
                            "new_version": version,
                            "old_warnings": baseline_count,
                            "new_warnings": current_count,
                        }
                    )

                if current_count != baseline_count:
                    changes_detected.append(
                        {
                            "dependency": dep_name,
                            "type": "warning_count_change",
                            "version": version,
                            "old_warnings": baseline_count,
                            "new_warnings": current_count,
                            "improvement": current_count < baseline_count,
                        }
                    )

        # Create change report
        change_report = {
            "baseline_date": baseline["created_at"],
            "check_date": current["checked_at"],
            "changes_detected": changes_detected,
            "current_state": current,
            "baseline_state": baseline,
        }

        return change_report

    def generate_monitoring_report(self, change_data: Dict[str, Any]) -> str:
        """Generate a monitoring report."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        report_file = self.report_dir / f"external_warnings_monitor_{timestamp}.md"

        report = [
            "# External Dependency Warning Monitoring Report",
            f"**Generated:** {datetime.now(UTC).isoformat()}",
            f"**Baseline Date:** {change_data['baseline_date']}",
            "",
            "## Executive Summary",
            "",
        ]

        changes = change_data["changes_detected"]
        if not changes:
            report.extend(
                [
                    "✅ **No changes detected** - All external dependencies stable",
                    "",
                    "**Current filtering status:** MAINTAIN existing warning filters",
                    "**Action required:** None",
                    "",
                ]
            )
        else:
            improvements = [c for c in changes if c.get("improvement", False)]
            regressions = [
                c
                for c in changes
                if c.get("improvement", False) == False
                and c["type"] == "warning_count_change"
            ]
            version_changes = [c for c in changes if c["type"] == "version_change"]

            if improvements:
                report.extend(
                    [
                        f"🎉 **Warning improvements detected:** {len(improvements)} dependencies have fewer warnings",
                        "**Action required:** Review and potentially remove warning filters",
                        "",
                    ]
                )

            if regressions:
                report.extend(
                    [
                        f"⚠️ **Warning regressions detected:** {len(regressions)} dependencies have more warnings",
                        "**Action required:** Review new warnings and update filters if needed",
                        "",
                    ]
                )

            if version_changes:
                report.extend(
                    [
                        f"📦 **Version changes detected:** {len(version_changes)} dependencies updated",
                        "**Action required:** Monitor warning changes with new versions",
                        "",
                    ]
                )

        # Detailed changes
        if changes:
            report.extend(["## Detailed Changes", ""])

            for change in changes:
                report.extend([f"### {change['dependency']}", ""])

                if change["type"] == "version_change":
                    report.extend(
                        [
                            f"**Version Change:** {change['old_version']} → {change['new_version']}",
                            f"**Warning Count:** {change['old_warnings']} → {change['new_warnings']}",
                            "",
                        ]
                    )
                elif change["type"] == "warning_count_change":
                    if change["improvement"]:
                        status = "🎉 IMPROVEMENT"
                        action = "Consider removing warning filters"
                    else:
                        status = "⚠️ REGRESSION"
                        action = "Review new warnings and update filters"

                    report.extend(
                        [
                            f"**Status:** {status}",
                            f"**Version:** {change['version']}",
                            f"**Warning Count:** {change['old_warnings']} → {change['new_warnings']}",
                            f"**Recommended Action:** {action}",
                            "",
                        ]
                    )

        # Current dependency status
        report.extend(["## Current Dependency Status", ""])

        current_deps = change_data["current_state"]["dependencies"]
        for dep_name, dep_data in current_deps.items():
            report.extend(
                [
                    f"### {dep_name}",
                    f"- **Package:** {dep_data['package']}",
                    f"- **Version:** {dep_data['version']}",
                    f"- **Warnings:** {dep_data['warning_count']}",
                    f"- **Patterns Monitored:** {', '.join(dep_data['patterns_monitored'])}",
                    "",
                ]
            )

        # Recommendations
        report.extend(
            [
                "## Monitoring Recommendations",
                "",
                "### When to Remove Warning Filters",
                "",
                "1. **Zero Warnings Detected**: When a dependency shows 0 warnings for 2+ consecutive checks",
                "2. **Version Documentation**: When dependency release notes mention deprecation warning fixes",
                "3. **Stable Reduction**: When warning count reduces and stays stable across multiple versions",
                "",
                "### When to Update Filters",
                "",
                "1. **New Warning Patterns**: When dependencies introduce new deprecation warnings",
                "2. **Warning Count Increase**: When existing dependencies generate more warnings",
                "3. **New Dependencies**: When adding dependencies that generate external warnings",
                "",
                "### Next Steps",
                "",
                "1. **Regular Monitoring**: Run this check weekly or before dependency updates",
                "2. **Baseline Updates**: Update baseline after confirming stable changes",
                "3. **Filter Maintenance**: Update pyproject.toml filters based on findings",
                "",
            ]
        )

        # Write report
        with open(report_file, "w") as f:
            f.write("\n".join(report))

        print(f"Monitoring report generated: {report_file}")
        return str(report_file)

    def update_baseline(self):
        """Update baseline with current state."""
        print("Updating baseline...")
        self.create_baseline()


def main():
    parser = argparse.ArgumentParser(description="Monitor external dependency warnings")
    parser.add_argument(
        "--baseline", action="store_true", help="Create/update baseline"
    )
    parser.add_argument("--check", action="store_true", help="Check for changes")
    parser.add_argument(
        "--report", action="store_true", help="Generate monitoring report"
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update baseline after confirming changes",
    )

    args = parser.parse_args()

    monitor = ExternalWarningMonitor()

    if args.baseline:
        monitor.create_baseline()
    elif args.check:
        changes = monitor.check_for_changes()
        if changes["changes_detected"]:
            print(f"\n{len(changes['changes_detected'])} changes detected!")
            for change in changes["changes_detected"]:
                print(f"  - {change['dependency']}: {change['type']}")
        else:
            print("\nNo changes detected.")
    elif args.report:
        changes = monitor.check_for_changes()
        report_file = monitor.generate_monitoring_report(changes)
        print(f"Report available at: {report_file}")
    elif args.update_baseline:
        monitor.update_baseline()
    else:
        # Default: check and report if changes found
        changes = monitor.check_for_changes()
        if changes["changes_detected"]:
            print("\nChanges detected! Generating report...")
            monitor.generate_monitoring_report(changes)
        else:
            print("\nNo changes detected.")


if __name__ == "__main__":
    main()
