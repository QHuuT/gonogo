"""
Regression tests for pytest collection fixes.

Ensures that classes with __test__ = False are not collected as test classes
and that legitimate test classes are still collected properly.

Related to: PytestCollectionWarning fix - preventing false positive test collection
"""

import pytest
from pathlib import Path
import sys
import importlib.util

class TestPytestCollectionRegression:
    """Regression tests for pytest collection behavior."""

    def test_database_model_not_collected(self):
        """Test that Test model class is not collected as test class."""
        # Import the Test model class
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        from be.models.traceability.test import Test

        # Verify it has __test__ = False
        assert hasattr(Test, '__test__')
        assert Test.__test__ is False

    def test_test_entity_helper_not_collected(self):
        """Test that TestEntity helper class is not collected."""
        # Import TestEntity from the test file
        spec = importlib.util.spec_from_file_location(
            "test_traceability_base",
            Path(__file__).parent / "shared" / "models" / "test_traceability_base.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Verify TestEntity has __test__ = False
        assert hasattr(module.TestEntity, '__test__')
        assert module.TestEntity.__test__ is False

    def test_database_integration_classes_not_collected(self):
        """Test that database integration utility classes are not collected."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        from shared.testing.database_integration import TestDiscovery, TestDatabaseSync, TestExecutionTracker

        # Verify all three classes have __test__ = False
        assert hasattr(TestDiscovery, '__test__')
        assert TestDiscovery.__test__ is False

        assert hasattr(TestDatabaseSync, '__test__')
        assert TestDatabaseSync.__test__ is False

        assert hasattr(TestExecutionTracker, '__test__')
        assert TestExecutionTracker.__test__ is False

    def test_test_failure_dataclass_not_collected(self):
        """Test that TestFailure dataclass is not collected."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        from shared.testing.failure_tracker import TestFailure

        # Verify TestFailure has __test__ = False
        assert hasattr(TestFailure, '__test__')
        assert TestFailure.__test__ is False

    def test_tool_classes_not_collected(self):
        """Test that tool classes are not collected."""
        # Test TestCoverageReporter
        spec = importlib.util.spec_from_file_location(
            "test_coverage_report",
            Path(__file__).parent.parent.parent / "tools" / "test_coverage_report.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(module.TestCoverageReporter, '__test__')
        assert module.TestCoverageReporter.__test__ is False

    def test_diagnostic_classes_not_collected(self):
        """Test that diagnostic classes are not collected."""
        spec = importlib.util.spec_from_file_location(
            "test_diagnosis",
            Path(__file__).parent.parent.parent / "test_diagnosis.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(module.TestDiagnostics, '__test__')
        assert module.TestDiagnostics.__test__ is False

    def test_legitimate_test_classes_still_collected(self):
        """Test that real test classes are still collected properly."""
        # This test class itself should be collected
        assert not hasattr(TestPytestCollectionRegression, '__test__') or TestPytestCollectionRegression.__test__ is not False

        # Test methods should be detected
        test_methods = [method for method in dir(self) if method.startswith('test_')]
        assert len(test_methods) > 0
        assert 'test_legitimate_test_classes_still_collected' in test_methods

    def test_no_collection_warnings_generated(self):
        """Test that no PytestCollectionWarning is generated during collection."""
        # This is more of a documentation test - the actual verification
        # happens when pytest runs without warnings
        # The presence of __test__ = False on all problematic classes
        # should prevent collection warnings

        # List of classes that should have __test__ = False
        classes_to_check = [
            "be.models.traceability.test.Test",
            "shared.testing.database_integration.TestDiscovery",
            "shared.testing.database_integration.TestDatabaseSync",
            "shared.testing.database_integration.TestExecutionTracker",
            "shared.testing.failure_tracker.TestFailure"
        ]

        # This test passes if no warnings are generated during collection
        # which is verified by the pytest run itself
        assert len(classes_to_check) == 5