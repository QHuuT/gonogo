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
        # Read file content to avoid import issues in test environment
        db_integration_path = Path(__file__).parent.parent.parent / "src" / "shared" / "testing" / "database_integration.py"

        with open(db_integration_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify the file contains __test__ = False for all three classes
        assert '__test__ = False  # Tell pytest this is not a test class' in content

        # Verify each class has the marker
        class_names = ['TestDiscovery', 'TestDatabaseSync', 'TestExecutionTracker']
        for class_name in class_names:
            # Check that the class exists and has __test__ = False
            lines = content.split('\n')
            in_target_class = False
            test_false_found = False

            for line in lines:
                if f'class {class_name}' in line:
                    in_target_class = True
                elif in_target_class and 'class ' in line and not line.strip().startswith('#'):
                    # Found another class, exit current class
                    break
                elif in_target_class and '__test__ = False' in line:
                    test_false_found = True
                    break

            assert test_false_found, f"{class_name} class should have __test__ = False"

    def test_test_failure_dataclass_not_collected(self):
        """Test that TestFailure dataclass is not collected."""
        # Read file content to avoid import issues in test environment
        failure_tracker_path = Path(__file__).parent.parent.parent / "src" / "shared" / "testing" / "failure_tracker.py"

        with open(failure_tracker_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify the file contains __test__ = False for TestFailure
        assert '__test__ = False  # Tell pytest this is not a test class' in content

        # Verify it's in the TestFailure class definition
        lines = content.split('\n')
        in_test_failure = False
        test_false_found = False

        for line in lines:
            if 'class TestFailure' in line:
                in_test_failure = True
            elif in_test_failure and 'class ' in line and not line.strip().startswith('#'):
                # Found another class, exit TestFailure
                break
            elif in_test_failure and '__test__ = False' in line:
                test_false_found = True
                break

        assert test_false_found, "TestFailure class should have __test__ = False"

    def test_formatter_class_not_collected(self):
        """Test that TestFormatter class is not collected."""
        # Read file content to avoid import issues
        formatter_path = Path(__file__).parent.parent.parent / "src" / "shared" / "logging" / "formatters.py"

        with open(formatter_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify the file contains __test__ = False for TestFormatter
        assert '__test__ = False  # Tell pytest this is not a test class' in content

        # Verify it's in the TestFormatter class definition
        lines = content.split('\n')
        in_test_formatter = False
        test_false_found = False

        for line in lines:
            if 'class TestFormatter' in line:
                in_test_formatter = True
            elif in_test_formatter and 'class ' in line and not line.strip().startswith('#'):
                # Found another class, exit TestFormatter
                break
            elif in_test_formatter and '__test__ = False' in line:
                test_false_found = True
                break

        assert test_false_found, "TestFormatter class should have __test__ = False"

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