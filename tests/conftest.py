"""
Pytest configuration and shared fixtures for GoNoGo blog tests.
Following testing pyramid: Unit > Integration > E2E
"""

import os
import tempfile
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.be.main import app
from src.security.gdpr.models import Base

# Load custom test runner plugin
pytest_plugins = ["tools.test_runner_plugin"]


def pytest_configure(config):
    """Register custom markers for RTM traceability."""
    config.addinivalue_line(
        "markers",
        "user_story(id): mark test as linked to user story (US-XXXXX). Can specify multiple.",
    )
    config.addinivalue_line(
        "markers", "epic(id): mark test as linked to epic (EP-XXXXX). Can specify multiple."
    )
    config.addinivalue_line(
        "markers",
        "component(name): mark test component (backend, frontend, database, etc.). Can specify multiple.",
    )
    config.addinivalue_line(
        "markers",
        "defect(id): mark test as defect regression test (DEF-XXXXX). Can specify multiple.",
    )
    config.addinivalue_line(
        "markers", "priority(level): mark test priority (critical, high, medium, low)"
    )
    config.addinivalue_line(
        "markers", "test_type(type): categorizes tests by type (unit, integration, etc.)"
    )
    config.addinivalue_line(
        "markers", "detailed: marks tests for detailed debugging mode"
    )
    config.addinivalue_line(
        "markers", "smoke: marks tests as smoke tests (critical functionality)"
    )
    config.addinivalue_line(
        "markers", "functional: marks tests as functional tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
    config.addinivalue_line(
        "markers", "gdpr: marks tests as GDPR compliance tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "bdd: marks tests as BDD scenarios"
    )


@pytest.fixture(scope="session")
def test_db() -> Generator[str, None, None]:
    """Create a temporary SQLite database for testing."""

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        test_db_url = f"sqlite:///{temp_file.name}"

        # Create test database
        engine = create_engine(test_db_url, echo=False)
        Base.metadata.create_all(bind=engine)

        try:
            yield test_db_url
        finally:
            # Properly dispose of the engine to release database connections
            engine.dispose()

            # Cleanup - retry deletion with error handling for Windows
            try:
                os.unlink(temp_file.name)
            except PermissionError:
                # On Windows, sometimes the file is still locked briefly
                # Try once more after a short delay
                import time
                time.sleep(0.1)
                try:
                    os.unlink(temp_file.name)
                except PermissionError:
                    # If still failing, log but don't crash tests
                    import warnings
                    warnings.warn(f"Could not delete temporary test database: {temp_file.name}")
                    pass


@pytest.fixture
def db_session(test_db: str):
    """Create a database session for testing."""

    engine = create_engine(test_db, echo=False)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for FastAPI app."""

    return TestClient(app)


@pytest.fixture
def sample_blog_post():
    """Sample blog post data for testing."""

    return {
        "title": "Test Blog Post",
        "slug": "test-blog-post",
        "content": "This is test content for our blog post.",
        "excerpt": "This is a test excerpt.",
        "published": True,
        "tags": ["test", "blog"],
        "author": "Test Author",
    }


@pytest.fixture
def sample_comment():
    """Sample comment data for testing."""

    return {
        "author_name": "Test Commenter",
        "email": "test@example.com",
        "content": "This is a test comment.",
        "consent_given": True,
    }


@pytest.fixture
def gdpr_test_data():
    """GDPR test data for compliance testing."""

    return {
        "consent_request": {
            "consent_type": "analytics",
            "consent_given": True,
            "consent_version": "1.0",
        },
        "data_subject_request": {
            "request_type": "access",
            "contact_email": "user@example.com",
            "description": "I want to see all my data",
        },
    }


# Test configuration
@pytest.fixture(autouse=True)
def test_environment():
    """Set up test environment variables."""

    os.environ.update(
        {
            "ENVIRONMENT": "testing",
            "DEBUG": "false",
            "SECRET_KEY": "test-secret-key",
            "DATABASE_URL": "sqlite:///:memory:",
            "GDPR_TEST_MODE": "true",
        }
    )


# Security test fixtures
@pytest.fixture
def security_headers():
    """Expected security headers for testing."""

    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
    }


@pytest.fixture
def malicious_payloads():
    """Common attack payloads for security testing."""

    return [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "../../../etc/passwd",
        "javascript:alert(1)",
        "${7*7}",  # Template injection
        "{{7*7}}",  # Jinja2 injection
    ]
