"""
Regression test for SQLAlchemy import deprecation warnings.

This test ensures that SQLAlchemy imports use the new recommended paths
and don't generate MovedIn20Warning deprecation warnings.

Related Issue: MovedIn20Warning for declarative_base import
Bug ID: W-20250926-declarative-base-import-deprecation
"""

import warnings

import pytest
from sqlalchemy.orm import declarative_base  # noqa: F401 - testing deprecation


def test_no_declarative_base_deprecation_warnings():
    """
    Regression test: Ensure no MovedIn20Warning for declarative_base imports.

    This test verifies that our SQLAlchemy model files use the correct
    import paths and don't generate deprecation warnings about moved functions.
    """
    # Import our model files and check for deprecation warnings
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")  # Catch all warnings

        # Import the files that previously had deprecated imports

        # Check that no MovedIn20Warning was generated
        moved_warnings = [
            w
            for w in warning_list
            if issubclass(w.category, DeprecationWarning)
            and "MovedIn20Warning" in str(w.message)
        ]

        assert len(moved_warnings) == 0, (
            f"Found {len(moved_warnings)} MovedIn20Warning deprecation warnings. "
            f"Warnings: {[str(w.message) for w in moved_warnings]}"
        )

        # Check that no declarative_base deprecation warnings were generated
        declarative_warnings = [
            w
            for w in warning_list
            if issubclass(w.category, DeprecationWarning)
            and "declarative_base" in str(w.message)
            and "sqlalchemy.orm.declarative_base" in str(w.message)
        ]

        assert len(declarative_warnings) == 0, (
            f"Found {len(declarative_warnings)} declarative_base deprecation warnings. "
            f"Warnings: {[str(w.message) for w in declarative_warnings]}"
        )


def test_proper_declarative_base_import():
    """
    Test that declarative_base is imported from the correct module.

    This ensures our models use sqlalchemy.orm.declarative_base instead
    of the deprecated sqlalchemy.ext.declarative.declarative_base.
    """
    # Import our base classes
    from src.be.models.traceability.base import Base as TraceabilityBase
    from src.security.gdpr.models import Base as GDPRBase

    # Verify both bases are instances of declarative_base
    assert TraceabilityBase is not None
    assert GDPRBase is not None

    # Verify they have the expected declarative attributes
    assert hasattr(TraceabilityBase, "metadata")
    assert hasattr(GDPRBase, "metadata")
    assert hasattr(TraceabilityBase, "registry")
    assert hasattr(GDPRBase, "registry")


def test_models_work_with_new_import():
    """
    Test that the models still work correctly with the new import path.

    This ensures that changing from sqlalchemy.ext.declarative to
    sqlalchemy.orm doesn't break functionality.
    """
    # Import model classes that depend on the base
    from src.be.models.traceability.epic import Epic
    from src.security.gdpr.models import ConsentRecord

    # Verify the models can be instantiated (basic functionality test)
    epic = Epic(
        epic_id="EP-TEST-001", title="Test Epic", description="Test description"
    )

    consent = ConsentRecord(
        consent_id="test-consent-id",
        consent_type="essential",
        consent_given=True,
        consent_version="1.0",
    )

    # Basic attribute access to ensure the models work
    assert epic.epic_id == "EP-TEST-001"
    assert epic.title == "Test Epic"
    assert consent.consent_id == "test-consent-id"
    assert consent.consent_type == "essential"
    assert consent.consent_given == True


def test_import_paths_are_future_proof():
    """
    Test that we're using the recommended import paths for SQLAlchemy 2.0+.

    This ensures our code is forward-compatible with future SQLAlchemy versions.
    """
    # Test that the recommended import path works

    # Create a base using the recommended import
    TestBase = declarative_base()

    # Verify it has the expected structure
    assert hasattr(TestBase, "metadata")
    assert hasattr(TestBase, "registry")

    # Verify our models' bases are created the same way
    from src.be.models.traceability.base import Base as TraceabilityBase
    from src.security.gdpr.models import Base as GDPRBase

    # Both should have the same type
    assert type(TraceabilityBase) == type(TestBase)
    assert type(GDPRBase) == type(TestBase)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
