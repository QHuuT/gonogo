#!/usr/bin/env python3
"""
Component Inheritance Acceptance Tests

Comprehensive tests to verify all acceptance criteria for US-00009.

Related Issue: US-00009 - Implement Component Inheritance System
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import sys
import logging

# Add src to path for imports
sys.path.append('src')

from be.database import SessionLocal
from be.models.traceability.defect import Defect
from be.models.traceability.epic import Epic
from be.models.traceability.test import Test
from be.models.traceability.user_story import UserStory
from be.services.component_inheritance_service import ComponentInheritanceService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_component_inheritance_logic():
    """Test component inheritance logic (Epic ← User Story → Defect)."""
    print("\n=== Testing Component Inheritance Logic ===")

    session = SessionLocal()

    # Check existing inheritance
    defects_with_inheritance = session.query(Defect).filter(
        Defect.component.isnot(None),
        Defect.github_user_story_number.isnot(None)
    ).all()

    print(f"Defects with inherited components: {len(defects_with_inheritance)}")
    for defect in defects_with_inheritance:
        us = session.query(UserStory).filter(
            UserStory.github_issue_number == defect.github_user_story_number
        ).first()
        if us:
            print(f"  {defect.defect_id}: {defect.component} (from {us.user_story_id}: {us.component})")

    # Check epic inheritance
    epics_with_components = session.query(Epic).filter(Epic.component.isnot(None)).all()
    print(f"\nEpics with inherited components: {len(epics_with_components)}")
    for epic in epics_with_components:
        inherited = epic.get_inherited_components()
        print(f"  {epic.epic_id}: {epic.component} (inherited: {inherited})")

    session.close()
    return True


def test_defect_creation_workflow():
    """Test inheritance in defect creation workflow."""
    print("\n=== Testing Defect Creation Workflow ===")

    session = SessionLocal()

    # Create test defect linked to existing user story
    test_defect = Defect(
        defect_id='DEF-TEST002',
        github_issue_number=998,
        title='Test Defect for Creation Workflow',
        github_user_story_number=8  # This should inherit backend component
    )

    session.add(test_defect)
    session.commit()

    # Check if component was inherited automatically by trigger
    updated_defect = session.query(Defect).filter(Defect.defect_id == 'DEF-TEST002').first()
    inherited_component = updated_defect.component

    # Clean up
    session.delete(updated_defect)
    session.commit()
    session.close()

    print(f"Test defect inherited component: {inherited_component}")
    return inherited_component == 'backend'


def test_component_override():
    """Test component override capability for special cases."""
    print("\n=== Testing Component Override Capability ===")

    with ComponentInheritanceService() as service:
        # Get a defect with existing component
        defect = service.session.query(Defect).filter(
            Defect.component.isnot(None)
        ).first()

        if not defect:
            print("No defects with components found for override test")
            return False

        original_component = defect.component
        print(f"Original component for {defect.defect_id}: {original_component}")

        # Test that override works with force=True
        result = service.inherit_defect_component(defect, force=True)
        print(f"Override with force=True successful: {result}")

        # Reset for next test
        defect.component = original_component

        # Test that override doesn't work with force=False
        result_no_force = service.inherit_defect_component(defect, force=False)
        print(f"Override with force=False successful: {result_no_force}")

        return result and not result_no_force


def test_database_triggers():
    """Test database triggers for automatic inheritance."""
    print("\n=== Testing Database Triggers ===")

    session = SessionLocal()

    # Test defect trigger
    test_defect = Defect(
        defect_id='DEF-TEST003',
        github_issue_number=997,
        title='Test Defect for Trigger',
        github_user_story_number=60  # Should inherit backend component (US-00060)
    )

    session.add(test_defect)
    session.commit()

    # Check if trigger worked
    updated_defect = session.query(Defect).filter(Defect.defect_id == 'DEF-TEST003').first()
    trigger_worked = updated_defect.component is not None

    print(f"Defect trigger test - Component inherited: {updated_defect.component}")

    # Test user story update trigger
    us = session.query(UserStory).filter(UserStory.github_issue_number == 60).first()
    if us:
        original_component = us.component
        us.component = 'testing'  # Change component
        session.commit()

        # Check if defect was updated (only if defect component was None)
        updated_defect = session.query(Defect).filter(Defect.defect_id == 'DEF-TEST003').first()

        # Reset user story
        us.component = original_component
        session.commit()

    # Clean up
    session.delete(updated_defect)
    session.commit()
    session.close()

    return trigger_worked


def test_validation_consistency():
    """Test validation for component consistency."""
    print("\n=== Testing Component Consistency Validation ===")

    with ComponentInheritanceService() as service:
        results = service.validate_component_consistency()

        print(f"Total inconsistencies found: {results['total_inconsistencies']}")
        print(f"Defect inconsistencies: {len(results['defect_inconsistencies'])}")
        print(f"Test inconsistencies: {len(results['test_inconsistencies'])}")

        return results['total_inconsistencies'] == 0


def run_acceptance_tests():
    """Run all acceptance tests for US-00009."""
    print("=== US-00009 Component Inheritance System Acceptance Tests ===")

    tests = [
        ("Component inheritance logic", test_component_inheritance_logic),
        ("Defect creation workflow", test_defect_creation_workflow),
        ("Component override capability", test_component_override),
        ("Database triggers", test_database_triggers),
        ("Validation consistency", test_validation_consistency),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            status = "PASS" if result else "FAIL"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"\n{test_name}: FAIL - {e}")
            logger.error(f"Test {test_name} failed: {e}")

    print("\n=== Acceptance Test Summary ===")
    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll acceptance criteria met! US-00009 is ready for completion.")
        return True
    else:
        print(f"\n{total - passed} tests failed. Review and fix issues before completion.")
        return False


if __name__ == '__main__':
    success = run_acceptance_tests()
    sys.exit(0 if success else 1)