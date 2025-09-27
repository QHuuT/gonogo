"""
Reports View Controller

Handles test failure reports and analytics presentation logic.
Transforms backend report data into frontend-ready format.
"""

from typing import Any, Dict, List

from .base_view import BaseView


class ReportsView(BaseView):
    """Reports-specific view controller."""

    def prepare_data(self, report_data: Dict) -> Dict[str, Any]:
        """Transform raw report data into frontend format."""
        return {
            "stats": report_data.get("stats", {}),
            "top_failing_tests": self._prepare_failing_tests(
                report_data.get("top_failing", [])
            ),
            "patterns": self._prepare_patterns(report_data.get("patterns", [])),
            "recommendations": self._prepare_recommendations(
                report_data.get("recommendations", [])
            ),
            "metadata": {
                "generated_at": report_data.get("generated_at"),
                "report_type": "failure_analysis",
            },
        }

    def _prepare_failing_tests(self, tests: List[Dict]) -> List[Dict]:
        """Prepare failing tests data for frontend display."""
        prepared_tests = []
        for test in tests:
            prepared_tests.append(
                {
                    "test_name": test.get("test_name", ""),
                    "failure_count": test.get("failure_count", 0),
                    "category": test.get("category", ""),
                    "severity": test.get("severity", ""),
                    "last_failure": test.get("last_failure", ""),
                    "file_path": test.get("file_path", ""),
                    "display_name": self._truncate_name(test.get("test_name", ""), 50),
                    "display_path": self._truncate_path(test.get("file_path", ""), 40),
                }
            )
        return prepared_tests

    def _prepare_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """Prepare failure patterns data for frontend display."""
        prepared_patterns = []
        for pattern in patterns:
            confidence = pattern.get("confidence", 0)
            confidence_class = self._get_confidence_class(confidence)

            prepared_patterns.append(
                {
                    "description": pattern.get("description", ""),
                    "category": pattern.get("category", ""),
                    "occurrences": pattern.get("occurrences", 0),
                    "confidence": confidence,
                    "confidence_class": confidence_class,
                    "recommendation": pattern.get("recommendation", ""),
                }
            )
        return prepared_patterns

    def _prepare_recommendations(self, recommendations: List[str]) -> List[Dict]:
        """Prepare recommendations data for frontend display."""
        prepared_recs = []
        for rec in recommendations:
            rec_type = self._get_recommendation_type(rec)
            prepared_recs.append(
                {
                    "text": rec,
                    "type": rec_type,
                    "icon": self._get_recommendation_icon(rec_type),
                }
            )
        return prepared_recs

    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate test name for display."""
        if len(name) <= max_length:
            return name
        return f"{name[: max_length - 3]}..."

    def _truncate_path(self, path: str, max_length: int) -> str:
        """Truncate file path for display."""
        if len(path) <= max_length:
            return path
        return f"...{path[-(max_length - 3) :]}"

    def _get_confidence_class(self, confidence: float) -> str:
        """Get CSS class for confidence level."""
        if confidence > 0.8:
            return "high"
        elif confidence > 0.5:
            return "medium"
        else:
            return "low"

    def _get_recommendation_type(self, recommendation: str) -> str:
        """Determine recommendation type from text."""
        if "🚨" in recommendation or "critical" in recommendation.lower():
            return "critical"
        elif "⚠️" in recommendation or "warning" in recommendation.lower():
            return "warning"
        elif "💡" in recommendation:
            return "suggestion"
        elif "✅" in recommendation:
            return "success"
        else:
            return "info"

    def _get_recommendation_icon(self, rec_type: str) -> str:
        """Get icon for recommendation type."""
        icons = {
            "critical": "🚨",
            "warning": "⚠️",
            "suggestion": "💡",
            "success": "✅",
            "info": "ℹ️",
        }
        return icons.get(rec_type, "ℹ️")

    def render_failure_summary(self, report_data: Dict) -> str:
        """Render failure summary dashboard."""
        # This would use the component service to build a summary dashboard
        # Implementation depends on specific requirements
        pass

    def render_pattern_analysis(self, patterns: List[Dict]) -> str:
        """Render pattern analysis section."""
        # This would use the component service to build pattern cards
        # Implementation depends on specific requirements
        pass
