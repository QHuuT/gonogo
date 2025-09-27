#!/usr/bin/env python3
"""
HTML Report Generator for GoNoGo Test System

Generates comprehensive, interactive HTML reports from structured test logs
with filtering, sorting, and drill-down capabilities.

Related to: EP-00006 Test Logging and Reporting
User Story: US-00023 HTML report generation system with interactive features

Usage:
    python tools/report_generator.py --input quality/logs/test_execution.log --output quality/reports/
    python tools/report_generator.py --type unit --format detailed
    python tools/report_generator.py --live-mode --refresh 5
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import Jinja2 for template rendering
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("Jinja2 not available. Install with: pip install jinja2")
    sys.exit(1)

# Import our structured logging system
sys.path.append(str(Path(__file__).parent.parent))
from src.shared.logging import LogEntry


@dataclass
class TestSummary:
    """Summary statistics for test execution."""

    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total_duration_ms: float = 0.0
    average_duration_ms: float = 0.0
    success_rate: float = 0.0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    session_duration_ms: float = 0.0


@dataclass
class TestResult:
    """Individual test result for reporting."""

    test_id: str
    test_name: str
    status: str
    duration_ms: float
    timestamp: str
    test_type: str = "unknown"
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


@dataclass
class CoverageSummary:
    """Coverage statistics for reporting."""

    total_statements: int = 0
    covered_statements: int = 0
    coverage_percentage: float = 0.0
    branch_coverage: float = 0.0
    uncovered_lines: List[str] = None
    by_file: Dict[str, Dict[str, Any]] = None

    def __post_init__(self):
        if self.uncovered_lines is None:
            self.uncovered_lines = []
        if self.by_file is None:
            self.by_file = {}


@dataclass
class ReportData:
    """Complete data structure for report generation."""

    summary: TestSummary
    test_results: List[TestResult]
    test_types: Dict[str, TestSummary]
    timeline: List[Dict[str, Any]]
    failure_analysis: Dict[str, Any]
    coverage_data: Optional[CoverageSummary]
    environment_info: Dict[str, Any]
    generation_info: Dict[str, Any]


class ReportGenerator:
    """Main report generator class."""

    def __init__(
        self, template_dir: Optional[Path] = None, output_dir: Optional[Path] = None
    ):
        """Initialize the report generator."""
        self.template_dir = template_dir or Path("quality/reports/templates")
        self.output_dir = output_dir or Path("quality/reports")
        self.assets_dir = self.output_dir / "assets"

        # Set up Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Add custom filters
        self._setup_jinja_filters()

        # Ensure directories exist
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

    def _setup_jinja_filters(self):
        """Set up custom Jinja2 filters for report generation."""

        def format_duration(duration_ms: float) -> str:
            """Format duration in milliseconds to human readable."""
            if duration_ms < 1000:
                return f"{duration_ms:.1f}ms"
            elif duration_ms < 60000:
                return f"{duration_ms / 1000:.1f}s"
            else:
                return f"{duration_ms / 60000:.1f}m"

        def format_timestamp(timestamp: str) -> str:
            """Format ISO timestamp to human readable."""
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return timestamp

        def format_percentage(value: float) -> str:
            """Format percentage value."""
            return f"{value:.1f}%"

        def status_color(status: str) -> str:
            """Get CSS color class for test status."""
            colors = {
                "passed": "success",
                "failed": "danger",
                "skipped": "warning",
                "started": "info",
            }
            return colors.get(status.lower(), "secondary")

        def truncate_text(text: str, length: int = 100) -> str:
            """Truncate text to specified length."""
            return text if len(text) <= length else text[: length - 3] + "..."

        # Register filters
        self.jinja_env.filters["format_duration"] = format_duration
        self.jinja_env.filters["format_timestamp"] = format_timestamp
        self.jinja_env.filters["format_datetime"] = (
            format_timestamp  # Alias for compatibility
        )
        self.jinja_env.filters["format_percentage"] = format_percentage
        self.jinja_env.filters["status_color"] = status_color
        self.jinja_env.filters["truncate"] = truncate_text

    def load_log_data(self, log_file_path: Path) -> List[LogEntry]:
        """Load structured log data from file."""
        log_entries = []

        if not log_file_path.exists():
            print(f"Warning: Log file {log_file_path} does not exist")
            return log_entries

        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        log_data = json.loads(line)
                        # Convert JSON back to LogEntry-like object
                        entry = LogEntry(
                            timestamp=log_data.get("timestamp", ""),
                            level=log_data.get("level", "info"),
                            message=log_data.get("message", ""),
                            test_id=log_data.get("test_id"),
                            test_name=log_data.get("test_name"),
                            test_status=log_data.get("test_status"),
                            duration_ms=log_data.get("duration_ms"),
                            environment=log_data.get("environment"),
                            session_id=log_data.get("session_id"),
                            metadata=log_data.get("metadata"),
                            stack_trace=log_data.get("stack_trace"),
                            tags=log_data.get("tags", []),
                        )
                        log_entries.append(entry)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Invalid JSON on line {line_num}: {e}")
                        continue

        except Exception as e:
            print(f"Error reading log file {log_file_path}: {e}")

        return log_entries

    def load_coverage_data(
        self, coverage_file_path: Optional[Path] = None
    ) -> Optional[CoverageSummary]:
        """Load coverage data from JSON file."""
        if coverage_file_path is None:
            coverage_file_path = Path("quality/reports/coverage.json")

        if not coverage_file_path.exists():
            print(f"Coverage file not found: {coverage_file_path}")
            return None

        try:
            with open(coverage_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract summary data
            totals = data.get("totals", {})
            coverage_summary = CoverageSummary(
                total_statements=totals.get("num_statements", 0),
                covered_statements=totals.get("covered_lines", 0),
                coverage_percentage=round(float(totals.get("percent_covered", 0.0)), 2),
                branch_coverage=round(
                    float(totals.get("percent_covered_display", 0.0)), 2
                ),
                by_file={},
            )

            # Extract per-file coverage data
            files = data.get("files", {})
            for file_path, file_data in files.items():
                if file_path.startswith("src/"):  # Only include source files
                    coverage_summary.by_file[file_path] = {
                        "statements": file_data.get("summary", {}).get(
                            "num_statements", 0
                        ),
                        "covered": file_data.get("summary", {}).get("covered_lines", 0),
                        "percentage": round(
                            float(
                                file_data.get("summary", {}).get("percent_covered", 0.0)
                            ),
                            2,
                        ),
                        "missing_lines": file_data.get("missing_lines", []),
                        "excluded_lines": file_data.get("excluded_lines", []),
                    }

            return coverage_summary

        except Exception as e:
            print(f"Error loading coverage data: {e}")
            return None

    def process_log_data(
        self, log_entries: List[LogEntry], test_type_filter: Optional[str] = None
    ) -> ReportData:
        """Process log entries into report data structure."""

        # Filter by test type if specified
        if test_type_filter:
            log_entries = [
                entry
                for entry in log_entries
                if test_type_filter in (entry.tags or [])
                or (entry.test_name and test_type_filter in entry.test_name.lower())
            ]

        # Extract test results
        test_results = []
        test_summaries = defaultdict(lambda: TestSummary())
        timeline_events = []

        # Group logs by test_id to build complete test results
        tests_by_id = defaultdict(list)
        for entry in log_entries:
            if entry.test_id:
                tests_by_id[entry.test_id].append(entry)

        # Process each test
        for test_id, test_logs in tests_by_id.items():
            test_logs.sort(key=lambda x: x.timestamp)

            # Find the final status log
            final_log = None
            for log in reversed(test_logs):
                if log.test_status in ["passed", "failed", "skipped"]:
                    final_log = log
                    break

            if final_log:
                result = TestResult(
                    test_id=test_id,
                    test_name=final_log.test_name or "Unknown Test",
                    status=final_log.test_status,
                    duration_ms=final_log.duration_ms or 0.0,
                    timestamp=final_log.timestamp,
                    error_message=(
                        final_log.message if final_log.test_status == "failed" else None
                    ),
                    stack_trace=final_log.stack_trace,
                    metadata=final_log.metadata,
                    tags=final_log.tags,
                )
                test_results.append(result)

                # Add to timeline
                timeline_events.append(
                    {
                        "timestamp": final_log.timestamp,
                        "test_name": result.test_name,
                        "status": result.status,
                        "duration_ms": result.duration_ms,
                    }
                )

        # Calculate summary statistics
        summary = self._calculate_summary(test_results)

        # Calculate per-type summaries
        type_summaries = self._calculate_type_summaries(test_results)

        # Generate failure analysis
        failure_analysis = self._analyze_failures(test_results)

        # Prepare environment and generation info
        environment_info = self._get_environment_info(log_entries)
        generation_info = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_log_entries": len(log_entries),
            "generator_version": "1.0.0",
            "test_type_filter": test_type_filter,
        }

        # Load coverage data
        coverage_data = self.load_coverage_data()

        return ReportData(
            summary=summary,
            test_results=test_results,
            test_types=type_summaries,
            timeline=sorted(timeline_events, key=lambda x: x["timestamp"]),
            failure_analysis=failure_analysis,
            coverage_data=coverage_data,
            environment_info=environment_info,
            generation_info=generation_info,
        )

    def _calculate_summary(self, test_results: List[TestResult]) -> TestSummary:
        """Calculate overall test summary statistics."""
        if not test_results:
            return TestSummary()

        status_counts = Counter(result.status for result in test_results)
        total_duration = sum(result.duration_ms for result in test_results)

        passed = status_counts.get("passed", 0)
        failed = status_counts.get("failed", 0)
        skipped = status_counts.get("skipped", 0)
        total = len(test_results)

        # Calculate time bounds
        timestamps = [result.timestamp for result in test_results]
        start_time = min(timestamps) if timestamps else None
        end_time = max(timestamps) if timestamps else None

        session_duration = 0.0
        if start_time and end_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                session_duration = (end_dt - start_dt).total_seconds() * 1000
            except ValueError:
                pass

        return TestSummary(
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            total_duration_ms=total_duration,
            average_duration_ms=total_duration / total if total > 0 else 0.0,
            success_rate=(passed / total * 100) if total > 0 else 0.0,
            start_time=start_time,
            end_time=end_time,
            session_duration_ms=session_duration,
        )

    def _calculate_type_summaries(
        self, test_results: List[TestResult]
    ) -> Dict[str, TestSummary]:
        """Calculate summary statistics by test type."""
        type_results = defaultdict(list)

        # Group tests by type (inferred from test name or tags)
        for result in test_results:
            test_type = self._infer_test_type(result)
            type_results[test_type].append(result)

        # Calculate summary for each type
        type_summaries = {}
        for test_type, results in type_results.items():
            type_summaries[test_type] = self._calculate_summary(results)

        return type_summaries

    def _infer_test_type(self, result: TestResult) -> str:
        """Infer test type from test name and tags."""
        if result.tags:
            for tag in result.tags:
                if tag in [
                    "unit",
                    "integration",
                    "security",
                    "e2e",
                    "bdd",
                    "performance",
                ]:
                    return tag

        test_name_lower = result.test_name.lower()
        if "integration" in test_name_lower:
            return "integration"
        elif "security" in test_name_lower:
            return "security"
        elif "e2e" in test_name_lower or "end_to_end" in test_name_lower:
            return "e2e"
        elif "bdd" in test_name_lower:
            return "bdd"
        elif "performance" in test_name_lower or "perf" in test_name_lower:
            return "performance"
        else:
            return "unit"

    def _analyze_failures(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Analyze test failures for patterns and insights."""
        failed_tests = [r for r in test_results if r.status == "failed"]

        if not failed_tests:
            return {"total_failures": 0, "patterns": [], "most_common_errors": []}

        # Analyze error patterns
        error_patterns = []
        error_messages = [
            test.error_message for test in failed_tests if test.error_message
        ]

        # Simple pattern detection
        assertion_failures = len(
            [msg for msg in error_messages if "assert" in msg.lower()]
        )
        timeout_failures = len(
            [msg for msg in error_messages if "timeout" in msg.lower()]
        )
        connection_failures = len(
            [
                msg
                for msg in error_messages
                if any(
                    word in msg.lower() for word in ["connection", "network", "socket"]
                )
            ]
        )

        if assertion_failures > 0:
            error_patterns.append(
                {"type": "Assertion Failures", "count": assertion_failures}
            )
        if timeout_failures > 0:
            error_patterns.append(
                {"type": "Timeout Failures", "count": timeout_failures}
            )
        if connection_failures > 0:
            error_patterns.append(
                {"type": "Connection Failures", "count": connection_failures}
            )

        # Most common error messages (truncated)
        error_counter = Counter(
            [msg[:100] + "..." if len(msg) > 100 else msg for msg in error_messages]
        )
        most_common = [
            {"message": msg, "count": count}
            for msg, count in error_counter.most_common(5)
        ]

        return {
            "total_failures": len(failed_tests),
            "patterns": error_patterns,
            "most_common_errors": most_common,
            "failure_rate": (
                len(failed_tests) / len(test_results) * 100 if test_results else 0
            ),
        }

    def _get_environment_info(self, log_entries: List[LogEntry]) -> Dict[str, Any]:
        """Extract environment information from log entries."""
        environments = set()
        session_ids = set()

        for entry in log_entries:
            if entry.environment:
                environments.add(entry.environment)
            if entry.session_id:
                session_ids.add(entry.session_id)

        return {
            "environments": list(environments),
            "session_count": len(session_ids),
            "log_entries_processed": len(log_entries),
        }

    def generate_report(
        self,
        report_data: ReportData,
        template_name: str = "main_report.html",
        output_filename: str = "test_report.html",
    ) -> Path:
        """Generate HTML report from report data."""

        # Ensure we have templates
        self._ensure_templates_exist()

        try:
            template = self.jinja_env.get_template(template_name)
        except Exception as e:
            print(f"Error loading template {template_name}: {e}")
            print("Creating basic template...")
            self._create_basic_template()
            template = self.jinja_env.get_template(template_name)

        # Render the template
        html_content = template.render(
            data=report_data,
            summary=asdict(report_data.summary),
            test_results=[asdict(test) for test in report_data.test_results],
            test_types={k: asdict(v) for k, v in report_data.test_types.items()},
            timeline=report_data.timeline,
            failure_analysis=report_data.failure_analysis,
            environment_info=report_data.environment_info,
            generation_info=report_data.generation_info,
        )

        # Write the report
        output_path = self.output_dir / output_filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Report generated: {output_path}")
        return output_path

    def _ensure_templates_exist(self):
        """Ensure required templates exist, create basic ones if needed."""
        main_template = self.template_dir / "main_report.html"
        if not main_template.exists():
            self._create_basic_template()

    def _create_basic_template(self):
        """Create a basic HTML template if none exists."""
        basic_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GoNoGo Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .metric { background: white; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px; }
        .metric-value { font-size: 2em; font-weight: bold; }
        .success { color: #28a745; }
        .danger { color: #dc3545; }
        .warning { color: #ffc107; }
        .info { color: #17a2b8; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #dee2e6; }
        th { background-color: #f8f9fa; }
        .status-passed { background-color: #d4edda; }
        .status-failed { background-color: #f8d7da; }
        .status-skipped { background-color: #fff3cd; }
    </style>
</head>
<body>
    <div class="header">
        <h1>GoNoGo Test Execution Report</h1>
        <p>Generated: {{ generation_info.generated_at | format_timestamp }}</p>
        {% if generation_info.test_type_filter %}
        <p>Filter: {{ generation_info.test_type_filter }} tests</p>
        {% endif %}
    </div>

    <div class="summary">
        <div class="metric">
            <div class="metric-value">{{ summary.total_tests }}</div>
            <div>Total Tests</div>
        </div>
        <div class="metric">
            <div class="metric-value success">{{ summary.passed }}</div>
            <div>Passed</div>
        </div>
        <div class="metric">
            <div class="metric-value danger">{{ summary.failed }}</div>
            <div>Failed</div>
        </div>
        <div class="metric">
            <div class="metric-value warning">{{ summary.skipped }}</div>
            <div>Skipped</div>
        </div>
        <div class="metric">
            <div class="metric-value info">{{ summary.success_rate | format_percentage }}</div>
            <div>Success Rate</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ summary.total_duration_ms | format_duration }}</div>
            <div>Total Duration</div>
        </div>
    </div>

    {% if test_types %}
    <h2>Results by Test Type</h2>
    <table>
        <thead>
            <tr>
                <th>Test Type</th>
                <th>Total</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Skipped</th>
                <th>Success Rate</th>
                <th>Duration</th>
            </tr>
        </thead>
        <tbody>
            {% for type_name, type_summary in test_types.items() %}
            <tr>
                <td><strong>{{ type_name.title() }}</strong></td>
                <td>{{ type_summary.total_tests }}</td>
                <td class="success">{{ type_summary.passed }}</td>
                <td class="danger">{{ type_summary.failed }}</td>
                <td class="warning">{{ type_summary.skipped }}</td>
                <td>{{ type_summary.success_rate | format_percentage }}</td>
                <td>{{ type_summary.total_duration_ms | format_duration }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <h2>Test Results</h2>
    <table>
        <thead>
            <tr>
                <th>Test Name</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Timestamp</th>
                <th>Details</th>
            </tr>
        </thead>
        <tbody>
            {% for result in test_results %}
            <tr class="status-{{ result.status }}">
                <td>{{ result.test_name | truncate(50) }}</td>
                <td><span class="{{ result.status | status_color }}">{{ result.status.title() }}</span></td>
                <td>{{ result.duration_ms | format_duration }}</td>
                <td>{{ result.timestamp | format_timestamp }}</td>
                <td>
                    {% if result.error_message %}
                    <details>
                        <summary>Error Details</summary>
                        <pre>{{ result.error_message | truncate(200) }}</pre>
                    </details>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% if failure_analysis.total_failures > 0 %}
    <h2>Failure Analysis</h2>
    <div class="summary">
        <div class="metric">
            <div class="metric-value danger">{{ failure_analysis.total_failures }}</div>
            <div>Total Failures</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ failure_analysis.failure_rate | format_percentage }}</div>
            <div>Failure Rate</div>
        </div>
    </div>

    {% if failure_analysis.patterns %}
    <h3>Error Patterns</h3>
    <ul>
        {% for pattern in failure_analysis.patterns %}
        <li>{{ pattern.type }}: {{ pattern.count }}</li>
        {% endfor %}
    </ul>
    {% endif %}
    {% endif %}

    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d;">
        <p>Generated by GoNoGo Report Generator v{{ generation_info.generator_version }}</p>
        <p>{{ environment_info.log_entries_processed }} log entries processed</p>
    </footer>
</body>
</html>"""

        template_path = self.template_dir / "main_report.html"
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(basic_template)

        print(f"Created basic template: {template_path}")


def main():
    """CLI entry point for the report generator."""
    parser = argparse.ArgumentParser(
        description="Generate HTML test reports from structured logs"
    )

    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("quality/logs/test_execution.log"),
        help="Input log file path",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("quality/reports"),
        help="Output directory",
    )
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "security", "e2e", "bdd", "all"],
        default="all",
        help="Filter by test type",
    )
    parser.add_argument(
        "--template", default="main_report.html", help="Template name to use"
    )
    parser.add_argument(
        "--filename", default="test_report.html", help="Output filename"
    )
    parser.add_argument(
        "--demo", action="store_true", help="Generate demo report with sample data"
    )

    args = parser.parse_args()

    # Create report generator
    generator = ReportGenerator(output_dir=args.output)

    if args.demo:
        # Generate demo report with sample data
        print("Generating demo report with sample data...")
        demo_data = _create_demo_data()
        output_path = generator.generate_report(
            demo_data, args.template, "demo_" + args.filename
        )
        print(f"Demo report generated: {output_path}")
        return

    # Load and process real log data
    print(f"Loading log data from: {args.input}")
    log_entries = generator.load_log_data(args.input)

    if not log_entries:
        print("No log entries found. Use --demo to generate a sample report.")
        return

    print(f"Processing {len(log_entries)} log entries...")
    test_type_filter = None if args.type == "all" else args.type
    report_data = generator.process_log_data(log_entries, test_type_filter)

    # Analyze log quality and provide feedback
    _analyze_and_report_log_quality(log_entries, report_data)

    print(f"Generating report with {len(report_data.test_results)} test results...")
    output_path = generator.generate_report(report_data, args.template, args.filename)

    print(f"Report generation complete: {output_path}")
    print(
        f"Summary: {report_data.summary.total_tests} tests, "
        f"{report_data.summary.success_rate:.1f}% success rate"
    )


def _analyze_and_report_log_quality(
    log_entries: List[LogEntry], report_data: ReportData
):
    """Analyze log quality and provide feedback about potential issues."""

    # Count logs with test_status
    logs_with_status = sum(1 for entry in log_entries if entry.test_status)
    logs_with_test_id = sum(1 for entry in log_entries if entry.test_id)

    # Calculate conversion rate
    conversion_rate = (
        (len(report_data.test_results) / logs_with_test_id * 100)
        if logs_with_test_id > 0
        else 0
    )

    # Provide feedback based on analysis
    if len(report_data.test_results) == 0 and len(log_entries) > 0:
        print("\n[WARNING] No test results generated from log entries!")
        print("   This usually indicates missing test_status fields in log entries.")
        print("   Solutions:")
        print(
            "   - Use structured logging methods: logger.test_passed(), logger.test_failed(), etc."
        )
        print("   - Generate sample logs: python tools/generate_test_logs.py")
        print("   - Try demo mode: python tools/report_generator.py --demo")

    elif conversion_rate < 50 and logs_with_test_id > 0:
        print(
            f"\n[WARNING] Low conversion rate: {conversion_rate:.1f}% "
            f"({len(report_data.test_results)}/{logs_with_test_id})"
        )
        print("   Some log entries may be missing test_status fields.")
        print(
            f"   Log analysis: {logs_with_status}/{len(log_entries)} entries have test_status"
        )

    elif len(report_data.test_results) > 0:
        print(
            f"[SUCCESS] Good log quality: {len(report_data.test_results)} test results "
            f"from {len(log_entries)} log entries"
        )
        if logs_with_status < len(log_entries):
            incomplete_logs = len(log_entries) - logs_with_status
            print(
                f"   Note: {incomplete_logs} log entries without test_status (info/debug logs)"
            )


def _create_demo_data() -> ReportData:
    """Create demo data for testing the report generator."""
    from datetime import datetime, timedelta

    # Create sample test results
    base_time = datetime.now()
    test_results = []

    for i in range(20):
        status = "passed" if i < 15 else "failed" if i < 18 else "skipped"
        test_results.append(
            TestResult(
                test_id=f"test_{i:03d}",
                test_name=f"test_module.TestClass.test_function_{i:03d}",
                status=status,
                duration_ms=50.0 + (i * 10.0),
                timestamp=(base_time + timedelta(seconds=i)).isoformat(),
                error_message=(
                    "Assertion failed: expected True, got False"
                    if status == "failed"
                    else None
                ),
                metadata={"test_index": i},
                tags=["unit"] if i < 10 else ["integration"],
            )
        )

    # Calculate summary
    summary = TestSummary(
        total_tests=20,
        passed=15,
        failed=3,
        skipped=2,
        total_duration_ms=sum(r.duration_ms for r in test_results),
        success_rate=75.0,
        start_time=base_time.isoformat(),
        end_time=(base_time + timedelta(minutes=2)).isoformat(),
    )

    # Create demo coverage data
    demo_coverage = CoverageSummary(
        total_statements=150,
        covered_statements=135,
        coverage_percentage=90.0,
        branch_coverage=88.5,
        by_file={
            "src/shared/logging/logger.py": {
                "statements": 45,
                "covered": 42,
                "percentage": 93.3,
                "missing_lines": [23, 67, 89],
                "excluded_lines": [],
            },
            "src/shared/logging/config.py": {
                "statements": 25,
                "covered": 25,
                "percentage": 100.0,
                "missing_lines": [],
                "excluded_lines": [5, 6],
            },
            "src/shared/logging/sanitizer.py": {
                "statements": 80,
                "covered": 68,
                "percentage": 85.0,
                "missing_lines": [45, 46, 47, 78, 79, 80, 95, 96, 97, 98, 99, 100],
                "excluded_lines": [10, 11],
            },
        },
    )

    return ReportData(
        summary=summary,
        test_results=test_results,
        test_types={"unit": summary, "integration": summary},
        timeline=[],
        failure_analysis={
            "total_failures": 3,
            "patterns": [],
            "most_common_errors": [],
        },
        coverage_data=demo_coverage,
        environment_info={"environments": ["test"], "session_count": 1},
        generation_info={
            "generated_at": datetime.now().isoformat(),
            "generator_version": "1.0.0",
        },
    )


if __name__ == "__main__":
    main()
