"""Regression demo for multi-persona dashboard summaries (US-00072)."""

import json
from pathlib import Path

import pytest

from src.be.api.rtm import calculate_dashboard_summary

DEMO_PATH = (
    Path(__file__).resolve().parents[2] / "demo" / "multipersona_dashboard_demo.json"
)


def load_demo_dataset():
    with open(DEMO_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.mark.epic("EP-00010")
@pytest.mark.user_story("US-00072")
@pytest.mark.component("backend")
@pytest.mark.test_type("regression")
class TestDashboardPersonaDemo:
    """Ensure persona summaries stay stable against curated demo data."""

    data = load_demo_dataset()
    epics = data["epics"]
    expectations = data["expected"]

    @pytest.mark.parametrize("persona", ["PM", "PO", "QA"])
    def test_summary_matches_demo_expectations(self, persona):
        summary = calculate_dashboard_summary(self.epics, persona)
        expected = self.expectations[persona]

        # Expectation keys must be present
        missing = [key for key in expected if key not in summary]
        assert not missing, f"Missing fields for {persona}: {missing}"

        for key, expected_value in expected.items():
            actual_value = summary[key]
            if isinstance(expected_value, float):
                assert actual_value == pytest.approx(
                    expected_value, rel=1e-3
                ), f"Unexpected {key} for {persona}: got {actual_value}, expected {expected_value}"
            else:
                assert (
                    actual_value == expected_value
                ), f"Unexpected {key} for {persona}: got {actual_value}, expected {expected_value}"

    def test_demo_dataset_covers_velocity_and_scope_dimensions(self):
        pm_summary = calculate_dashboard_summary(self.epics, "PM")
        po_summary = calculate_dashboard_summary(self.epics, "PO")

        assert "average_velocity_per_member" in pm_summary
        assert pm_summary["average_velocity_per_member"] == pytest.approx(
            8.33, rel=1e-3
        )

        assert "average_scope_creep_percentage" in po_summary
        assert po_summary["average_scope_creep_percentage"] == pytest.approx(
            17.3, rel=1e-3
        )

    def test_demo_dataset_captures_quality_dimensions(self):
        qa_summary = calculate_dashboard_summary(self.epics, "QA")

        assert qa_summary["average_test_coverage"] == pytest.approx(83.0, rel=1e-3)
        assert qa_summary["average_defect_density"] == pytest.approx(0.33, rel=1e-3)
        assert qa_summary["average_technical_debt"] == pytest.approx(50.0, rel=1e-3)
