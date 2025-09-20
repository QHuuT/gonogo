"""
Unit tests for FastAPI main application.
Testing pyramid: Unit tests (70% of total tests)
"""

import pytest
from fastapi.testclient import TestClient


class TestMainApplication:
    """Unit tests for main FastAPI application routes."""

    def test_health_check_endpoint(self, client: TestClient):
        """Test that health check endpoint returns correct response."""

        response = client.get("/health")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "gonogo-blog"

    def test_home_endpoint_returns_coming_soon(self, client: TestClient):
        """Test that home endpoint returns coming soon message."""

        response = client.get("/")

        assert response.status_code == 200

        data = response.json()
        assert "GoNoGo Blog" in data["message"]
        assert "Coming Soon" in data["message"]

    def test_app_title_and_metadata(self):
        """Test that FastAPI app has correct metadata."""

        from src.be.main import app

        assert app.title == "GoNoGo Blog"
        assert "GDPR-compliant" in app.description
        assert app.version == "0.1.0"

    def test_static_files_mounted(self):
        """Test that static files are properly mounted."""

        from src.be.main import app

        # Check that static files route exists
        static_mount = None
        for route in app.routes:
            if hasattr(route, 'path') and route.path == '/static':
                static_mount = route
                break

        assert static_mount is not None, "Static files should be mounted at /static"

    def test_nonexistent_endpoint_returns_404(self, client: TestClient):
        """Test that non-existent endpoints return 404."""

        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404

    def test_health_endpoint_accepts_only_get(self, client: TestClient):
        """Test that health endpoint only accepts GET requests."""

        # GET should work
        get_response = client.get("/health")
        assert get_response.status_code == 200

        # POST should not work
        post_response = client.post("/health")
        assert post_response.status_code == 405  # Method Not Allowed

        # PUT should not work
        put_response = client.put("/health")
        assert put_response.status_code == 405

    def test_app_has_templates_configured(self):
        """Test that Jinja2 templates are properly configured."""

        from src.be.main import templates

        assert templates is not None
        assert hasattr(templates, 'env')  # Jinja2 environment should be available

    def test_cors_headers_in_response(self, client: TestClient):
        """Test that appropriate headers are set in responses."""

        response = client.get("/health")

        # Should have standard FastAPI headers
        assert "content-type" in response.headers
        assert response.headers["content-type"] == "application/json"