#!/usr/bin/env python3
"""
Dependency Update Detector

Automatically detects when external dependencies have updates available
and triggers warning monitoring checks to see if deprecation warnings
have been resolved.

Usage:
    python tools/check_dependency_updates.py --check           # Check for updates
    python tools/check_dependency_updates.py --auto-monitor    # Check and monitor warnings
    python tools/check_dependency_updates.py --report          # Generate update report
"""

import json
import subprocess
import sys
import argparse
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re

# Import our warning monitor
from monitor_external_warnings import ExternalWarningMonitor, EXTERNAL_DEPENDENCIES

class DependencyUpdateDetector:
    """Detects dependency updates and triggers warning monitoring."""

    def __init__(self):
        self.update_log = Path("quality/monitoring/dependency_updates.json")
        self.update_log.parent.mkdir(parents=True, exist_ok=True)

    def check_for_updates(self) -> Dict[str, Dict[str, str]]:
        """Check for available updates to monitored dependencies."""
        print("Checking for dependency updates...")

        updates_available = {}

        for dep_name, dep_config in EXTERNAL_DEPENDENCIES.items():
            package_name = dep_config["package"]
            print(f"  Checking {package_name}...")

            try:
                # Get current version
                current_version = self._get_current_version(package_name)
                if current_version == "unknown":
                    print(f"    Could not determine current version")
                    continue

                # Get latest available version
                latest_version = self._get_latest_version(package_name)
                if latest_version == "unknown":
                    print(f"    Could not determine latest version")
                    continue

                print(f"    Current: {current_version}")
                print(f"    Latest:  {latest_version}")

                if self._is_newer_version(latest_version, current_version):
                    updates_available[dep_name] = {
                        "package": package_name,
                        "current_version": current_version,
                        "latest_version": latest_version,
                        "update_available": True
                    }
                    print(f"    UPDATE AVAILABLE!")
                else:
                    print(f"    Up to date")

            except Exception as e:
                print(f"    Error checking {package_name}: {e}")

        return updates_available

    def _get_current_version(self, package_name: str) -> str:
        """Get currently installed version of a package."""
        try:
            # Try importing and getting __version__
            result = subprocess.run([
                sys.executable, "-c",
                f"import {package_name.replace('-', '_')}; print({package_name.replace('-', '_')}.__version__)"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return result.stdout.strip()

            # Fallback to pip show
            result = subprocess.run([
                "pip", "show", package_name
            ], capture_output=True, text=True, timeout=10)

            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':', 1)[1].strip()

        except Exception:
            pass

        return "unknown"

    def _get_latest_version(self, package_name: str) -> str:
        """Get latest available version from PyPI."""
        try:
            # Use pip index to get latest version info
            result = subprocess.run([
                "pip", "index", "versions", package_name
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Parse output to find latest version
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Available versions:' in line:
                        # Extract first version (latest)
                        versions_part = \
                            line.split('Available versions:', 1)[1].strip()
                        if versions_part:
                            # Take first version (they're sorted newest first)
                            latest = versions_part.split(',')[0].strip()
                            return latest

            # Fallback: use pip search (if available) or API call
            # For now, try pip list --outdated
            result = subprocess.run([
                "pip", "list", "--outdated", "--format=json"
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                outdated_packages = json.loads(result.stdout)
                for pkg in outdated_packages:
                    if pkg["name"].lower() == package_name.lower():
                        return pkg["latest_version"]

        except Exception:
            pass

        return "unknown"

    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """Compare version strings to see if version1 is newer than version2."""
        try:
            # Simple version comparison (works for most semantic versions)
            def version_tuple(v):
                # Remove any pre-release identifiers (alpha, beta, rc, etc.)
                v_clean = re.split(r'[^0-9.]', v)[0]
                return tuple(map(int, v_clean.split('.')))

            return version_tuple(version1) > version_tuple(version2)
        except Exception:
            # If parsing fails, do string comparison
            return version1 != version2

    def log_update_check(self, updates_found: Dict[str, Dict[str, str]]):
        """Log the results of an update check."""
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "updates_found": len(updates_found),
            "dependencies_checked": list(EXTERNAL_DEPENDENCIES.keys()),
            "updates": updates_found
        }

        # Load existing log or create new
        log_data = []
        if self.update_log.exists():
            try:
                with open(self.update_log, 'r') as f:
                    log_data = json.load(f)
            except Exception:
                log_data = []

        # Add new entry
        log_data.append(log_entry)

        # Keep only last 50 entries
        log_data = log_data[-50:]

        # Save log
        with open(self.update_log, 'w') as f:
            json.dump(log_data, f, indent=2)

    def auto_monitor_on_updates(self) -> Dict[str, any]:
        """Check for updates and automatically run warning monitoring if updates found."""
        print("=== Automatic Dependency Update & Warning Monitoring ===")
        print()

        # Check for updates
        updates = self.check_for_updates()

        # Log the check
        self.log_update_check(updates)

        results = {
            "updates_found": updates,
            "monitoring_triggered": False,
            "monitoring_results": None
        }

        if updates:
            print(f"\n{len(updates)} dependencies have updates available!")
            print("Triggering warning monitoring to check for resolved deprecations...")

            # Run warning monitoring
            monitor = ExternalWarningMonitor()
            monitoring_results = monitor.check_for_changes()

            results["monitoring_triggered"] = True
            results["monitoring_results"] = monitoring_results

            # Generate report if changes detected
            if monitoring_results["changes_detected"]:
                print("Changes detected in warnings - generating report...")
                report_file = monitor.generate_monitoring_report(monitoring_results)
                results["report_generated"] = report_file
        else:
            print("\nAll monitored dependencies are up to date.")

        return results

    def generate_update_report(self, updates: Dict[str, Dict[str, str]]) -> str:
        """Generate a dependency update report."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        report_file = \
            Path(f"quality/monitoring/reports/dependency_updates_{timestamp}.md")
        report_file.parent.mkdir(parents=True, exist_ok=True)

        report = [
            "# Dependency Update Report",
            f"**Generated:** {datetime.now(UTC).isoformat()}",
            "",
            "## Summary",
            ""
        ]

        if not updates:
            report.extend([
                "**All monitored dependencies are up to date**",
                "",
                "No updates available for external dependencies that we monitor for deprecation warnings.",
                ""
            ])
        else:
            report.extend([
                f"**{len(updates)} dependencies have updates available**",
                "",
                "**Recommended Actions:**",
                "1. Review update changelogs for deprecation warning fixes",
                "2. Test updates in development environment",
                "3. Run warning monitoring after updates",
                "4. Update warning filters if deprecations are resolved",
                ""
            ])

        # Update details
        if updates:
            report.extend([
                "## Available Updates",
                ""
            ])

            for dep_name, update_info in updates.items():
                report.extend([
                    f"### {dep_name}",
                    f"- **Package:** {update_info['package']}",
                    f"- **Current Version:** {update_info['current_version']}",
                    f"- **Latest Version:** {update_info['latest_version']}",
                    "",
                    "**Update Commands:**",
                    f"```bash",
                    f"pip install {update_info['package']}>={update_info['latest_version']}",
                    f"python tools/monitor_external_warnings.py --check",
                    f"```",
                    ""
                ])

        # Monitoring workflow
        report.extend([
            "## Warning Monitoring Workflow",
            "",
            "### After Updating Dependencies",
            "",
            "1. **Check Warning Changes:**",
            "   ```bash",
            "   python tools/monitor_external_warnings.py --check",
            "   ```",
            "",
            "2. **Generate Monitoring Report:**",
            "   ```bash",
            "   python tools/monitor_external_warnings.py --report",
            "   ```",
            "",
            "3. **Update Baseline (if changes are stable):**",
            "   ```bash",
            "   python tools/monitor_external_warnings.py --update-baseline",
            "   ```",
            "",
            "4. **Update Warning Filters (if warnings resolved):**",
            "   - Edit `pyproject.toml` filterwarnings section",
            "   - Remove filters for resolved deprecation warnings",
            "   - Test with: `pytest tests/ -v`",
            "",
            "### Automation",
            "",
            "```bash",
            "# Automatic check and monitor",
            "python tools/check_dependency_updates.py --auto-monitor",
            "```",
            ""
        ])

        # Write report
        with open(report_file, 'w') as f:
            f.write('\n'.join(report))

        print(f"Update report generated: {report_file}")
        return str(report_file)

def main():
    parser = \
        argparse.ArgumentParser(description="Check for dependency updates and monitor warnings")
    parser.add_argument("--check", action="store_true", help="Check for dependency updates")
    parser.add_argument("--auto-monitor", action="store_true", help="Check updates and auto-monitor warnings")
    parser.add_argument("--report", action="store_true", help="Generate update report")

    args = parser.parse_args()

    detector = DependencyUpdateDetector()

    if args.check:
        updates = detector.check_for_updates()
        detector.log_update_check(updates)
        if updates:
            print(f"\n{len(updates)} updates available!")
        else:
            print("\nAll dependencies up to date.")
    elif args.auto_monitor:
        results = detector.auto_monitor_on_updates()
        if results["updates_found"]:
            print(
                f"\nCompleted automatic monitoring"
                f"for {len(results['updates_found'])} updated dependencies."
            )
        else:
            print("\nNo updates found, monitoring skipped.")
    elif args.report:
        updates = detector.check_for_updates()
        detector.generate_update_report(updates)
    else:
        # Default: check for updates
        updates = detector.check_for_updates()
        detector.log_update_check(updates)

if __name__ == "__main__":
    main()