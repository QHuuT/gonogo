"""
Failure Reporting and Analysis

This module generates comprehensive reports and visualizations
for test failure tracking and pattern analysis.

Related to: US-00025 Test failure tracking and reporting
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


from .failure_tracker import FailureTracker

# Import frontend services for proper separation of concerns
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from fe.services import TemplateService, AssetService


class FailureReporter:
    """Generate comprehensive failure analysis reports."""

    def __init__(self, failure_tracker: FailureTracker):
        """Initialize reporter with failure tracker instance."""
        self.tracker = failure_tracker

        # Use frontend services for template rendering
        self.template_service = TemplateService()
        self.asset_service = AssetService()

        # Legacy compatibility - maintain old interface
        self.template_env = self.template_service.jinja_env

    def generate_daily_summary(
        self, output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate daily failure summary report."""
        if output_path is None:
            output_path = Path("quality/reports/failure_summary_daily.json")

        # Get statistics for different time periods
        today_stats = self.tracker.get_failure_statistics(days=1)
        week_stats = self.tracker.get_failure_statistics(days=7)
        month_stats = self.tracker.get_failure_statistics(days=30)

        # Get top failing tests
        top_failing = self.tracker.get_top_failing_tests(limit=10)

        # Detect current patterns
        patterns = self.tracker.detect_patterns()

        # Create comprehensive report
        report_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "today": {
                    "total_failures": today_stats.total_failures,
                    "unique_failures": today_stats.unique_failures,
                    "failure_rate": today_stats.failure_rate,
                    "most_common_category": today_stats.most_common_category.value,
                },
                "week": {
                    "total_failures": week_stats.total_failures,
                    "unique_failures": week_stats.unique_failures,
                    "failure_rate": week_stats.failure_rate,
                    "most_common_category": week_stats.most_common_category.value,
                },
                "month": {
                    "total_failures": month_stats.total_failures,
                    "unique_failures": month_stats.unique_failures,
                    "failure_rate": month_stats.failure_rate,
                    "most_common_category": month_stats.most_common_category.value,
                },
            },
            "top_failing_tests": [
                {
                    "test_name": test["test_name"],
                    "failure_count": test["failure_count"],
                    "category": test["category"],
                    "severity": test["severity"],
                    "last_failure": test["last_failure"],
                    "file_path": test["file_path"],
                }
                for test in top_failing
            ],
            "patterns": [
                {
                    "description": pattern.description,
                    "category": pattern.category.value,
                    "occurrences": pattern.occurrences,
                    "confidence": pattern.confidence,
                    "recommendation": pattern.recommendation,
                }
                for pattern in patterns
            ],
        }

        # Save JSON report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        return report_data

    def generate_html_failure_report(self, output_path: Optional[Path] = None) -> str:
        """Generate HTML failure analysis report."""
        if output_path is None:
            output_path = Path("quality/reports/failure_analysis.html")

        # Get comprehensive data
        stats = self.tracker.get_failure_statistics(days=30)
        top_failing = self.tracker.get_top_failing_tests(limit=15)
        patterns = self.tracker.detect_patterns()

        # Get CSS files for reports page from asset service
        css_files = self.asset_service.get_all_css_for_page("reports")

        # Render HTML using frontend template service
        html_content = self.template_service.render_template(
            "reports/failure_report.html",
            css_files=css_files,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            stats=stats,
            failing_tests_rows=self._generate_failing_tests_rows(top_failing),
            pattern_cards=self._generate_pattern_cards(patterns),
            recommendations_html=self._generate_recommendations_html(stats, patterns),
        )

        # Save HTML report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(output_path)

    def _generate_failing_tests_rows(self, top_failing: List[Dict]) -> str:
        """Generate HTML rows for top failing tests table."""
        if not top_failing:
            return "<tr><td colspan='6' style='text-align: center; color: #666;'>No recent failures detected</td></tr>"

        rows = []
        for test in top_failing:
            test_name = test["test_name"]
            failure_count = test["failure_count"]
            category = test["category"]
            severity = test["severity"]
            last_failure = test["last_failure"]
            file_path = test["file_path"]

            # Determine styling classes
            category_class = f"category-{category.lower()}"
            severity_class = f"severity-{severity.lower()}"

            # Truncate long test names for display
            display_name = test_name if len(test_name) <= 50 else f"{test_name[:47]}..."

            # Format last failure date
            formatted_date = last_failure[:10] if last_failure else "Unknown"

            # Truncate file path
            display_path = (
                file_path if len(file_path) <= 40 else f"...{file_path[-37:]}"
            )

            row = f"""
                <tr>
                    <td title="{test_name}">{display_name}</td>
                    <td><strong>{failure_count}</strong></td>
                    <td><span class="category-badge {category_class}">{
                category.replace("_", " ").title()
            }</span></td>
                    <td><span class="{severity_class}">{severity.title()}</span></td>
                    <td>{formatted_date}</td>
                    <td title="{file_path}">{display_path}</td>
                </tr>
            """
            rows.append(row)

        return "".join(rows)

    def _generate_pattern_cards(self, patterns: List) -> str:
        """Generate HTML cards for detected patterns."""
        if not patterns:
            return "<p style='color: #666; text-align: center;'>No significant patterns detected</p>"

        cards = []
        for pattern in patterns:
            confidence_class = (
                "high"
                if pattern.confidence > 0.8
                else "medium"
                if pattern.confidence > 0.5
                else "low"
            )

            card = f"""
                <div class="pattern-card">
                    <div class="pattern-header">{pattern.description}</div>
                    <div class="pattern-meta">
                        <strong>Occurrences:</strong> {pattern.occurrences} |
                        <strong>Category:</strong> {pattern.category.value.replace("_", " ").title()} |
                        <strong>Confidence:</strong> <span class="confidence-{confidence_class}">{pattern.confidence:.0%}</span>
                    </div>
                    {f'<div class="pattern-recommendation"><strong>Recommendation:</strong> {pattern.recommendation}</div>' if pattern.recommendation else ""}
                </div>
            """
            cards.append(card)

        return "".join(cards)

    def _generate_recommendations_html(self, stats, patterns) -> str:
        """Generate HTML for actionable recommendations."""
        recommendations = []

        # Critical failures recommendation
        if stats.critical_failure_count > 0:
            recommendations.append(
                f"🚨 Address {stats.critical_failure_count} critical failures immediately"
            )

        # High failure rate recommendation
        if stats.failure_rate > 10:
            recommendations.append(
                f"⚠️ Failure rate is {stats.failure_rate:.1f}% - investigate test stability"
            )

        # Flaky tests recommendation
        if stats.flaky_test_count > 0:
            recommendations.append(
                f"🔄 {stats.flaky_test_count} flaky tests detected - improve test reliability"
            )

        # Pattern-based recommendations
        for pattern in patterns:
            if pattern.recommendation and pattern.confidence > 0.7:
                recommendations.append(f"💡 {pattern.recommendation}")

        # General recommendations
        if stats.total_failures > 50:
            recommendations.append(
                "📊 High failure volume detected - consider test suite optimization"
            )

        if not recommendations:
            recommendations.append(
                "✅ No critical issues detected - continue monitoring"
            )

        # Convert to HTML list
        items = "".join([f"<li>{rec}</li>" for rec in recommendations])
        return f"<ul>{items}</ul>"
