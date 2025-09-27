"""
Pytest configuration and shared fixtures for GoNoGo blog tests.
Following testing pyramid: Unit > Integration > E2E
"""

import gc
import os
import tempfile
import time
import warnings
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.be.main import app
from src.security.gdpr.models import Base

# Load custom test runner plugin
pytest_plugins = ["tools.test_runner_plugin"]


def _cleanup_temp_database(db_path: str) -> None:
    """
    Enhanced temporary database cleanup with robust Windows file locking handling.

    Uses multiple strategies to ensure database files are properly cleaned up:
    1. Force garbage collection to release Python references
    2. Multiple retry attempts with increasing delays
    3. Graceful degradation with informative logging
    """
    # Force garbage collection to release any remaining Python references
    gc.collect()

    max_retries = 5
    base_delay = 0.1

    for attempt in range(max_retries):
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
                return  # Success - file deleted
            else:
                return  # File doesn't exist - nothing to clean up
        except PermissionError:
            if attempt < max_retries - 1:
                # Calculate exponential backoff delay
                delay = base_delay * (2**attempt)
                time.sleep(delay)
                continue
            else:
                # Final attempt failed - this is expected occasionally on Windows
                # Use a more specific and less alarming log message
                import logging

                logger = logging.getLogger(__name__)
                logger.debug(
                    f"Temporary database cleanup deferred (Windows file locking): {os.path.basename(db_path)}"
                )

                # Only register for cleanup at exit if we absolutely can't delete now
                import atexit

                atexit.register(_delayed_cleanup, db_path)
                return
        except (OSError, FileNotFoundError):
            # File already deleted or other OS-level issue
            return


def _delayed_cleanup(db_path: str) -> None:
    """Attempt cleanup at program exit when file locks should be released."""
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except (PermissionError, OSError, FileNotFoundError):
        # Silently ignore - OS will clean up temp files eventually
        pass


def pytest_configure(config):
    """Configure pytest to filter external dependency warnings."""
    # Only apply filters if FILTER_EXTERNAL_WARNINGS environment variable is set
    if os.getenv("FILTER_EXTERNAL_WARNINGS", "false").lower() == "true":
        # Filter out external dependency warnings while keeping our code warnings
        warnings.filterwarnings(
            "ignore", ".*datetime.utcnow.*", DeprecationWarning, "sqlalchemy.*"
        )
        warnings.filterwarnings(
            "ignore",
            ".*asyncio_default_fixture_loop_scope.*",
            module="pytest_asyncio.*",
        )
        warnings.filterwarnings("ignore", ".*", DeprecationWarning, "site-packages.*")


def pytest_configure(config):
    """Register custom markers for RTM traceability."""
    config.addinivalue_line(
        "markers",
        "user_story(id): mark test as linked to user story (US-XXXXX). Can specify multiple.",
    )
    config.addinivalue_line(
        "markers",
        "epic(id): mark test as linked to epic (EP-XXXXX). Can specify multiple.",
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
        "markers",
        "test_type(type): categorizes tests by type (unit, integration, etc.)",
    )
    config.addinivalue_line(
        "markers", "detailed: marks tests for detailed debugging mode"
    )
    config.addinivalue_line(
        "markers", "smoke: marks tests as smoke tests (critical functionality)"
    )
    config.addinivalue_line("markers", "functional: marks tests as functional tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "gdpr: marks tests as GDPR compliance tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "bdd: marks tests as BDD scenarios")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers",
        "test_category(category): categorizes tests by specific category (smoke, performance, etc.)",
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

            # Enhanced cleanup with retry logic for Windows file locking
            _cleanup_temp_database(temp_file.name)


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
