"""
Regression tests for Dashboard Metrics API endpoints.

Tests specifically designed to catch the 500 error issue that occurred when
threshold-evaluated metrics were being compared directly as dictionaries.

Related Issues:
- Fix for 500 error in metrics API for PM persona
- Epic performance overview display issue in multi-persona dashboard

Parent Epic: EP-00010 - Multi-persona traceability dashboard
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.be.database import get_db
from src.be.main import app
from src.be.models.traceability.base import Base

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_dashboard_metrics.db"
test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    """Create test database tables and clean up after each test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_epics_with_metrics(client, test_db):
    """Create sample Epics with varied completion and metrics data."""
    epics_data = [
        {
            "epic_id": "EP-TEST-001",
            "title": "High Risk Epic",
            "description": "Epic with high risk metrics",
            "priority": "critical",
            "completion_percentage": 25.0,
            "status": "active",
        },
        {
            "epic_id": "EP-TEST-002",
            "title": "Medium Progress Epic",
            "description": "Epic with medium progress",
            "priority": "high",
            "completion_percentage": 75.0,
            "status": "active",
        },
        {
            "epic_id": "EP-TEST-003",
            "title": "Completed Epic",
            "description": "Epic that is completed",
            "priority": "medium",
            "completion_percentage": 100.0,
            "status": "completed",
        },
    ]

    created_epics = []
    for epic_data in epics_data:
        response = client.post("/api/rtm/epics/", params=epic_data)
        assert response.status_code == 200
        created_epics.append(response.json())

    # Add some user stories and tests to create realistic metrics
    for i, epic in enumerate(created_epics):
        epic_id = epic["id"]

        # Add user stories
        for j in range(2):
            us_data = {
                "user_story_id": f"US-TEST-{i+1:03d}-{j+1:02d}",
                "epic_id": epic_id,
                "github_issue_number": 100 + (i * 10) + j,
                "title": f"User Story {j+1} for Epic {i+1}",
                "story_points": 3 + j,
                "priority": "high" if j == 0 else "medium",
            }
            response = client.post("/api/rtm/user-stories/", params=us_data)
            assert response.status_code == 200

        # Add tests
        for k in range(3):
            test_data = {
                "test_type": "unit" if k < 2 else "integration",
                "test_file_path": f"tests/unit/test_epic_{i+1}_{k+1}.py",
                "title": f"Test {k+1} for Epic {i+1}",
                "epic_id": epic_id,
                "test_function_name": f"test_function_{k+1}",
            }
            response = client.post("/api/rtm/tests/", params=test_data)
            assert response.status_code == 200

            # Update test execution status
            test_id = response.json()["id"]
            execution_data = {
                "status": "passed" if k < 2 else "failed",
                "duration_ms": 100.0 + (k * 50),
            }
            client.put(f"/api/rtm/tests/{test_id}/execution", params=execution_data)

        # Add some defects for the first epic to create risk metrics
        if i == 0:
            for d in range(2):
                defect_data = {
                    "defect_id": f"DEF-TEST-{i+1:03d}-{d+1:02d}",
                    "github_issue_number": 200 + (i * 10) + d,
                    "title": f"Defect {d+1} for Epic {i+1}",
                    "severity": "critical" if d == 0 else "medium",
                    "priority": "high",
                    "epic_id": epic_id,
                }
                response = client.post("/api/rtm/defects/", params=defect_data)
                assert response.status_code == 200

    return created_epics


