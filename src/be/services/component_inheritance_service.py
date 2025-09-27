"""
Component Inheritance Service

Handles automatic component inheritance from parent relationships in the RTM system.
Implements the component inheritance logic: Epic ← User Story → Defect/Test

Related Issue: US-00009 - Implement Component Inheritance System
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import logging
from typing import Dict, Optional

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.traceability.defect import Defect
from ..models.traceability.epic import Epic
from ..models.traceability.test import Test
from ..models.traceability.user_story import UserStory

logger = logging.getLogger(__name__)


class ComponentInheritanceService:
    """Service for managing component inheritance across RTM entities."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize with optional database session."""
        self.session = session or SessionLocal()
        self._should_close_session = session is None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with session cleanup."""
        if self._should_close_session:
            self.session.close()

    def inherit_defect_component(self, defect: Defect, force: bool = False) -> bool:
        """
        Inherit component for a defect from its parent User Story.

        Args:
            defect: The defect to update
            force: If True, override existing component

        Returns:
            True if component was inherited, False otherwise
        """
        if not force and defect.component is not None:
            logger.debug(
                f"Defect {defect.defect_id} already has component: {defect.component}"
            )
            return False

        if not defect.github_user_story_number:
            logger.debug(f"Defect {defect.defect_id} has no parent User Story")
            return False

        user_story = (
            self.session.query(UserStory)
            .filter(UserStory.github_issue_number == defect.github_user_story_number)
            .first()
        )

        if not user_story:
            logger.warning(
                (
    f"Defect {defect.defect_id} references "
    f"non-existent User Story #{defect.github_user_story_number}"
)
            )
            return False

        if not user_story.component:
            logger.debug(
                f"User Story {user_story.user_story_id} has no component to inherit"
            )
            return False

        old_component = defect.component
        defect.component = user_story.component

        logger.info(
            (
    f"Inherited component for "
    f"{defect.defect_id}: {old_component} → {defect.component}"
)
        )
        return True

    def inherit_test_component(self, test: Test, force: bool = False) -> bool:
        """
        Inherit component for a test from its parent User Story.

        Args:
            test: The test to update
            force: If True, override existing component

        Returns:
            True if component was inherited, False otherwise
        """
        if not force and test.component is not None:
            logger.debug(f"Test {test.id} already has component: {test.component}")
            return False

        if not test.github_user_story_number:
            logger.debug(f"Test {test.id} has no parent User Story")
            return False

        user_story = (
            self.session.query(UserStory)
            .filter(UserStory.github_issue_number == test.github_user_story_number)
            .first()
        )

        if not user_story:
            logger.warning(
                (
    f"Test {test.id} references "
    f"non-existent User Story #{test.github_user_story_number}"
)
            )
            return False

        if not user_story.component:
            logger.debug(
                f"User Story {user_story.user_story_id} has no component to inherit"
            )
            return False

        old_component = test.component
        test.component = user_story.component

        logger.info(
            f"Inherited component for test {test.id}: {old_component} → {test.component}"
        )
        return True

    def update_epic_components(self, epic: Epic) -> bool:
        """
        Update Epic components based on child User Stories.

        Args:
            epic: The epic to update

        Returns:
            True if components were updated, False otherwise
        """
        old_component = epic.component
        epic.update_component_from_user_stories()

        if old_component != epic.component:
            logger.info(
                f"Updated Epic {epic.epic_id} components: {old_component} → {epic.component}"
            )
            return True

        return False

    def process_all_defect_inheritance(self, force: bool = False) -> Dict[str, int]:
        """
        Process component inheritance for all defects.

        Args:
            force: If True, override existing components

        Returns:
            Dict with processing statistics
        """
        logger.info(f"Processing defect component inheritance (force={force})")

        stats = {
    
            "total_defects": 0,
            "defects_with_user_stories": 0,
            "inherited_successfully": 0,
            "inheritance_failures": 0,
            "already_had_component": 0,
        
}

        defects = self.session.query(Defect).all()
        stats["total_defects"] = len(defects)

        for defect in defects:
            if defect.github_user_story_number:
                stats["defects_with_user_stories"] += 1

                if not force and defect.component:
                    stats["already_had_component"] += 1
                    continue

                try:
                    if self.inherit_defect_component(defect, force=force):
                        stats["inherited_successfully"] += 1
                    else:
                        stats["inheritance_failures"] += 1
                except Exception as e:
                    logger.error(
                        f"Error inheriting component for {defect.defect_id}: {e}"
                    )
                    stats["inheritance_failures"] += 1

        return stats

    def process_all_test_inheritance(self, force: bool = False) -> Dict[str, int]:
        """
        Process component inheritance for all tests.

        Args:
            force: If True, override existing components

        Returns:
            Dict with processing statistics
        """
        logger.info(f"Processing test component inheritance (force={force})")

        stats = {
    
            "total_tests": 0,
            "tests_with_user_stories": 0,
            "inherited_successfully": 0,
            "inheritance_failures": 0,
            "already_had_component": 0,
        
}

        tests = self.session.query(Test).all()
        stats["total_tests"] = len(tests)

        for test in tests:
            if test.github_user_story_number:
                stats["tests_with_user_stories"] += 1

                if not force and test.component:
                    stats["already_had_component"] += 1
                    continue

                try:
                    if self.inherit_test_component(test, force=force):
                        stats["inherited_successfully"] += 1
                    else:
                        stats["inheritance_failures"] += 1
                except Exception as e:
                    logger.error(f"Error inheriting component for test {test.id}: {e}")
                    stats["inheritance_failures"] += 1

        return stats

    def process_all_epic_inheritance(self) -> Dict[str, int]:
        """
        Process component inheritance for all epics.

        Returns:
            Dict with processing statistics
        """
        logger.info("Processing epic component inheritance")

        stats = {"total_epics": 0, "epics_updated": 0, "epics_unchanged": 0}

        epics = self.session.query(Epic).all()
        stats["total_epics"] = len(epics)

        for epic in epics:
            try:
                if self.update_epic_components(epic):
                    stats["epics_updated"] += 1
                else:
                    stats["epics_unchanged"] += 1
            except Exception as e:
                logger.error(f"Error updating components for {epic.epic_id}: {e}")

        return stats

    def process_full_inheritance_chain(self, dry_run: bool = True) -> Dict[str, any]:
        """
        Process complete component inheritance chain.

        Args:
            dry_run: If True, don't commit changes to database

        Returns:
            Dict with complete processing results
        """
        logger.info(f"Processing full component inheritance chain (dry_run={dry_run})")

        results = {
            "dry_run": dry_run,
            "defect_stats": {},
            "test_stats": {},
            "epic_stats": {},
            "total_changes": 0,
        }

        try:
            # Process defects and tests first (inherit from User Stories)
            results["defect_stats"] = self.process_all_defect_inheritance(force=False)
            results["test_stats"] = self.process_all_test_inheritance(force=False)

            # Then process epics (inherit from User Stories)
            results["epic_stats"] = self.process_all_epic_inheritance()

            # Calculate total changes
            results["total_changes"] = (
                results["defect_stats"]["inherited_successfully"]
                + results["test_stats"]["inherited_successfully"]
                + results["epic_stats"]["epics_updated"]
            )

            if not dry_run:
                self.session.commit()
                logger.info(
                    f"Committed {results['total_changes']} component inheritance changes"
                )
            else:
                self.session.rollback()
                logger.info(
                    f"DRY RUN: Would commit {results['total_changes']} component inheritance changes"
                )

        except Exception as e:
            logger.error(f"Error during full inheritance processing: {e}")
            self.session.rollback()
            raise

        return results

    def validate_component_consistency(self) -> Dict[str, any]:
        """
        Validate component consistency across relationships.

        Returns:
            Dict with validation results
        """
        logger.info("Validating component consistency")

        results = {
    
            "total_inconsistencies": 0,
            "defect_inconsistencies": [],
            "test_inconsistencies": [],
            "epic_inconsistencies": [],
        
}

        # Check defects vs their User Stories
        defects = (
            self.session.query(Defect)
            .filter(
                Defect.github_user_story_number.isnot(None),
                Defect.component.isnot(None),
            )
            .all()
        )

        for defect in defects:
            user_story = (
                self.session.query(UserStory)
                .filter(
                    UserStory.github_issue_number == defect.github_user_story_number
                )
                .first()
            )

            if (
                user_story
                and user_story.component
                and defect.component != user_story.component
            ):
                inconsistency = {
    
                    "defect_id": defect.defect_id,
                    "defect_component": defect.component,
                    "user_story_id": user_story.user_story_id,
                    "user_story_component": user_story.component,
                
}
                results["defect_inconsistencies"].append(inconsistency)
                results["total_inconsistencies"] += 1

        # Check tests vs their User Stories
        tests = (
            self.session.query(Test)
            .filter(
                Test.github_user_story_number.isnot(None), Test.component.isnot(None)
            )
            .all()
        )

        for test in tests:
            user_story = (
                self.session.query(UserStory)
                .filter(UserStory.github_issue_number == test.github_user_story_number)
                .first()
            )

            if (
                user_story
                and user_story.component
                and test.component != user_story.component
            ):
                inconsistency = {
    
                    "test_id": test.id,
                    "test_component": test.component,
                    "user_story_id": user_story.user_story_id,
                    "user_story_component": user_story.component,
                
}
                results["test_inconsistencies"].append(inconsistency)
                results["total_inconsistencies"] += 1

        logger.info(
            f"Found {results['total_inconsistencies']} component inconsistencies"
        )
        return results


# Convenience functions for direct use


def inherit_all_components(dry_run: bool = True) -> Dict[str, any]:
    """Convenience function to process all component inheritance."""
    with ComponentInheritanceService() as service:
        return service.process_full_inheritance_chain(dry_run=dry_run)


def validate_component_consistency() -> Dict[str, any]:
    """Convenience function to validate component consistency."""
    with ComponentInheritanceService() as service:
        return service.validate_component_consistency()


def inherit_defect_components(force: bool = False) -> Dict[str, int]:
    """Convenience function to inherit defect components."""
    with ComponentInheritanceService() as service:
        return service.process_all_defect_inheritance(force=force)


def inherit_test_components(force: bool = False) -> Dict[str, int]:
    """Convenience function to inherit test components."""
    with ComponentInheritanceService() as service:
        return service.process_all_test_inheritance(force=force)
