"""
Failure Reporting and Analysis

This module generates comprehensive reports and visualizations
for test failure tracking and pattern analysis.

Related to: US-00025 Test failure tracking and reporting
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .failure_tracker import FailureStatistics, FailureTracker


class FailureReporter:
    """Generate comprehensive failure analysis reports."""

    def __init__(self, failure_tracker: FailureTracker):
        """Initialize reporter with failure tracker instance."""
        self.tracker = failure_tracker

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

        report_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "today": {
                    "total_failures": today_stats.total_failures,
                    "unique_failures": today_stats.unique_failures,
                    "failure_rate": today_stats.failure_rate,
                    "critical_count": today_stats.critical_failure_count,
                },
                "week": {
                    "total_failures": week_stats.total_failures,
                    "unique_failures": week_stats.unique_failures,
                    "failure_rate": week_stats.failure_rate,
                    "trend": week_stats.trend_analysis.get(
                        "trend_direction", "unknown"
                    ),
                },
                "month": {
                    "total_failures": month_stats.total_failures,
                    "unique_failures": month_stats.unique_failures,
                    "failure_rate": month_stats.failure_rate,
                    "most_common_category": month_stats.most_common_category.value,
                },
            },
            "top_failing_tests": top_failing,
            "detected_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "description": p.description,
                    "occurrences": p.occurrences,
                    "category": p.category.value,
                    "severity": p.severity.value,
                    "impact_score": p.impact_score,
                    "affected_test_count": len(p.affected_tests),
                }
                for p in patterns
            ],
            "recommendations": self._generate_recommendations(
                today_stats, week_stats, patterns
            ),
        }

        # Save report
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

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Failure Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .timestamp {{
            opacity: 0.9;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        .content {{
            padding: 30px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }}
        .metric-card.warning {{
            border-left-color: #ffc107;
            background: #fff9c4;
        }}
        .metric-card.danger {{
            border-left-color: #dc3545;
            background: #f8d7da;
        }}
        .metric-card.success {{
            border-left-color: #28a745;
            background: #d4edda;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .failure-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .failure-table th,
        .failure-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .failure-table th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .category-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 500;
            color: white;
        }}
        .category-assertion {{ background-color: #dc3545; }}
        .category-import {{ background-color: #fd7e14; }}
        .category-timeout {{ background-color: #6f42c1; }}
        .category-unicode {{ background-color: #e83e8c; }}
        .category-unknown {{ background-color: #6c757d; }}
        .severity-critical {{ color: #dc3545; font-weight: bold; }}
        .severity-high {{ color: #fd7e14; font-weight: bold; }}
        .severity-medium {{ color: #ffc107; }}
        .severity-low {{ color: #28a745; }}
        .severity-flaky {{ color: #6f42c1; font-style: italic; }}
        .pattern-card {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        .pattern-header {{
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .pattern-meta {{
            font-size: 0.9em;
            color: #666;
        }}
        .recommendations {{
            background: #e7f3ff;
            border: 1px solid #b3d4fc;
            border-radius: 8px;
            padding: 20px;
        }}
        .recommendations h3 {{
            margin-top: 0;
            color: #0066cc;
        }}
        .recommendations ul {{
            margin-bottom: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Test Failure Analysis Report</h1>
            <div class="timestamp">Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        </div>

        <div class="content">
            <!-- Metrics Overview -->
            <div class="section">
                <h2>📊 Failure Metrics (Last 30 Days)</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{stats.total_failures}</div>
                        <div class="metric-label">Total Failures</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{stats.unique_failures}</div>
                        <div class="metric-label">Unique Failures</div>
                    </div>
                    <div class="metric-card {'danger' if stats.failure_rate > 10 else 'warning' if stats.failure_rate > 5 else 'success'}">
                        <div class="metric-value">{stats.failure_rate:.1f}%</div>
                        <div class="metric-label">Failure Rate</div>
                    </div>
                    <div class="metric-card {'danger' if stats.critical_failure_count > 0 else 'success'}">
                        <div class="metric-value">{stats.critical_failure_count}</div>
                        <div class="metric-label">Critical Failures</div>
                    </div>
                    <div class="metric-card {'warning' if stats.flaky_test_count > 0 else 'success'}">
                        <div class="metric-value">{stats.flaky_test_count}</div>
                        <div class="metric-label">Flaky Tests</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{stats.most_common_category.value.replace('_', ' ').title()}</div>
                        <div class="metric-label">Most Common Category</div>
                    </div>
                </div>
            </div>

            <!-- Top Failing Tests -->
            <div class="section">
                <h2>🔥 Top Failing Tests</h2>
                <table class="failure-table">
                    <thead>
                        <tr>
                            <th>Test Name</th>
                            <th>File</th>
                            <th>Failures</th>
                            <th>Category</th>
                            <th>Severity</th>
                            <th>Last Failure</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._generate_failing_tests_rows(top_failing)}
                    </tbody>
                </table>
            </div>

            <!-- Failure Patterns -->
            <div class="section">
                <h2>🔍 Detected Patterns</h2>
                {self._generate_pattern_cards(patterns)}
            </div>

            <!-- Recommendations -->
            <div class="section">
                <h2>💡 Recommendations</h2>
                <div class="recommendations">
                    <h3>Action Items</h3>
                    {self._generate_recommendations_html(stats, patterns)}
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

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
            category_class = f"category-{test['category'].replace('_', '-')}"
            severity_class = f"severity-{test['severity']}"

            rows.append(
                f"""
                <tr>
                    <td>{test['test_name']}</td>
                    <td><code>{test['test_file']}</code></td>
                    <td><strong>{test['total_failures']}</strong></td>
                    <td><span class="category-badge {category_class}">{test['category'].replace('_', ' ').title()}</span></td>
                    <td><span class="{severity_class}">{test['severity'].title()}</span></td>
                    <td>{test['last_failure'][:10] if test['last_failure'] else 'Unknown'}</td>
                </tr>
            """
            )

        return "".join(rows)

    def _generate_pattern_cards(self, patterns: List) -> str:
        """Generate HTML cards for detected patterns."""
        if not patterns:
            return "<p style='color: #666;'>No significant patterns detected in recent failures.</p>"

        cards = []
        for pattern in patterns:
            cards.append(
                f"""
                <div class="pattern-card">
                    <div class="pattern-header">{pattern.description}</div>
                    <div class="pattern-meta">
                        <strong>Occurrences:</strong> {pattern.occurrences} |
                        <strong>Category:</strong> {pattern.category.value.replace('_', ' ').title()} |
                        <strong>Impact Score:</strong> {pattern.impact_score:.1f} |
                        <strong>Affected Tests:</strong> {len(pattern.affected_tests)}
                    </div>
                </div>
            """
            )

        return "".join(cards)

    def _generate_recommendations(self, today_stats, week_stats, patterns) -> List[str]:
        """Generate actionable recommendations based on failure analysis."""
        recommendations = []

        # Critical failure recommendations
        if today_stats.critical_failure_count > 0:
            recommendations.append(
                "🚨 Address critical failures immediately - these may block releases"
            )

        # High failure rate recommendations
        if week_stats.failure_rate > 15:
            recommendations.append(
                "📈 Failure rate is high (>15%) - review test stability and infrastructure"
            )

        # Flaky test recommendations
        if week_stats.flaky_test_count > 0:
            recommendations.append(
                f"🔄 {week_stats.flaky_test_count} flaky tests detected - investigate intermittent issues"
            )

        # Pattern-based recommendations
        for pattern in patterns:
            if pattern.category.value == "unicode_error" and pattern.occurrences > 2:
                recommendations.append(
                    "🌐 Multiple Unicode errors detected - review file encoding practices"
                )
            elif pattern.category.value == "import_error" and pattern.occurrences > 1:
                recommendations.append(
                    "📦 Import errors detected - verify dependencies and Python path configuration"
                )
            elif pattern.category.value == "timeout_error" and pattern.occurrences > 1:
                recommendations.append(
                    "⏱️ Timeout errors detected - review test performance and infrastructure"
                )

        # Trend-based recommendations
        trend = week_stats.trend_analysis.get("trend_direction", "stable")
        if trend == "increasing":
            recommendations.append(
                "📊 Failure trend is increasing - investigate recent changes and infrastructure"
            )

        # Default recommendations if no specific issues
        if not recommendations:
            recommendations.extend(
                [
                    "✅ Test failure rates are within acceptable ranges",
                    "🔄 Continue monitoring for patterns and trends",
                    "📋 Review this report weekly to identify emerging issues",
                ]
            )

        return recommendations

    def _generate_recommendations_html(self, stats, patterns) -> str:
        """Generate HTML for recommendations section."""
        recommendations = self._generate_recommendations(stats, stats, patterns)

        items = [f"<li>{rec}</li>" for rec in recommendations]
        return f"<ul>{''.join(items)}</ul>"
