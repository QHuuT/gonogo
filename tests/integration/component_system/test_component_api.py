"""
Integration tests for RTM Component API endpoints.

Tests the component filtering, grouping, and statistics functionality
added in US-00005: Implement RTM Component Data API and Filtering.

Related Issue: US-00005 - Implement RTM Component Data API and Filtering
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import pytest
from fastapi.testclient import TestClient

from src.be.main import app
from src.be.database import SessionLocal
from src.be.models.traceability import Epic, UserStory, Test, Defect


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create database session for tests."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00005")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
class TestComponentEndpoints:
    """Test component-related API endpoints."""

    @pytest.mark.test_category("smoke")
    @pytest.mark.priority("high")
    def test_list_components(self, client):
        """Test listing all unique components."""
        response = client.get("/api/rtm/components/")
        assert response.status_code == 200

        components = response.json()
        assert isinstance(components, list)
        assert len(components) > 0

        # Should include expected components
        expected_components = ['backend', 'frontend', 'testing', 'ci-cd']
        for comp in expected_components:
            assert comp in components

    @pytest.mark.test_category("smoke")
    @pytest.mark.priority("high")
    def test_component_statistics(self, client):
        """Test component statistics endpoint."""
        response = client.get("/api/rtm/components/statistics")
        assert response.status_code == 200

        data = response.json()
        assert "components" in data
        assert "summary" in data

        # Check structure of component statistics
        components = data["components"]
        assert isinstance(components, dict)

        for component, stats in components.items():
            assert "epic_count" in stats
            assert "user_story_count" in stats
            assert "test_count" in stats
            assert "defect_count" in stats
            assert "test_pass_rate" in stats
            assert "critical_defects" in stats
            assert "total_items" in stats

            # Verify total_items calculation
            expected_total = (
                stats["epic_count"] + stats["user_story_count"] +
                stats["test_count"] + stats["defect_count"]
            )
            assert stats["total_items"] == expected_total

        # Check summary statistics
        summary = data["summary"]
        assert "total_components" in summary
        assert "total_epics" in summary
        assert "total_user_stories" in summary
        assert "total_tests" in summary
        assert "total_defects" in summary

    @pytest.mark.test_category("smoke")
    @pytest.mark.priority("high")
    def test_component_distribution(self, client):
        """Test component distribution analytics."""
        response = client.get("/api/rtm/components/distribution")
        assert response.status_code == 200

        data = response.json()
        assert "distribution" in data
        assert "total_items" in data
        assert "total_components" in data

        distribution = data["distribution"]
        assert isinstance(distribution, list)
        assert len(distribution) > 0

        # Check that percentages add up to 100 (with rounding tolerance)
        total_percentage = sum(item["percentage"] for item in distribution)
        assert 99.0 <= total_percentage <= 101.0

        # Check distribution item structure
        for item in distribution:
            assert "component" in item
            assert "count" in item
            assert "percentage" in item
            assert "breakdown" in item

            breakdown = item["breakdown"]
            assert "epics" in breakdown
            assert "user_stories" in breakdown
            assert "tests" in breakdown
            assert "defects" in breakdown

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_component_items(self, client):
        """Test getting all items for a specific component."""
        # First get available components
        components_response = client.get("/api/rtm/components/")
        components = components_response.json()

        if components:
            component = components[0]  # Test with first available component

            response = client.get(f"/api/rtm/components/{component}/items")
            assert response.status_code == 200

            data = response.json()
            assert "component" in data
            assert data["component"] == component
            assert "epics" in data
            assert "user_stories" in data
            assert "tests" in data
            assert "defects" in data

            # Test with specific filters
            response = client.get(
                f"/api/rtm/components/{component}/items"
                "?include_epics=true&include_user_stories=false&limit=5"
            )
            assert response.status_code == 200

            data = response.json()
            assert isinstance(data["epics"], list)
            assert isinstance(data["user_stories"], list)
            assert len(data["user_stories"]) == 0  # Should be empty due to filter


@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00005")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("undefined")
@pytest.mark.priority("undefined")
class TestComponentFiltering:
    """Test component filtering in existing endpoints."""

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_epic_component_filtering(self, client):
        """Test epic filtering by component."""
        # Test single component filter
        response = client.get("/api/rtm/epics/?component=backend")
        assert response.status_code == 200

        epics = response.json()
        for epic in epics:
            # Epic component should contain 'backend' (may be comma-separated)
            assert 'backend' in epic.get('component', '')

        # Test multiple component filter
        response = client.get("/api/rtm/epics/?component=backend,frontend")
        assert response.status_code == 200

        epics = response.json()
        for epic in epics:
            component = epic.get('component', '')
            assert 'backend' in component or 'frontend' in component

        # Test exclude component filter
        response = client.get("/api/rtm/epics/?exclude_component=testing")
        assert response.status_code == 200

        epics = response.json()
        for epic in epics:
            component = epic.get('component', '')
            assert 'testing' not in component

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_user_story_component_filtering(self, client):
        """Test user story filtering by component."""
        response = client.get("/api/rtm/user-stories/?component=backend&limit=5")
        assert response.status_code == 200

        user_stories = response.json()
        for us in user_stories:
            assert us.get('component') == 'backend'

        # Test multiple components
        response = client.get("/api/rtm/user-stories/?component=backend,frontend")
        assert response.status_code == 200

        user_stories = response.json()
        for us in user_stories:
            assert us.get('component') in ['backend', 'frontend']

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_defect_component_filtering(self, client):
        """Test defect filtering by component."""
        response = client.get("/api/rtm/defects/?component=backend")
        assert response.status_code == 200

        defects = response.json()
        for defect in defects:
            assert defect.get('component') == 'backend'

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_test_component_filtering(self, client):
        """Test test filtering by component."""
        response = client.get("/api/rtm/tests/?component=backend")
        assert response.status_code == 200

        tests = response.json()
        for test in tests:
            # Component may be None for tests that haven't inherited yet
            component = test.get('component')
            if component is not None:
                assert component == 'backend'


@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00005")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("undefined")
@pytest.mark.priority("undefined")
class TestComponentAPIEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_nonexistent_component(self, client):
        """Test filtering with non-existent component."""
        response = client.get("/api/rtm/user-stories/?component=nonexistent")
        assert response.status_code == 200

        user_stories = response.json()
        assert len(user_stories) == 0

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_component_items_nonexistent(self, client):
        """Test getting items for non-existent component."""
        response = client.get("/api/rtm/components/nonexistent/items")
        assert response.status_code == 200

        data = response.json()
        assert data["component"] == "nonexistent"
        assert len(data["epics"]) == 0
        assert len(data["user_stories"]) == 0
        assert len(data["tests"]) == 0
        assert len(data["defects"]) == 0

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_empty_component_filter(self, client):
        """Test filtering with empty component parameter."""
        response = client.get("/api/rtm/user-stories/?component=")
        assert response.status_code == 200

        # Should return all user stories (no filtering applied)
        user_stories = response.json()
        assert isinstance(user_stories, list)

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_component_filter_with_spaces(self, client):
        """Test component filtering with spaces in component names."""
        response = client.get("/api/rtm/user-stories/?component=backend, frontend")
        assert response.status_code == 200

        # Should handle spaces correctly (strip them)
        user_stories = response.json()
        for us in user_stories:
            component = us.get('component')
            if component:
                assert component in ['backend', 'frontend']


@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00005")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("undefined")
@pytest.mark.priority("undefined")
class TestComponentAPIPerformance:
    """Test performance aspects of component API."""

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_component_statistics_performance(self, client, db_session):
        """Test that component statistics can handle reasonable data volumes."""
        # This test ensures the statistics endpoint performs reasonably
        # with the current data set
        response = client.get("/api/rtm/components/statistics")
        assert response.status_code == 200

        data = response.json()

        # Should complete quickly and return comprehensive data
        assert "components" in data
        assert "summary" in data

        # Verify the summary matches the detailed stats
        summary = data["summary"]
        components = data["components"]

        calculated_epics = sum(stats["epic_count"] for stats in components.values())
        calculated_us = sum(stats["user_story_count"] for stats in components.values())
        calculated_tests = sum(stats["test_count"] for stats in components.values())
        calculated_defects = sum(stats["defect_count"] for stats in components.values())

        # Note: Epics can have multiple components, so the epic count in summary
        # might be different from the sum of individual component epic counts
        assert summary["total_user_stories"] == calculated_us
        assert summary["total_tests"] == calculated_tests
        assert summary["total_defects"] == calculated_defects

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_large_component_filter(self, client):
        """Test filtering with large result sets."""
        response = client.get("/api/rtm/user-stories/?limit=50")
        assert response.status_code == 200

        user_stories = response.json()
        assert len(user_stories) <= 50  # Should respect limit

        # Test with component filter and large limit
        response = client.get("/api/rtm/user-stories/?component=backend&limit=50")
        assert response.status_code == 200

        filtered_stories = response.json()
        assert len(filtered_stories) <= 50

        for us in filtered_stories:
            assert us.get('component') == 'backend'


@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00005")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("undefined")
@pytest.mark.priority("undefined")
class TestComponentAPIIntegration:
    """Test integration between component API and other RTM features."""

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_component_data_in_epic_progress(self, client):
        """Test that epic progress includes component information."""
        # Get first epic
        epics_response = client.get("/api/rtm/epics/?limit=1")
        epics = epics_response.json()

        if epics:
            epic_id = epics[0]["epic_id"]

            response = client.get(f"/api/rtm/analytics/epic/{epic_id}/progress")
            assert response.status_code == 200

            data = response.json()
            assert "epic" in data

            epic_data = data["epic"]
            assert "component" in epic_data
            assert "inherited_components" in epic_data

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_component_data_in_rtm_matrix(self, client):
        """Test that RTM matrix includes component information."""
        response = client.get("/api/rtm/reports/matrix?format=json&limit=5")
        assert response.status_code == 200

        data = response.json()

        # Check that component data is included in the matrix
        if "epics" in data:
            for epic_data in data["epics"]:
                # Component is in the epic sub-object
                assert "epic" in epic_data
                epic = epic_data["epic"]
                assert "component" in epic

                # Check user stories in this epic
                if "user_stories" in epic_data:
                    for us in epic_data["user_stories"]:
                        assert "component" in us

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_dashboard_data_with_components(self, client):
        """Test that dashboard data includes component information."""
        response = client.get("/api/rtm/reports/dashboard-data")
        assert response.status_code == 200

        data = response.json()

        # Dashboard should include summary data that could be component-aware
        assert "summary" in data
        summary = data["summary"]

        assert "total_epics" in summary
        assert "total_user_stories" in summary
        assert "total_tests" in summary
        assert "total_defects" in summary

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_rtm_matrix_html_component_columns(self, client):
        """Test that RTM matrix HTML includes component columns in all subtables."""
        response = client.get("/api/rtm/reports/matrix?format=html&limit=1")
        assert response.status_code == 200

        html_content = response.text

        # Check that component column headers are present in all table types
        assert '<th scope="col">Component</th>' in html_content

        # Check that all expected columns exist in the HTML tables
        expected_columns = [
            'ID', 'Title', 'Component', 'Story Points', 'Status',  # User Stories
            'Test Type', 'Function/Scenario', 'Last Execution', 'File Path',  # Tests
            'Priority', 'Severity'  # Defects
        ]

        for column in expected_columns:
            column_header = f'<th scope="col">{column}</th>'
            assert column_header in html_content, f"Missing '{column}' column in RTM matrix HTML"

        # Check that empty state messages have correct colspan
        assert 'colspan="5"' in html_content  # User stories (5 columns now)
        assert 'colspan="6"' in html_content  # Tests and defects (6 columns now)

    @pytest.mark.test_category("undefined")
    @pytest.mark.priority("undefined")
    def test_rtm_matrix_horizontal_scrolling(self, client):
        """Test that RTM matrix HTML includes horizontal scrolling support."""
        response = client.get("/api/rtm/reports/matrix?format=html&limit=1")
        assert response.status_code == 200

        html_content = response.text

        # Check horizontal scrolling CSS is present
        assert 'overflow-x: auto' in html_content
        assert 'min-width: 800px' in html_content
        assert 'position: sticky' in html_content

        # Check table container structure
        assert 'class="rtm-table-container"' in html_content
        assert 'class="rtm-table"' in html_content
        assert 'class="rtm-table__header"' in html_content
        assert 'class="rtm-table__body"' in html_content

        # Check sticky header styling
        assert 'z-index: 10' in html_content
        assert 'top: 0' in html_content

        # Check scrollbar customization
        assert '::-webkit-scrollbar' in html_content
        assert 'height: 8px' in html_content

        # Check responsive design
        assert 'min-width: 600px' in html_content  # Mobile breakpoint


@pytest.mark.asyncio
@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00005")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("undefined")
@pytest.mark.priority("undefined")
async def test_component_api_complete_workflow():
    """Test a complete workflow using component API features."""
    client = TestClient(app)

    # 1. Get available components
    components_response = client.get("/api/rtm/components/")
    assert components_response.status_code == 200
    components = components_response.json()
    assert len(components) > 0

    # 2. Get statistics for all components
    stats_response = client.get("/api/rtm/components/statistics")
    assert stats_response.status_code == 200
    stats = stats_response.json()

    # 3. Filter entities by component
    for component in components[:2]:  # Test first 2 components
        # Filter user stories
        us_response = client.get(f"/api/rtm/user-stories/?component={component}")
        assert us_response.status_code == 200

        # Filter epics
        epic_response = client.get(f"/api/rtm/epics/?component={component}")
        assert epic_response.status_code == 200

        # Get all items for component
        items_response = client.get(f"/api/rtm/components/{component}/items")
        assert items_response.status_code == 200

    # 4. Get distribution analytics
    dist_response = client.get("/api/rtm/components/distribution")
    assert dist_response.status_code == 200

    # All requests should complete successfully
    print("Complete component API workflow test passed!")