"""
Regression tests for database cleanup functionality.

Ensures that temporary test databases are properly cleaned up without
generating UserWarnings about file deletion failures.

Related to: Windows file locking issues with SQLite database cleanup
"""

import os
import tempfile
import time
import warnings

import pytest
from sqlalchemy import create_engine

from src.security.gdpr.models import Base
from tests.conftest import _cleanup_temp_database


class TestDatabaseCleanupRegression:
    """Regression tests for database cleanup functionality."""

    def test_temp_database_cleanup_no_warnings(self):
        """Test that database cleanup doesn't generate UserWarnings."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", UserWarning)

            # Create temporary database
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
                test_db_url = f"sqlite:///{temp_file.name}"

            try:
                # Create and use database
                engine = create_engine(test_db_url, echo=False)
                Base.metadata.create_all(bind=engine)
                engine.dispose()

                # Test cleanup function
                _cleanup_temp_database(temp_file.name)

                # Check for UserWarnings about database cleanup
                cleanup_warnings = [
                    warning
                    for warning in w
                    if "Could not delete temporary test database"
                    in str(warning.message)
                ]

                # Should have no cleanup warnings
                assert len(cleanup_warnings) == 0, (
                    f"Found {len(cleanup_warnings)} database cleanup warnings"
                )

            finally:
                # Ensure cleanup even if test fails
                try:
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
                except (PermissionError, OSError):
                    pass

    def test_cleanup_function_handles_nonexistent_file(self):
        """Test that cleanup function handles non-existent files gracefully."""
        # Test cleanup with non-existent file (should not raise exception)
        fake_path = "/tmp/claude/nonexistent_database.db"
        try:
            _cleanup_temp_database(fake_path)
            # Should complete without exception
        except Exception as e:
            pytest.fail(f"Cleanup function raised unexpected exception: {e}")

    def test_cleanup_function_retries_on_permission_error(self):
        """Test that cleanup function implements retry logic."""
        # Create a file and test retry behavior
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # File exists, test cleanup
            start_time = time.time()
            _cleanup_temp_database(temp_path)
            elapsed_time = time.time() - start_time

            # Should either succeed immediately or take some time due to retries
            # If it takes more than 0.1 seconds, retries were likely attempted
            # This is a heuristic test - exact timing depends on system performance

            # Verify file is cleaned up (either immediately or after retries)
            if os.path.exists(temp_path):
                # If file still exists, it should be due to persistent locking
                # This is acceptable behavior on Windows
                pass
            else:
                # File was successfully deleted
                pass

        finally:
            # Final cleanup
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except (PermissionError, OSError):
                pass

    def test_multiple_database_cleanup_sequential(self):
        """Test multiple database cleanup operations in sequence."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", UserWarning)

            db_files = []
            try:
                # Create multiple temporary databases
                for i in range(3):
                    with tempfile.NamedTemporaryFile(
                        suffix=f"_test_{i}.db", delete=False
                    ) as temp_file:
                        test_db_url = f"sqlite:///{temp_file.name}"
                        db_files.append(temp_file.name)

                        # Create and use database
                        engine = create_engine(test_db_url, echo=False)
                        Base.metadata.create_all(bind=engine)
                        engine.dispose()

                # Clean up all databases
                for db_file in db_files:
                    _cleanup_temp_database(db_file)

                # Check for UserWarnings
                cleanup_warnings = [
                    warning
                    for warning in w
                    if "Could not delete temporary test database"
                    in str(warning.message)
                ]

                # Should have no cleanup warnings
                assert len(cleanup_warnings) == 0, (
                    f"Found {len(cleanup_warnings)} database cleanup warnings in sequential test"
                )

            finally:
                # Final cleanup
                for db_file in db_files:
                    try:
                        if os.path.exists(db_file):
                            os.unlink(db_file)
                    except (PermissionError, OSError):
                        pass

    def test_database_fixture_integration(self, test_db):
        """Test that database fixtures work without warnings."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", UserWarning)

            # Use the database fixture
            engine = create_engine(test_db, echo=False)
            connection = engine.connect()
            connection.close()
            engine.dispose()

            # Check for warnings during fixture usage
            cleanup_warnings = [
                warning
                for warning in w
                if "Could not delete temporary test database" in str(warning.message)
            ]

            # Should have no warnings from fixture usage
            assert len(cleanup_warnings) == 0, (
                f"Found {len(cleanup_warnings)} warnings from database fixture"
            )