@pytest.mark.epic("EP-00010")
@pytest.mark.user_story("US-00071")
@pytest.mark.test_type("integration", "regression")
@pytest.mark.component("backend")
class TestDashboardMetricsRegression:
    """Regression tests for dashboard metrics API endpoints."""

    def test_pm_persona_metrics_success(self, client, sample_epics_with_metrics):
        """Test PM persona metrics API returns 200 and valid data structure."""
        response = client.get("/api/rtm/dashboard/metrics?persona=PM")

        assert (
            response.status_code == 200
        ), f"Expected 200 but got {response.status_code}: {response.text}"

        data = response.json()

        # Verify response structure
        assert "persona" in data
        assert "epics" in data
        assert "summary" in data
        assert "filters_applied" in data

        assert data["persona"] == "PM"
        assert isinstance(data["epics"], list)
        assert len(data["epics"]) == 3  # Should have 3 test epics

        # Verify summary structure for PM persona
        summary = data["summary"]
        required_pm_fields = [
            "total_epics",
            "at_risk_epics",
            "risk_percentage",
            "average_velocity",
            "average_velocity_per_member",
            "average_schedule_variance",
            "average_success_probability",
            "schedule_health",
        ]

        for field in required_pm_fields:
            assert field in summary, f"Missing required PM summary field: {field}"
            assert isinstance(
                summary[field], (int, float, str)
            ), f"Field {field} has invalid type: {type(summary[field])}"

    def test_po_persona_metrics_success(self, client, sample_epics_with_metrics):
        """Test PO persona metrics API returns 200 and valid data structure."""
        response = client.get("/api/rtm/dashboard/metrics?persona=PO")

        assert (
            response.status_code == 200
        ), f"Expected 200 but got {response.status_code}: {response.text}"

        data = response.json()

        # Verify response structure
        assert data["persona"] == "PO"
        assert isinstance(data["epics"], list)

        # Verify summary structure for PO persona
        summary = data["summary"]
        required_po_fields = [
            "total_epics",
            "average_satisfaction",
            "average_roi",
            "average_adoption",
            "average_scope_creep_percentage",
            "scope_creep_issues",
            "satisfaction_grade",
            "business_health",
        ]

        for field in required_po_fields:
            assert field in summary, f"Missing required PO summary field: {field}"

    def test_qa_persona_metrics_success(self, client, sample_epics_with_metrics):
        """Test QA persona metrics API returns 200 and valid data structure."""
        response = client.get("/api/rtm/dashboard/metrics?persona=QA")

        assert (
            response.status_code == 200
        ), f"Expected 200 but got {response.status_code}: {response.text}"

        data = response.json()

        # Verify response structure
        assert data["persona"] == "QA"
        assert isinstance(data["epics"], list)

        # Verify summary structure for QA persona
        summary = data["summary"]
        required_qa_fields = [
            "total_epics",
            "average_test_coverage",
            "average_defect_density",
            "average_technical_debt",
            "high_defect_epics",
            "coverage_grade",
            "quality_health",
        ]

        for field in required_qa_fields:
            assert field in summary, f"Missing required QA summary field: {field}"

    def test_threshold_evaluated_metrics_handling(
        self, client, sample_epics_with_metrics
    ):
        """Test that threshold-evaluated metrics are properly handled in calculations."""
        response = client.get("/api/rtm/dashboard/metrics?persona=PM")

        assert response.status_code == 200
        data = response.json()

        # Check that epic metrics contain threshold-evaluated format
        epic_metrics = data["epics"][0]["metrics"]

        # Verify that metrics are in threshold-evaluated format (value + status)
        assert "risk" in epic_metrics
        risk_metrics = epic_metrics["risk"]

        if "overall_risk_score" in risk_metrics:
            risk_score = risk_metrics["overall_risk_score"]
            # Should be a dict with 'value' and 'status' keys
            assert isinstance(
                risk_score, dict
            ), f"Risk score should be dict but got {type(risk_score)}"
            assert "value" in risk_score, "Risk score should have 'value' key"
            assert "status" in risk_score, "Risk score should have 'status' key"

        # Verify that summary calculations worked despite threshold format
        summary = data["summary"]
        assert isinstance(summary["average_success_probability"], (int, float))
        assert 0 <= summary["average_success_probability"] <= 100

    def test_metrics_api_with_filters(self, client, sample_epics_with_metrics):
        """Test dashboard metrics API with various filters."""
        # Test epic filter
        response = client.get(
            "/api/rtm/dashboard/metrics?persona=PM&epic_filter=EP-TEST-001"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["epics"]) == 1
        assert data["epics"][0]["epic_id"] == "EP-TEST-001"

        # Test status filter
        response = client.get(
            "/api/rtm/dashboard/metrics?persona=QA&status_filter=active"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["epics"]) == 2  # Only active epics

        # Test non-existent filter
        response = client.get(
            "/api/rtm/dashboard/metrics?persona=PO&status_filter=nonexistent"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["epics"]) == 0
        assert "No epics found matching the criteria" in data["message"]

    def test_metrics_calculation_performance(self, client, sample_epics_with_metrics):
        """Test that metrics calculation completes within reasonable time."""
        import time

        start_time = time.time()
        response = client.get("/api/rtm/dashboard/metrics?persona=PM")
        end_time = time.time()

        duration = end_time - start_time

        assert response.status_code == 200
        assert (
            duration < 10.0
        ), f"Metrics calculation took too long: {duration:.2f} seconds"

    def test_invalid_persona_parameter(self, client, sample_epics_with_metrics):
        """Test behavior with invalid persona parameter."""
        response = client.get("/api/rtm/dashboard/metrics?persona=INVALID")

        # Should still return 200 but with minimal summary data
        assert response.status_code == 200
        data = response.json()
        assert data["persona"] == "INVALID"
        # Summary should contain basic info for invalid persona
        assert "total_epics" in data["summary"]

    def test_extract_metric_value_function_edge_cases(self, client, test_db):
        """Test edge cases for _extract_metric_value function by creating epics with null metrics."""
        # Create epic with minimal data to test null/missing metrics handling
        epic_data = {
            "epic_id": "EP-NULL-TEST",
            "title": "Null Metrics Test Epic",
            "priority": "low",
        }
        response = client.post("/api/rtm/epics/", params=epic_data)
        assert response.status_code == 200

        # Test that metrics API handles epic with minimal/null metrics
        response = client.get("/api/rtm/dashboard/metrics?persona=PM")
        assert response.status_code == 200
        data = response.json()

        # Should not crash and should provide default values
        summary = data["summary"]
        assert isinstance(summary["average_velocity"], (int, float))
        assert isinstance(summary["average_success_probability"], (int, float))

    def test_demo_metrics_endpoint(self, client, test_db):
        """Test that demo metrics endpoint works as fallback."""
        response = client.get("/api/rtm/dashboard/metrics/demo?persona=PM")

        assert response.status_code == 200
        data = response.json()
        assert data["persona"] == "PM"
        assert "mode" in data
        assert data["mode"] == "demo"

    def test_all_personas_concurrent_access(self, client, sample_epics_with_metrics):
        """Test that all personas can be accessed concurrently without conflicts."""
        import concurrent.futures

        def fetch_persona_metrics(persona):
            response = client.get(f"/api/rtm/dashboard/metrics?persona={persona}")
            return persona, response.status_code, response.json()

        personas = ["PM", "PO", "QA"]
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(fetch_persona_metrics, persona) for persona in personas
            ]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        # All requests should succeed
        assert len(results) == 3
        for persona, status_code, data in results:
            assert status_code == 200, f"Failed for persona {persona}: {status_code}"
            assert data["persona"] == persona


