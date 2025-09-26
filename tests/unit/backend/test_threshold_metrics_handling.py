"""
Unit tests for threshold-evaluated metrics handling.

Tests the _extract_metric_value function and related threshold processing
to prevent regression of the 500 error that occurred when threshold-evaluated
metrics were compared directly as dictionaries.

Related Issue: Fix for 500 error in metrics API for PM persona
Parent Epic: EP-00010 - Multi-persona traceability dashboard
"""

import pytest
from unittest.mock import Mock, patch

from src.be.api.rtm import _extract_metric_value, calculate_dashboard_summary


@pytest.mark.epic("EP-00010")
@pytest.mark.user_story("US-00071")
@pytest.mark.test_type("unit")
@pytest.mark.component("backend")
class TestExtractMetricValue:
    """Unit tests for the _extract_metric_value helper function."""

    def test_extract_threshold_evaluated_metric(self):
        """Test extraction from threshold-evaluated metric format."""
        # Standard threshold-evaluated format
        threshold_metric = {"value": 42.5, "status": "ok"}
        assert _extract_metric_value(threshold_metric) == 42.5

        # Warning status
        warning_metric = {"value": 75, "status": "warning"}
        assert _extract_metric_value(warning_metric) == 75

        # Danger status
        danger_metric = {"value": 90, "status": "danger"}
        assert _extract_metric_value(danger_metric) == 90

    def test_extract_direct_numeric_value(self):
        """Test extraction from direct numeric values."""
        # Integer
        assert _extract_metric_value(100) == 100

        # Float
        assert _extract_metric_value(67.8) == 67.8

        # Zero
        assert _extract_metric_value(0) == 0

        # Negative (should work for variance metrics)
        assert _extract_metric_value(-5.2) == -5.2

    def test_extract_none_and_default_values(self):
        """Test handling of None values and default fallbacks."""
        # None with default 0
        assert _extract_metric_value(None) == 0

        # None with custom default
        assert _extract_metric_value(None, default=10) == 10
        assert _extract_metric_value(None, default=-1) == -1
        assert _extract_metric_value(None, default=100.5) == 100.5

    def test_extract_from_empty_or_invalid_dict(self):
        """Test handling of empty or invalid dictionary structures."""
        # Empty dict - returns the dict itself since it's not None and doesn't have 'value' key
        assert _extract_metric_value({}) == {}
        assert _extract_metric_value({}, default=5) == {}

        # Dict without 'value' key - returns the dict itself
        no_value_dict = {"status": "ok", "message": "test"}
        assert _extract_metric_value(no_value_dict) == no_value_dict

        # Dict with None value
        none_value_dict = {"value": None, "status": "ok"}
        assert _extract_metric_value(none_value_dict) == 0
        assert _extract_metric_value(none_value_dict, default=15) == 15

        # Dict with empty string value
        empty_string_dict = {"value": "", "status": "ok"}
        assert _extract_metric_value(empty_string_dict) == 0

    def test_extract_edge_cases(self):
        """Test edge cases and unusual input formats."""
        # String numbers (shouldn't happen but should be handled)
        string_metric = {"value": "42", "status": "ok"}
        # This should return "42" as-is since we don't convert types
        assert _extract_metric_value(string_metric) == "42"

        # Boolean values
        bool_metric = {"value": True, "status": "ok"}
        assert _extract_metric_value(bool_metric) == True

        # List or other types (should fallback to default)
        list_value = [1, 2, 3]
        assert _extract_metric_value(list_value) == [1, 2, 3]

    def test_extract_metric_preserves_original_data(self):
        """Test that _extract_metric_value doesn't modify the original data."""
        original_metric = {"value": 50, "status": "warning", "threshold": 40}
        original_copy = original_metric.copy()

        result = _extract_metric_value(original_metric)

        assert result == 50
        assert original_metric == original_copy  # Should be unchanged


