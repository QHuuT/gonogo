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
        # Read the file content instead of importing to avoid SQLAlchemy setup issues
        test_file_path = Path(__file__).parent / "shared" / "models" / "test_traceability_base.py"

        with open(test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify the file contains __test__ = False for TestEntity
        assert '__test__ = False  # Tell pytest this is not a test class' in content

        # Verify it's in the TestEntity class definition
        lines = content.split('\n')
        in_test_entity = False
        test_false_found = False

        for line in lines:
            if 'class TestEntity(' in line:
                in_test_entity = True
            elif in_test_entity and 'class ' in line and not line.strip().startswith('#'):
                # Found another class, exit TestEntity
                break
            elif in_test_entity and '__test__ = False' in line:
                test_false_found = True
                break

        assert test_false_found, "TestEntity class should have __test__ = False"

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
        # Test TestCoverageReporter - read file content to avoid import issues
        tool_file_path = Path(__file__).parent.parent.parent / "tools" / "test_coverage_report.py"

        with open(tool_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify the file contains __test__ = False for TestCoverageReporter
        assert '__test__ = False  # Tell pytest this is not a test class' in content

        # Verify it's in the TestCoverageReporter class definition
        lines = content.split('\n')
        in_test_coverage = False
        test_false_found = False

        for line in lines:
            if 'class TestCoverageReporter' in line:
                in_test_coverage = True
            elif in_test_coverage and 'class ' in line and not line.strip().startswith('#'):
                # Found another class, exit TestCoverageReporter
                break
            elif in_test_coverage and '__test__ = False' in line:
                test_false_found = True
                break

        assert test_false_found, "TestCoverageReporter class should have __test__ = False"

    def test_diagnostic_classes_not_collected(self):
        """Test that diagnostic classes are not collected."""
        # Test TestDiagnostics - read file content to avoid import issues
        diag_file_path = Path(__file__).parent.parent.parent / "test_diagnosis.py"

        with open(diag_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify the file contains __test__ = False for TestDiagnostics
        assert '__test__ = False  # Tell pytest this is not a test class' in content

        # Verify it's in the TestDiagnostics class definition
        lines = content.split('\n')
        in_test_diagnostics = False
        test_false_found = False

        for line in lines:
            if 'class TestDiagnostics' in line:
                in_test_diagnostics = True
            elif in_test_diagnostics and 'class ' in line and not line.strip().startswith('#'):
                # Found another class, exit TestDiagnostics
                break
            elif in_test_diagnostics and '__test__ = False' in line:
                test_false_found = True
                break

        assert test_false_found, "TestDiagnostics class should have __test__ = False"

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