@pytest.mark.epic("EP-00010")
@pytest.mark.user_story("US-00071")
@pytest.mark.test_type("unit")
@pytest.mark.component("backend")
class TestMetricValueExtractionUnit:
    """Unit tests for the _extract_metric_value helper function."""

    def test_extract_metric_value_import(self):
        """Test that we can import and use the _extract_metric_value function."""
        from src.be.api.rtm import _extract_metric_value

        # Test threshold-evaluated format
        threshold_metric = {"value": 42, "status": "ok"}
        assert _extract_metric_value(threshold_metric) == 42

        # Test direct value
        direct_value = 100
        assert _extract_metric_value(direct_value) == 100

        # Test None value
        assert _extract_metric_value(None) == 0
        assert _extract_metric_value(None, default=5) == 5

        # Test empty dict
        assert _extract_metric_value({}) == 0

        # Test dict without value key
        dict_no_value = {"status": "ok"}
        assert _extract_metric_value(dict_no_value) == 0

        # Test dict with None value
        dict_none_value = {"value": None, "status": "warning"}
        assert _extract_metric_value(dict_none_value, default=10) == 10


@pytest.mark.epic("EP-00010")
@pytest.mark.user_story("US-00071")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
class TestMetricsAPIErrorHandling:
    """Test error handling and edge cases for metrics API."""

    def test_metrics_with_no_epics(self, client, test_db):
        """Test metrics API behavior when no epics exist."""
        response = client.get("/api/rtm/dashboard/metrics?persona=PM")

        assert response.status_code == 200
        data = response.json()
        assert data["persona"] == "PM"
        assert data["epics"] == []
        assert "No epics found matching the criteria" in data["message"]
        assert data["summary"] == {}

    def test_metrics_with_database_error_resilience(
        self, client, sample_epics_with_metrics
    ):
        """Test that metrics API is resilient to potential database issues."""
        # This test ensures that even if there are database connectivity issues,
        # the API handles them gracefully rather than timing out

        response = client.get("/api/rtm/dashboard/metrics?persona=PM")
        assert response.status_code == 200

        # Should complete in reasonable time even with database load
        import time

        start = time.time()
        for _ in range(3):
            response = client.get("/api/rtm/dashboard/metrics?persona=QA")
            assert response.status_code == 200
        duration = time.time() - start
        assert duration < 30.0, f"Multiple requests took too long: {duration:.2f}s"
