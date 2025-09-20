"""
BDD test configuration and fixtures for pytest-bdd.
"""

import pytest
from pytest_bdd import given, when, then, parsers
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.be.main import app
from src.security.gdpr.models import Base


@pytest.fixture(scope="session")
def bdd_test_client():
    """Test client for BDD scenarios."""
    return TestClient(app)


@pytest.fixture(scope="session")
def bdd_database():
    """In-memory database for BDD tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def bdd_context():
    """Shared context for BDD scenarios."""
    return {
        "user_data": {},
        "responses": {},
        "consents": {},
        "comments": {},
        "current_user": None,
        "current_page": None,
        "gdpr_enabled": True
    }


# Common Background Steps
@given("the blog application is running")
def blog_app_running(bdd_test_client):
    """Verify the blog application is accessible."""
    response = bdd_test_client.get("/health")
    assert response.status_code == 200


@given("GDPR compliance is enabled")
def gdpr_compliance_enabled(bdd_context):
    """Set GDPR compliance mode."""
    bdd_context["gdpr_enabled"] = True


@given("the database contains sample blog posts")
def sample_blog_posts(bdd_database, bdd_context):
    """Create sample blog posts in the database."""
    # This would create sample posts in the database
    # For now, we'll mock this in the context
    bdd_context["sample_posts"] = [
        {
            "id": 1,
            "title": "Sample Blog Post",
            "content": "This is sample content for testing.",
            "published": True
        },
        {
            "id": 2,
            "title": "GDPR Compliance Guide",
            "content": "Understanding GDPR requirements for blogs.",
            "published": True
        }
    ]