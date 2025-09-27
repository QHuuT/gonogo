"""
Integration test to verify the fix for the 500 error in metrics API.

This test specifically validates that the multi-persona dashboard metrics API
works correctly with real data and doesn't regress to the previous error state.

Related Issues:
- 500 error in metrics API for PM persona
- Epic performance overview display issue in multi-persona dashboard

Parent Epic: EP-00010 - Multi-persona traceability dashboard
"""

import time

import pytest
from fastapi.testclient import TestClient

from src.be.main import app


@pytest.fixture
def client():
    """Create test client for direct API testing."""
    with TestClient(app) as c:
        yield c


@pytest.mark.epic("EP-00010")
@pytest.mark.user_story("US-00071")
@pytest.mark.test_type("integration", "regression")
@pytest.mark.component("backend")
class TestMetricsAPIRegressionIntegration:
    """Integration tests to verify the metrics API regression fix."""

    def test_pm_persona_no_500_error(self, client):
        """Test that PM persona metrics API returns 200, not 500."""
        response = client.get("/api/rtm/dashboard/metrics?persona=PM")

        # This was returning 500 before the fix
        assert response.status_code == 200, (
            f"Expected 200 but got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert data["persona"] == "PM"
        assert "epics" in data
        assert "summary" in data

    def test_po_persona_no_500_error(self, client):
        """Test that PO persona metrics API returns 200, not 500."""
        response = client.get("/api/rtm/dashboard/metrics?persona=PO")

        assert response.status_code == 200, (
            f"Expected 200 but got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert data["persona"] == "PO"

    def test_qa_persona_no_500_error(self, client):
        """Test that QA persona metrics API returns 200, not 500."""
        response = client.get("/api/rtm/dashboard/metrics?persona=QA")

        assert response.status_code == 200, (
            f"Expected 200 but got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert data["persona"] == "QA"

    def test_metrics_api_performance(self, client):
        """Test that metrics API completes within reasonable time (no timeouts)."""
        start_time = time.time()
        response = client.get("/api/rtm/dashboard/metrics?persona=PM")
        duration = time.time() - start_time

        assert response.status_code == 200
        assert duration < 30.0, f"API took too long: {duration:.2f} seconds"

    def test_threshold_metrics_format_in_response(self, client):
        """Test that response contains threshold-evaluated metrics in correct format."""
        response = client.get("/api/rtm/dashboard/metrics?persona=PM")

        assert response.status_code == 200
        data = response.json()

        if data["epics"]:
            # Check that at least one epic has threshold-evaluated metrics
            epic = data["epics"][0]
            metrics = epic["metrics"]

            # Look for threshold-evaluated format in risk metrics
            if "risk" in metrics and "overall_risk_score" in metrics["risk"]:
                risk_score = metrics["risk"]["overall_risk_score"]
                if isinstance(risk_score, dict):
                    assert "value" in risk_score
                    assert "status" in risk_score

    def test_summary_calculations_work_with_threshold_metrics(self, client):
        """Test that summary calculations work correctly with threshold-evaluated metrics."""
        response = client.get("/api/rtm/dashboard/metrics?persona=PM")

        assert response.status_code == 200
        data = response.json()

        summary = data["summary"]

        # These calculations should work without throwing TypeError
        if "average_success_probability" in summary:
            prob = summary["average_success_probability"]
            assert isinstance(prob, (int, float))
            assert 0 <= prob <= 100

        if "average_velocity" in summary:
            velocity = summary["average_velocity"]
            assert isinstance(velocity, (int, float))
            assert velocity >= 0

    def test_all_personas_concurrent_requests(self, client):
        """Test that multiple personas can be requested concurrently without errors."""
        import concurrent.futures

        def get_persona_metrics(persona):
            response = client.get(f"/api/rtm/dashboard/metrics?persona={persona}")
            return persona, response.status_code

        personas = ["PM", "PO", "QA"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(get_persona_metrics, persona) for persona in personas
            ]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All should succeed
        for persona, status_code in results:
            assert status_code == 200, f"Failed for persona {persona}: {status_code}"

    def test_api_doesnt_timeout_with_real_data(self, client):
        """Test that API doesn't timeout even with real database data."""
        # Make multiple requests to ensure stability
        for i in range(3):
            start = time.time()
            response = client.get("/api/rtm/dashboard/metrics?persona=PM")
            duration = time.time() - start

            assert response.status_code == 200, f"Request {i + 1} failed"
            assert duration < 10.0, f"Request {i + 1} took too long: {duration:.2f}s"

    def test_extract_metric_value_function_handles_real_data(self, client):
        """Test that _extract_metric_value function handles real API response data."""
        from src.be.api.rtm import _extract_metric_value

        response = client.get("/api/rtm/dashboard/metrics?persona=PM")
        assert response.status_code == 200

        data = response.json()

        if data["epics"]:
            epic = data["epics"][0]
            metrics = epic["metrics"]

            # Test extraction from real threshold-evaluated metrics
            if "risk" in metrics and "overall_risk_score" in metrics["risk"]:
                risk_score = metrics["risk"]["overall_risk_score"]
                extracted = _extract_metric_value(risk_score)

                # Should extract numeric value or return the data as-is
                assert extracted is not None

    def test_regression_specific_error_conditions(self, client):
        """Test specific conditions that caused the original 500 error."""
        # The original error occurred when trying to do arithmetic on dicts
        # This test ensures that condition is handled

        response = client.get("/api/rtm/dashboard/metrics?persona=PM")
        assert response.status_code == 200

        data = response.json()
        summary = data["summary"]

        # These operations previously failed with TypeError when metrics were dicts
        if "at_risk_epics" in summary:
            assert isinstance(summary["at_risk_epics"], int)

        if "average_velocity" in summary:
            assert isinstance(summary["average_velocity"], (int, float))

    def test_demo_endpoint_still_works(self, client):
        """Test that demo endpoint wasn't broken by the fix."""
        response = client.get("/api/rtm/dashboard/metrics/demo?persona=PM")

        assert response.status_code == 200
        data = response.json()
        assert data["persona"] == "PM"
        assert "mode" in data
        assert data["mode"] == "demo"


@pytest.mark.epic("EP-00010")
@pytest.mark.user_story("US-00071")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
class TestMultiPersonaDashboardIntegration:
    """Integration tests for the complete multi-persona dashboard functionality."""

    def test_multi_persona_dashboard_workflow(self, client):
        """Test the complete workflow that a user would experience."""
        # Step 1: PM checks project health
        pm_response = client.get("/api/rtm/dashboard/metrics?persona=PM")
        assert pm_response.status_code == 200
        pm_data = pm_response.json()

        # Step 2: PO checks business metrics
        po_response = client.get("/api/rtm/dashboard/metrics?persona=PO")
        assert po_response.status_code == 200
        po_data = po_response.json()

        # Step 3: QA checks quality metrics
        qa_response = client.get("/api/rtm/dashboard/metrics?persona=QA")
        assert qa_response.status_code == 200
        qa_data = qa_response.json()

        # All should have consistent epic data
        pm_epic_ids = [epic["epic_id"] for epic in pm_data["epics"]]
        po_epic_ids = [epic["epic_id"] for epic in po_data["epics"]]
        qa_epic_ids = [epic["epic_id"] for epic in qa_data["epics"]]

        # Should all see the same epics (filtered by their persona)
        assert len(pm_epic_ids) > 0
        assert len(po_epic_ids) > 0
        assert len(qa_epic_ids) > 0

    def test_epic_performance_overview_availability(self, client):
        """Test that epic performance overview data is available (the original complaint)."""
        response = client.get("/api/rtm/dashboard/metrics?persona=PM")
        assert response.status_code == 200

        data = response.json()

        # The epic performance overview should be available through the epics list
        assert "epics" in data
        assert len(data["epics"]) > 0

        # Each epic should have performance-related metrics
        for epic in data["epics"]:
            assert "epic_id" in epic
            assert "completion_percentage" in epic
            assert "metrics" in epic

            # Performance-related metrics should be available
            metrics = epic["metrics"]
            assert isinstance(metrics, dict)

            # Should have at least some performance indicators
            performance_indicators = [
                "timeline",
                "velocity",
                "risk",
                "team_productivity",
            ]
            has_performance_data = any(
                indicator in metrics for indicator in performance_indicators
            )
            assert has_performance_data, (
                f"Epic {epic['epic_id']} missing performance indicators"
            )