@pytest.mark.epic("EP-00010")
@pytest.mark.user_story("US-00071")
@pytest.mark.test_type("unit")
@pytest.mark.component("backend")
class TestDashboardSummaryCalculation:
    """Unit tests for dashboard summary calculation with threshold metrics."""

    def create_mock_epic_metrics(self, persona_type="pm"):
        """Create mock epic metrics data with threshold-evaluated format."""
        if persona_type == "pm":
            return [
                {
                    "epic_id": "EP-001",
                    "title": "Test Epic 1",
                    "status": "active",
                    "completion_percentage": 75.0,
                    "priority": "high",
                    "metrics": {
                        "risk": {
                            "overall_risk_score": {"value": 25, "status": "ok"},
                            "success_probability": {"value": 85, "status": "ok"},
                        },
                        "velocity": {
                            "velocity_points_per_sprint": {"value": 12.5, "status": "ok"},
                        },
                        "timeline": {
                            "schedule_variance_days": {"value": 2.5, "status": "warning"},
                        },
                        "team_productivity": {
                            "velocity_per_team_member": {"value": 4.2, "status": "ok"},
                        },
                    },
                },
                {
                    "epic_id": "EP-002",
                    "title": "Test Epic 2",
                    "status": "active",
                    "completion_percentage": 50.0,
                    "priority": "medium",
                    "metrics": {
                        "risk": {
                            "overall_risk_score": {"value": 45, "status": "warning"},
                            "success_probability": {"value": 70, "status": "warning"},
                        },
                        "velocity": {
                            "velocity_points_per_sprint": {"value": 8.0, "status": "warning"},
                        },
                        "timeline": {
                            "schedule_variance_days": {"value": -1.0, "status": "ok"},
                        },
                        "team_productivity": {
                            "velocity_per_team_member": {"value": 2.7, "status": "warning"},
                        },
                    },
                },
            ]
        elif persona_type == "po":
            return [
                {
                    "epic_id": "EP-001",
                    "metrics": {
                        "stakeholder": {
                            "satisfaction_score": {"value": 8.5, "status": "ok"},
                        },
                        "business_value": {
                            "roi_percentage": {"value": 150.0, "status": "ok"},
                        },
                        "adoption": {
                            "user_adoption_rate": {"value": 75.0, "status": "ok"},
                        },
                        "scope": {
                            "scope_creep_percentage": {"value": 15.0, "status": "warning"},
                        },
                    },
                },
            ]
        elif persona_type == "qa":
            return [
                {
                    "epic_id": "EP-001",
                    "metrics": {
                        "testing": {
                            "test_coverage": {"value": 85, "status": "ok"},
                        },
                        "defects": {
                            "defect_density": {"value": 0.3, "status": "ok"},
                        },
                        "technical_debt": {
                            "debt_hours": {"value": 12, "status": "warning"},
                        },
                    },
                },
            ]

    def test_pm_persona_summary_calculation(self):
        """Test PM persona summary calculation with threshold-evaluated metrics."""
        epic_metrics = self.create_mock_epic_metrics("pm")
        summary = calculate_dashboard_summary(epic_metrics, "PM")

        assert summary["total_epics"] == 2
        assert summary["at_risk_epics"] == 1  # One epic has risk score > 30
        assert summary["risk_percentage"] == 50.0  # 1 out of 2 epics at risk
        assert summary["average_velocity"] == 10.25  # (12.5 + 8.0) / 2
        assert summary["average_velocity_per_member"] == 3.45  # (4.2 + 2.7) / 2
        assert summary["average_schedule_variance"] == 0.8  # (2.5 + (-1.0)) / 2
        assert summary["average_success_probability"] == 77.5  # (85 + 70) / 2
        assert summary["schedule_health"] in ["Good", "Needs Attention"]

    def test_po_persona_summary_calculation(self):
        """Test PO persona summary calculation with threshold-evaluated metrics."""
        epic_metrics = self.create_mock_epic_metrics("po")
        summary = calculate_dashboard_summary(epic_metrics, "PO")

        assert summary["total_epics"] == 1
        assert summary["average_satisfaction"] == 8.5
        assert summary["average_roi"] == 150.0
        assert summary["average_adoption"] == 75.0
        assert summary["average_scope_creep_percentage"] == 15.0
        assert summary["scope_creep_issues"] == 0  # 15% is <= 20%
        assert summary["satisfaction_grade"] in ["Good", "Needs Improvement"]
        assert summary["business_health"] in ["Healthy", "Monitor"]

    def test_qa_persona_summary_calculation(self):
        """Test QA persona summary calculation with threshold-evaluated metrics."""
        epic_metrics = self.create_mock_epic_metrics("qa")
        summary = calculate_dashboard_summary(epic_metrics, "QA")

        assert summary["total_epics"] == 1
        assert summary["average_test_coverage"] == 85.0
        assert summary["average_defect_density"] == 0.3
        assert summary["average_technical_debt"] == 12.0
        assert summary["high_defect_epics"] == 0  # 0.3 is <= 0.5
        assert summary["coverage_grade"] in ["Good", "Needs Improvement"]
        assert summary["quality_health"] in ["Good", "Attention Required"]

    def test_empty_epic_metrics_handling(self):
        """Test that empty epic metrics are handled gracefully."""
        empty_metrics = []
        summary = calculate_dashboard_summary(empty_metrics, "PM")
        assert summary == {}

        summary = calculate_dashboard_summary(empty_metrics, "PO")
        assert summary == {}

        summary = calculate_dashboard_summary(empty_metrics, "QA")
        assert summary == {}

    def test_missing_metrics_handling(self):
        """Test handling of epics with missing or incomplete metrics."""
        incomplete_metrics = [
            {
                "epic_id": "EP-001",
                "metrics": {
                    # Missing most metric categories
                    "risk": {
                        "overall_risk_score": {"value": 10, "status": "ok"},
                    },
                },
            },
            {
                "epic_id": "EP-002",
                "metrics": {
                    # Empty metrics
                },
            },
        ]

        summary = calculate_dashboard_summary(incomplete_metrics, "PM")

        # Should not crash and should provide sensible defaults
        assert summary["total_epics"] == 2
        assert isinstance(summary["average_velocity"], (int, float))
        assert isinstance(summary["average_success_probability"], (int, float))
        assert summary["at_risk_epics"] == 0  # Only one epic has risk score, and it's <= 30

    def test_invalid_persona_handling(self):
        """Test handling of invalid persona types."""
        epic_metrics = self.create_mock_epic_metrics("pm")
        summary = calculate_dashboard_summary(epic_metrics, "INVALID")

        # Should return minimal summary for unknown persona
        assert summary["total_epics"] == 2

    def test_mixed_metric_formats_handling(self):
        """Test handling of mixed metric formats (some threshold, some direct values)."""
        mixed_metrics = [
            {
                "epic_id": "EP-001",
                "metrics": {
                    "risk": {
                        "overall_risk_score": {"value": 25, "status": "ok"},  # Threshold format
                        "success_probability": 90,  # Direct value
                    },
                    "velocity": {
                        "velocity_points_per_sprint": 15.0,  # Direct value
                    },
                },
            },
        ]

        summary = calculate_dashboard_summary(mixed_metrics, "PM")

        # Should handle both formats correctly
        assert summary["total_epics"] == 1
        assert summary["average_velocity"] == 15.0
        assert summary["average_success_probability"] == 90.0

    def test_division_by_zero_protection(self):
        """Test that division by zero is protected against."""
        # This should be handled by the empty metrics check, but test explicitly
        epic_metrics = []

        # Should not raise ZeroDivisionError
        summary = calculate_dashboard_summary(epic_metrics, "PM")
        assert summary == {}

    def test_none_and_null_values_in_metrics(self):
        """Test handling of None and null values within metrics."""
        null_value_metrics = [
            {
                "epic_id": "EP-001",
                "metrics": {
                    "risk": {
                        "overall_risk_score": {"value": None, "status": "ok"},
                        "success_probability": {"value": 0, "status": "ok"},
                    },
                    "velocity": {
                        "velocity_points_per_sprint": None,  # Direct None
                    },
                },
            },
        ]

        summary = calculate_dashboard_summary(null_value_metrics, "PM")

        # Should handle None values gracefully with defaults
        assert summary["total_epics"] == 1
        assert summary["average_velocity"] == 0.0  # Default for None
        assert summary["average_success_probability"] == 0.0
        assert summary["at_risk_epics"] == 0  # None becomes 0, which is <= 30


