"""
Database Integration for Test Execution Tracking.

Integrates test execution results with the RTM database system to provide
automatic traceability between tests and requirements.

Related Issue: US-00057 - Test execution integration with database
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from be.database import get_db_session
from be.models.traceability import Defect, Epic, Test, UserStory


class TestDiscovery:
    """Discovers and analyzes test files for database integration."""

    def __init__(self):
        self.test_patterns = {
            "unit": ["tests/unit/**/*.py"],
            "integration": ["tests/integration/**/*.py"],
            "e2e": ["tests/e2e/**/*.py"],
            "security": ["tests/security/**/*.py"],
            "bdd": ["tests/bdd/**/*.py"],
        }

        self.epic_pattern = re.compile(r"EP-(\d{5})")
        self.user_story_pattern = re.compile(r"US-(\d{5})")
        self.defect_pattern = re.compile(r"DEF-(\d{5})")

    def discover_tests(self, root_dir: Path = None) -> List[Dict]:
        """
        Discover all test files and extract metadata.

        Returns:
            List of test metadata dictionaries
        """
        if root_dir is None:
            root_dir = Path.cwd()

        discovered_tests = []

        for test_type, patterns in self.test_patterns.items():
            for pattern in patterns:
                test_files = list(root_dir.glob(pattern))
                for test_file in test_files:
                    if test_file.is_file() and test_file.name.startswith("test_"):
                        test_metadata = self._analyze_test_file(test_file, test_type)
                        if test_metadata:
                            discovered_tests.extend(test_metadata)

        return discovered_tests

    def _analyze_test_file(self, test_file: Path, test_type: str) -> List[Dict]:
        """Analyze a single test file and extract test functions."""
        try:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST to find test functions
            tree = ast.parse(content)
            test_functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    # Handle file path - for temp files, use absolute path
                    try:
                        file_path = str(test_file.relative_to(Path.cwd()))
                    except ValueError:
                        # File is not in current directory (e.g., temp file)
                        file_path = str(test_file)

                    test_metadata = {
                        "test_file_path": file_path,
                        "test_function_name": node.name,
                        "test_type": test_type,
                        "title": self._generate_test_title(node.name),
                        "line_number": node.lineno,
                        "epic_references": self._extract_epic_references(content),
                        "user_story_references": self._extract_user_story_references(
                            content
                        ),
                        "defect_references": self._extract_defect_references(content),
                        "bdd_scenario_name": self._extract_bdd_scenario_name(
                            node, content
                        ),
                    }
                    test_functions.append(test_metadata)

            return test_functions

        except Exception as e:
            print(f"Warning: Could not analyze {test_file}: {e}")
            return []

    def _generate_test_title(self, function_name: str) -> str:
        """Generate human-readable title from test function name."""
        # Convert test_function_name to "Test Function Name"
        title = function_name.replace("test_", "").replace("_", " ").title()
        return f"Test: {title}"

    def _extract_epic_references(self, content: str) -> List[str]:
        """Extract Epic references from test file content."""
        return [f"EP-{match}" for match in self.epic_pattern.findall(content)]

    def _extract_user_story_references(self, content: str) -> List[str]:
        """Extract User Story references from test file content."""
        return [f"US-{match}" for match in self.user_story_pattern.findall(content)]

    def _extract_defect_references(self, content: str) -> List[str]:
        """Extract Defect references from test file content."""
        return [f"DEF-{match}" for match in self.defect_pattern.findall(content)]

    def _extract_bdd_scenario_name(
        self, node: ast.FunctionDef, content: str
    ) -> Optional[str]:
        """Extract BDD scenario name if this is a BDD test."""
        # Look for pytest-bdd scenario decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if hasattr(decorator.func, "id") and decorator.func.id == "scenario":
                    # Extract scenario name from decorator
                    if decorator.args and isinstance(decorator.args[-1], ast.Constant):
                        return decorator.args[-1].value
        return None


class TestDatabaseSync:
    """Synchronizes discovered tests with the database."""

    def __init__(self):
        self.discovery = TestDiscovery()

    def sync_tests_to_database(self) -> Dict[str, int]:
        """
        Sync discovered tests to database.

        Returns:
            Dictionary with sync statistics
        """
        db = get_db_session()
        try:
            discovered_tests = self.discovery.discover_tests()

            stats = {
                "discovered": len(discovered_tests),
                "created": 0,
                "updated": 0,
                "linked_to_epics": 0,
                "errors": 0,
            }

            for test_data in discovered_tests:
                try:
                    result = self._create_or_update_test(db, test_data)
                    if result == "created":
                        stats["created"] += 1
                    elif result == "updated":
                        stats["updated"] += 1

                    # Link to Epic if references found
                    if test_data["epic_references"]:
                        if self._link_test_to_epic(db, test_data):
                            stats["linked_to_epics"] += 1

                except Exception as e:
                    print(f"Error syncing test {test_data['test_function_name']}: {e}")
                    stats["errors"] += 1

            db.commit()
            return stats

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def _create_or_update_test(self, db, test_data: Dict) -> str:
        """Create or update a test record in the database."""
        existing_test = (
            db.query(Test)
            .filter(
                Test.test_file_path == test_data["test_file_path"],
                Test.test_function_name == test_data["test_function_name"],
            )
            .first()
        )

        if existing_test:
            # Update existing test
            existing_test.title = test_data["title"]
            existing_test.test_type = test_data["test_type"]
            existing_test.bdd_scenario_name = test_data["bdd_scenario_name"]
            return "updated"
        else:
            # Create new test
            test = Test(
                test_type=test_data["test_type"],
                test_file_path=test_data["test_file_path"],
                title=test_data["title"],
                test_function_name=test_data["test_function_name"],
                bdd_scenario_name=test_data["bdd_scenario_name"],
                description=f"Auto-discovered test from {test_data['test_file_path']}:{test_data['line_number']}",
            )
            db.add(test)
            return "created"

    def _link_test_to_epic(self, db, test_data: Dict) -> bool:
        """Link test to Epic based on references found in test code."""
        if not test_data["epic_references"]:
            return False

        # Use the first Epic reference found
        epic_id = test_data["epic_references"][0]
        epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()

        if epic:
            # Update the test with Epic link
            test = (
                db.query(Test)
                .filter(
                    Test.test_file_path == test_data["test_file_path"],
                    Test.test_function_name == test_data["test_function_name"],
                )
                .first()
            )

            if test:
                test.epic_id = epic.id
                return True

        return False


class TestExecutionTracker:
    """Tracks test execution results and updates database."""

    def __init__(self):
        self.db_session = None

    def start_test_session(self):
        """Initialize database session for test execution tracking."""
        self.db_session = get_db_session()

    def end_test_session(self):
        """Close database session and commit changes."""
        if self.db_session:
            try:
                self.db_session.commit()
            except Exception as e:
                self.db_session.rollback()
                print(f"Error committing test execution results: {e}")
            finally:
                self.db_session.close()
                self.db_session = None

    def record_test_result(
        self,
        test_id: str,
        status: str,
        duration_ms: float = None,
        error_message: str = None,
    ) -> bool:
        """
        Record test execution result in database.

        Args:
            test_id: Test identifier (file::function format)
            status: Test status (passed, failed, skipped)
            duration_ms: Test execution duration in milliseconds
            error_message: Error message if test failed

        Returns:
            True if recorded successfully, False otherwise
        """
        if not self.db_session:
            return False

        try:
            # Parse test_id to extract file and function
            parts = test_id.split("::")
            if len(parts) < 2:
                return False

            test_file = parts[0]
            test_function = parts[-1]

            # Find test in database
            test = (
                self.db_session.query(Test)
                .filter(
                    Test.test_file_path == test_file,
                    Test.test_function_name == test_function,
                )
                .first()
            )

            if test:
                test.update_execution_result(status, duration_ms, error_message)
                return True

        except Exception as e:
            print(f"Error recording test result for {test_id}: {e}")

        return False

    def create_defect_from_failure(
        self, test_id: str, failure_message: str, stack_trace: str
    ) -> Optional[str]:
        """
        Create a defect record from test failure.

        Args:
            test_id: Test identifier
            failure_message: Failure message
            stack_trace: Full stack trace

        Returns:
            Defect ID if created successfully, None otherwise
        """
        if not self.db_session:
            return None

        try:
            # Find related test
            parts = test_id.split("::")
            if len(parts) < 2:
                return None

            test_file = parts[0]
            test_function = parts[-1]

            test = (
                self.db_session.query(Test)
                .filter(
                    Test.test_file_path == test_file,
                    Test.test_function_name == test_function,
                )
                .first()
            )

            if not test:
                return None

            # Generate defect ID
            defect_count = self.db_session.query(Defect).count()
            defect_id = f"DEF-{defect_count + 1:05d}"

            # Generate a placeholder GitHub issue number (will be updated when actual issue is created)
            github_issue_number = (
                900000 + defect_count + 1
            )  # Start from 900001 for test failures

            # Create defect
            defect = Defect(
                defect_id=defect_id,
                github_issue_number=github_issue_number,
                title=f"Test Failure: {test_function}",
                description=f"Test failure in {test_file}\n\nFailure Message:\n{failure_message}\n\nStack Trace:\n{stack_trace}",
                severity=self._determine_failure_severity(failure_message),
                priority="medium",
                status="open",
                defect_type="test_failure",
                test_id=test.id,
                epic_id=test.epic_id,
            )

            self.db_session.add(defect)
            return defect_id

        except Exception as e:
            print(f"Error creating defect from test failure {test_id}: {e}")
            return None

    def _determine_failure_severity(self, failure_message: str) -> str:
        """Determine defect severity based on failure message."""
        failure_lower = failure_message.lower()

        if any(keyword in failure_lower for keyword in ["assertion", "assert"]):
            return "medium"
        elif any(keyword in failure_lower for keyword in ["import", "module"]):
            return "high"
        elif any(
            keyword in failure_lower for keyword in ["security", "auth", "permission"]
        ):
            return "critical"
        else:
            return "low"


class BDDScenarioParser:
    """Parses BDD feature files and links scenarios to User Stories."""

    def __init__(self):
        self.scenario_pattern = re.compile(r"^\s*Scenario:?\s*(.+)$", re.MULTILINE)
        self.user_story_pattern = re.compile(r"US-(\d{5})")

    def parse_feature_files(self, root_dir: Path = None) -> List[Dict]:
        """
        Parse all BDD feature files and extract scenarios.

        Returns:
            List of scenario metadata dictionaries
        """
        if root_dir is None:
            root_dir = Path.cwd()

        feature_files = list(root_dir.glob("tests/bdd/features/**/*.feature"))
        scenarios = []

        for feature_file in feature_files:
            try:
                with open(feature_file, "r", encoding="utf-8") as f:
                    content = f.read()

                scenarios.extend(self._parse_feature_content(feature_file, content))

            except Exception as e:
                print(f"Warning: Could not parse {feature_file}: {e}")

        return scenarios

    def _parse_feature_content(self, feature_file: Path, content: str) -> List[Dict]:
        """Parse content of a single feature file."""
        scenarios = []
        scenario_matches = self.scenario_pattern.finditer(content)

        for match in scenario_matches:
            scenario_name = match.group(1).strip()
            scenario_line = content[: match.start()].count("\n") + 1

            # Extract User Story references from surrounding context
            user_story_refs = self._extract_user_story_context(content, match.start())

            # Handle file path - for temp files, use absolute path
            try:
                file_path = str(feature_file.relative_to(Path.cwd()))
            except ValueError:
                # File is not in current directory (e.g., temp file)
                file_path = str(feature_file)

            scenario_data = {
                "feature_file": file_path,
                "scenario_name": scenario_name,
                "line_number": scenario_line,
                "user_story_references": user_story_refs,
                "test_type": "bdd",
            }
            scenarios.append(scenario_data)

        return scenarios

    def _extract_user_story_context(self, content: str, position: int) -> List[str]:
        """Extract User Story references from context around scenario."""
        # Look in the first 500 characters before the scenario
        context_start = max(0, position - 500)
        context = content[context_start : position + 200]

        return [f"US-{match}" for match in self.user_story_pattern.findall(context)]

    def link_scenarios_to_user_stories(self) -> Dict[str, int]:
        """
        Link BDD scenarios to User Stories in database.

        Returns:
            Dictionary with linking statistics
        """
        db = get_db_session()
        try:
            scenarios = self.parse_feature_files()

            stats = {
                "scenarios_found": len(scenarios),
                "scenarios_linked": 0,
                "user_stories_updated": 0,
                "errors": 0,
            }

            for scenario in scenarios:
                try:
                    if scenario["user_story_references"]:
                        if self._link_scenario_to_user_story(db, scenario):
                            stats["scenarios_linked"] += 1
                            stats["user_stories_updated"] += 1

                except Exception as e:
                    print(f"Error linking scenario {scenario['scenario_name']}: {e}")
                    stats["errors"] += 1

            db.commit()
            return stats

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def _link_scenario_to_user_story(self, db, scenario: Dict) -> bool:
        """Link a scenario to its referenced User Story."""
        if not scenario["user_story_references"]:
            return False

        # Use first User Story reference
        us_id = scenario["user_story_references"][0]
        user_story = (
            db.query(UserStory).filter(UserStory.user_story_id == us_id).first()
        )

        if user_story:
            # Create or update test record for this scenario
            test = (
                db.query(Test)
                .filter(
                    Test.test_file_path == scenario["feature_file"],
                    Test.bdd_scenario_name == scenario["scenario_name"],
                )
                .first()
            )

            if not test:
                test = Test(
                    test_type="bdd",
                    test_file_path=scenario["feature_file"],
                    title=f"BDD: {scenario['scenario_name']}",
                    bdd_scenario_name=scenario["scenario_name"],
                    epic_id=user_story.epic_id,
                    description=f"BDD scenario from {scenario['feature_file']}:{scenario['line_number']}",
                )
                db.add(test)
            else:
                test.epic_id = user_story.epic_id

            return True

        return False
