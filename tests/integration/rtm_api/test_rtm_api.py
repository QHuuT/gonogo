"""
Integration tests for RTM API endpoints.

Tests CRUD operations and API functionality for the RTM system.

Related Issue: US-00054 - Database models and migration foundation
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.be.database import get_db
from src.be.main import app
from src.be.models.traceability.base import Base

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_rtm.db"
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
@pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
@pytest.mark.user_story("US-00001", "US-00054")
@pytest.mark.component("backend")
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
def sample_epic(client, test_db):
    """Create a sample Epic for testing."""
    epic_data = {
        "epic_id": "EP-00001",
        "title": "Test Epic",
        "description": "A test epic for integration testing",
        "business_value": "Improve testing capabilities",
        "priority": "high",
    }
    response = client.post("/api/rtm/epics/", params=epic_data)
    assert response.status_code == 200
    return response.json()


@pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
@pytest.mark.user_story("US-00001", "US-00054")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("undefined")
@pytest.mark.priority("undefined")
class TestEpicAPI:
    """Test Epic CRUD operations."""

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_create_epic(self, client, test_db):
        """Test creating a new Epic."""
        epic_data = {
            "epic_id": "EP-00001",
            "title": "Test Epic",
            "description": "A test epic",
            "priority": "high",
        }
        response = client.post("/api/rtm/epics/", params=epic_data)

        assert response.status_code == 200
        data = response.json()
        assert data["epic_id"] == "EP-00001"
        assert data["title"] == "Test Epic"
        assert data["priority"] == "high"

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_list_epics(self, client, sample_epic):
        """Test listing Epics."""
        response = client.get("/api/rtm/epics/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["epic_id"] == "EP-00001"

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_list_epics_with_filters(self, client, sample_epic):
        """Test listing Epics with filters."""
        # Filter by priority
        response = client.get("/api/rtm/epics/?priority=high")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        # Filter by non-existent priority
        response = client.get("/api/rtm/epics/?priority=critical")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_get_epic(self, client, sample_epic):
        """Test getting a specific Epic."""
        response = client.get("/api/rtm/epics/EP-00001")

        assert response.status_code == 200
        data = response.json()
        assert data["epic_id"] == "EP-00001"
        assert data["title"] == "Test Epic"

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_get_epic_not_found(self, client, test_db):
        """Test getting a non-existent Epic."""
        response = client.get("/api/rtm/epics/EP-99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_update_epic(self, client, sample_epic):
        """Test updating an Epic."""
        update_data = {"title": "Updated Epic Title", "priority": "critical"}
        response = client.put("/api/rtm/epics/EP-00001", params=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Epic Title"
        assert data["priority"] == "critical"

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_delete_epic(self, client, sample_epic):
        """Test deleting an Epic."""
        response = client.delete("/api/rtm/epics/EP-00001")

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify epic is deleted
        response = client.get("/api/rtm/epics/EP-00001")
        assert response.status_code == 404


@pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
@pytest.mark.user_story("US-00001", "US-00054")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("undefined")
@pytest.mark.priority("undefined")
class TestUserStoryAPI:
    """Test User Story CRUD operations."""

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_create_user_story(self, client, sample_epic):
        """Test creating a new User Story."""
        epic_id = sample_epic["id"]
        us_data = {
            "user_story_id": "US-00001",
            "epic_id": epic_id,
            "github_issue_number": 123,
            "title": "Test User Story",
            "story_points": 5,
            "priority": "high",
        }
        response = client.post("/api/rtm/user-stories/", params=us_data)

        assert response.status_code == 200
        data = response.json()
        assert data["user_story_id"] == "US-00001"
        assert data["epic_id"] == epic_id
        assert data["story_points"] == 5

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_list_user_stories(self, client, sample_epic):
        """Test listing User Stories."""
        # Create a user story first
        epic_id = sample_epic["id"]
        us_data = {
            "user_story_id": "US-00001",
            "epic_id": epic_id,
            "github_issue_number": 123,
            "title": "Test User Story",
        }
        client.post("/api/rtm/user-stories/", params=us_data)

        response = client.get("/api/rtm/user-stories/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_story_id"] == "US-00001"

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_list_user_stories_by_epic(self, client, sample_epic):
        """Test listing User Stories filtered by Epic."""
        epic_id = sample_epic["id"]

        # Create user stories
        us_data = {
            "user_story_id": "US-00001",
            "epic_id": epic_id,
            "github_issue_number": 123,
            "title": "Test User Story",
        }
        client.post("/api/rtm/user-stories/", params=us_data)

        response = client.get(f"/api/rtm/user-stories/?epic_id={epic_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["epic_id"] == epic_id

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_get_user_story(self, client, sample_epic):
        """Test getting a specific User Story."""
        epic_id = sample_epic["id"]
        us_data = {
            "user_story_id": "US-00001",
            "epic_id": epic_id,
            "github_issue_number": 123,
            "title": "Test User Story",
        }
        client.post("/api/rtm/user-stories/", params=us_data)

        response = client.get("/api/rtm/user-stories/US-00001")

        assert response.status_code == 200
        data = response.json()
        assert data["user_story_id"] == "US-00001"


@pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
@pytest.mark.user_story("US-00001", "US-00054")
@pytest.mark.component("backend")
class TestTestAPI:
    """Test Test entity CRUD operations."""

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_create_test(self, client, sample_epic):
        """Test creating a new Test."""
        epic_id = sample_epic["id"]
        test_data = {
            "test_type": "unit",
            "test_file_path": "tests/unit/test_example.py",
            "title": "Example Unit Test",
            "epic_id": epic_id,
            "test_function_name": "test_example_function",
        }
        response = client.post("/api/rtm/tests/", params=test_data)

        assert response.status_code == 200
        data = response.json()
        assert data["test_type"] == "unit"
        assert data["test_file_path"] == "tests/unit/test_example.py"
        assert data["epic_id"] == epic_id

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_list_tests(self, client, sample_epic):
        """Test listing Tests."""
        epic_id = sample_epic["id"]
        test_data = {
            "test_type": "unit",
            "test_file_path": "tests/unit/test_example.py",
            "title": "Example Unit Test",
            "epic_id": epic_id,
        }
        client.post("/api/rtm/tests/", params=test_data)

        response = client.get("/api/rtm/tests/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["test_type"] == "unit"

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_list_tests_with_filters(self, client, sample_epic):
        """Test listing Tests with filters."""
        epic_id = sample_epic["id"]

        # Create different types of tests
        test_data_1 = {
            "test_type": "unit",
            "test_file_path": "tests/unit/test_example.py",
            "title": "Unit Test",
            "epic_id": epic_id,
        }
        test_data_2 = {
            "test_type": "integration",
            "test_file_path": "tests/integration/test_api.py",
            "title": "Integration Test",
            "epic_id": epic_id,
        }
        client.post("/api/rtm/tests/", params=test_data_1)
        client.post("/api/rtm/tests/", params=test_data_2)

        # Filter by test type
        response = client.get("/api/rtm/tests/?test_type=unit")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["test_type"] == "unit"

        # Filter by epic
        response = client.get(f"/api/rtm/tests/?epic_id={epic_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_update_test_execution(self, client, sample_epic):
        """Test updating test execution results."""
        epic_id = sample_epic["id"]
        test_data = {
            "test_type": "unit",
            "test_file_path": "tests/unit/test_example.py",
            "title": "Example Unit Test",
            "epic_id": epic_id,
        }
        create_response = client.post("/api/rtm/tests/", params=test_data)
        test_id = create_response.json()["id"]

        # Update execution result
        execution_data = {"status": "passed", "duration_ms": 150.5}
        response = client.put(
            f"/api/rtm/tests/{test_id}/execution", params=execution_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["last_execution_status"] == "passed"
        assert data["execution_duration_ms"] == 150.5
        assert data["execution_count"] == 1


@pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
@pytest.mark.user_story("US-00001", "US-00054")
@pytest.mark.component("backend")
class TestDefectAPI:
    """Test Defect CRUD operations."""

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_create_defect(self, client, sample_epic):
        """Test creating a new Defect."""
        epic_id = sample_epic["id"]
        defect_data = {
            "defect_id": "DEF-00001",
            "github_issue_number": 456,
            "title": "Test Defect",
            "severity": "high",
            "priority": "critical",
            "epic_id": epic_id,
        }
        response = client.post("/api/rtm/defects/", params=defect_data)

        assert response.status_code == 200
        data = response.json()
        assert data["defect_id"] == "DEF-00001"
        assert data["severity"] == "high"
        assert data["epic_id"] == epic_id

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_list_defects(self, client, sample_epic):
        """Test listing Defects."""
        epic_id = sample_epic["id"]
        defect_data = {
            "defect_id": "DEF-00001",
            "github_issue_number": 456,
            "title": "Test Defect",
            "epic_id": epic_id,
        }
        client.post("/api/rtm/defects/", params=defect_data)

        response = client.get("/api/rtm/defects/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["defect_id"] == "DEF-00001"

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_list_defects_with_filters(self, client, sample_epic):
        """Test listing Defects with filters."""
        epic_id = sample_epic["id"]

        # Create defects with different severities
        defect_data_1 = {
            "defect_id": "DEF-00001",
            "github_issue_number": 456,
            "title": "Critical Defect",
            "severity": "critical",
            "epic_id": epic_id,
        }
        defect_data_2 = {
            "defect_id": "DEF-00002",
            "github_issue_number": 457,
            "title": "Medium Defect",
            "severity": "medium",
            "epic_id": epic_id,
        }
        client.post("/api/rtm/defects/", params=defect_data_1)
        client.post("/api/rtm/defects/", params=defect_data_2)

        # Filter by severity
        response = client.get("/api/rtm/defects/?severity=critical")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["severity"] == "critical"


@pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
@pytest.mark.user_story("US-00001", "US-00054")
@pytest.mark.component("backend")
class TestAnalyticsAPI:
    """Test analytics and reporting endpoints."""

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_epic_progress_analytics(self, client, sample_epic):
        """Test Epic progress analytics."""
        epic_id = sample_epic["epic_id"]

        response = client.get(f"/api/rtm/analytics/epic/{epic_id}/progress")

        assert response.status_code == 200
        data = response.json()
        assert "epic" in data
        assert "metrics" in data
        assert data["epic"]["epic_id"] == epic_id
        assert "total_story_points" in data["metrics"]
        assert "test_pass_rate" in data["metrics"]

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_rtm_overview_analytics(self, client, sample_epic):
        """Test RTM overview analytics."""
        response = client.get("/api/rtm/analytics/overview")

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "epics" in data["summary"]
        assert "user_stories" in data["summary"]
        assert "tests" in data["summary"]
        assert "defects" in data["summary"]

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_pagination(self, client, sample_epic):
        """Test pagination in list endpoints."""
        epic_id = sample_epic["id"]

        # Create multiple test entities
        for i in range(5):
            test_data = {
                "test_type": "unit",
                "test_file_path": f"tests/unit/test_{i}.py",
                "title": f"Test {i}",
                "epic_id": epic_id,
            }
            client.post("/api/rtm/tests/", params=test_data)

        # Test pagination
        response = client.get("/api/rtm/tests/?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        response = client.get("/api/rtm/tests/?limit=2&offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        response = client.get("/api/rtm/tests/?limit=2&offset=4")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Only one remaining


@pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
@pytest.mark.user_story("US-00001", "US-00054")
@pytest.mark.component("backend")
class TestAPIIntegration:
    """Test API integration scenarios."""

    @pytest.mark.epic("EP-00001", "EP-00005", "EP-99999")
    @pytest.mark.user_story("US-00001", "US-00054")
    @pytest.mark.component("backend")
    def test_full_rtm_workflow(self, client, test_db):
        """Test a complete RTM workflow."""
        # 1. Create Epic
        epic_data = {
            "epic_id": "EP-00001",
            "title": "Full Workflow Epic",
            "priority": "high",
        }
        epic_response = client.post("/api/rtm/epics/", params=epic_data)
        epic_id = epic_response.json()["id"]

        # 2. Create User Story
        us_data = {
            "user_story_id": "US-00001",
            "epic_id": epic_id,
            "github_issue_number": 123,
            "title": "Workflow User Story",
            "story_points": 8,
        }
        us_response = client.post("/api/rtm/user-stories/", params=us_data)
        assert us_response.status_code == 200

        # 3. Create Test
        test_data = {
            "test_type": "unit",
            "test_file_path": "tests/unit/test_workflow.py",
            "title": "Workflow Test",
            "epic_id": epic_id,
        }
        test_response = client.post("/api/rtm/tests/", params=test_data)
        test_id = test_response.json()["id"]

        # 4. Update test execution
        execution_data = {"status": "passed", "duration_ms": 200.0}
        client.put(f"/api/rtm/tests/{test_id}/execution", params=execution_data)

        # 5. Create Defect
        defect_data = {
            "defect_id": "DEF-00001",
            "github_issue_number": 456,
            "title": "Workflow Defect",
            "severity": "medium",
            "epic_id": epic_id,
        }
        defect_response = client.post("/api/rtm/defects/", params=defect_data)
        assert defect_response.status_code == 200

        # 6. Check analytics
        progress_response = client.get("/api/rtm/analytics/epic/EP-00001/progress")
        assert progress_response.status_code == 200

        progress_data = progress_response.json()
        assert progress_data["metrics"]["user_stories_count"] == 1
        assert progress_data["metrics"]["tests_count"] == 1
        assert progress_data["metrics"]["defects_count"] == 1
        assert progress_data["metrics"]["test_pass_rate"] == 100.0