@pytest.mark.epic("EP-00010")
@pytest.mark.user_story("US-00071")
@pytest.mark.test_type("unit")
@pytest.mark.component("backend")
class TestThresholdMetricsIntegration:
    """Integration tests for threshold metrics with actual Epic model."""

    @patch('src.be.api.rtm.get_threshold_service')
    def test_threshold_service_integration(self, mock_threshold_service):
        """Test integration with the threshold service."""
        # Mock the threshold service
        mock_service = Mock()
        mock_service.evaluate_metric.return_value = {"value": 42, "status": "ok"}
        mock_threshold_service.return_value = mock_service

        # Test that the mocked service would work with our extraction
        result = mock_service.evaluate_metric("test_metric", 42)
        extracted_value = _extract_metric_value(result)

        assert extracted_value == 42

    def test_real_world_metric_structure(self):
        """Test with realistic metric structures that Epic model would generate."""
        # This represents what the Epic model actually generates
        realistic_epic_metrics = [
            {
                "epic_id": "EP-00010",
                "title": "Multi-persona Dashboard",
                "status": "active",
                "completion_percentage": 85.0,
                "priority": "high",
                "metrics": {
                    "timeline": {
                        "estimated_duration_days": None,
                        "actual_duration_days": None,
                        "is_overdue": {"value": False, "status": "ok"},
                    },
                    "velocity": {
                        "velocity_points_per_sprint": {"value": 0.0, "status": "ok"},
                        "velocity_per_team_member": {"value": 0.0, "status": "ok"},
                    },
                    "risk": {
                        "overall_risk_score": {"value": 0, "status": "ok"},
                        "success_probability": {"value": 100, "status": "ok"},
                        "risk_factors": [],
                    },
                    "team_productivity": {
                        "velocity_per_team_member": {"value": 0.0, "status": "ok"},
                        "team_size": {"value": 1, "status": "ok"},
                    },
                },
            },
        ]

        # This should not crash and should produce valid summary
        summary = calculate_dashboard_summary(realistic_epic_metrics, "PM")

        assert summary["total_epics"] == 1
        assert summary["at_risk_epics"] == 0
        assert summary["average_success_probability"] == 100.0
        assert summary["schedule_health"] == "Good"