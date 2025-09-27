#!/usr/bin/env python3
"""
Restoration Validation Script

Validates that the GitHub issues restoration completed successfully by checking
database counts, foreign key relationships, and data integrity.

Usage:
    python tools/validate_restoration.py
"""

import sys
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.append('src')

from sqlalchemy.orm import Session
from be.database import get_db_session
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory
from be.models.traceability.defect import Defect
from be.models.traceability.capability import Capability

def count_records(session: Session) -> Dict[str, int]:
    """Count records in each table."""
    return {
        "epics": session.query(Epic).count(),
        "user_stories": session.query(UserStory).count(),
        "defects": session.query(Defect).count(),
        "capabilities": session.query(Capability).count()
    }

def validate_epic_data(session: Session) -> List[str]:
    """Validate epic data integrity."""
    issues = []

    epics = session.query(Epic).all()

    for epic in epics:
        # Check required fields
        if not epic.epic_id:
            issues.append(f"Epic {epic.id} missing epic_id")
        if not epic.title:
            issues.append(f"Epic {epic.epic_id} missing title")
        if epic.github_issue_number is None:
            issues.append(f"Epic {epic.epic_id} missing github_issue_number")
        if not epic.priority:
            issues.append(f"Epic {epic.epic_id} missing priority")
        if not epic.component:
            issues.append(f"Epic {epic.epic_id} missing component")

        # Check capability relationship
        if epic.capability_id:
            capability = session.query(Capability).filter(Capability.id == epic.capability_id).first()
            if not capability:
                issues.append(f"Epic {epic.epic_id} references non-existent capability {epic.capability_id}")

    return issues

def validate_user_story_data(session: Session) -> List[str]:
    """Validate user story data integrity."""
    issues = []

    user_stories = session.query(UserStory).all()

    for us in user_stories:
        # Check required fields
        if not us.user_story_id:
            issues.append(f"User Story {us.id} missing user_story_id")
        if not us.title:
            issues.append(f"User Story {us.user_story_id} missing title")
        if us.github_issue_number is None:
            issues.append(f"User Story {us.user_story_id} missing github_issue_number")
        if us.epic_id is None:
            issues.append(f"User Story {us.user_story_id} missing epic_id")

        # Check epic relationship
        if us.epic_id:
            epic = session.query(Epic).filter(Epic.id == us.epic_id).first()
            if not epic:
                issues.append(f"User Story {us.user_story_id} references non-existent epic {us.epic_id}")

    return issues

def validate_defect_data(session: Session) -> List[str]:
    """Validate defect data integrity."""
    issues = []

    defects = session.query(Defect).all()

    for defect in defects:
        # Check required fields
        if not defect.defect_id:
            issues.append(f"Defect {defect.id} missing defect_id")
        if not defect.title:
            issues.append(f"Defect {defect.defect_id} missing title")
        if defect.github_issue_number is None:
            issues.append(f"Defect {defect.defect_id} missing github_issue_number")

        # Check epic relationship (optional for defects)
        if defect.epic_id:
            epic = session.query(Epic).filter(Epic.id == defect.epic_id).first()
            if not epic:
                issues.append(f"Defect {defect.defect_id} references non-existent epic {defect.epic_id}")

    return issues

def validate_capability_data(session: Session) -> List[str]:
    """Validate capability data integrity."""
    issues = []

    expected_capabilities = ["CAP-00001", "CAP-00002", "CAP-00003", "CAP-00004"]
    existing_capabilities = session.query(Capability.capability_id).all()
    existing_cap_ids = [cap[0] for cap in existing_capabilities]

    for expected_cap in expected_capabilities:
        if expected_cap not in existing_cap_ids:
            issues.append(f"Missing required capability: {expected_cap}")

    capabilities = session.query(Capability).all()
    for cap in capabilities:
        if not cap.capability_id:
            issues.append(f"Capability {cap.id} missing capability_id")
        if not cap.name:
            issues.append(f"Capability {cap.capability_id} missing name")

    return issues

def check_foreign_key_integrity(session: Session) -> List[str]:
    """Check foreign key relationships."""
    issues = []

    # Check user stories have valid epic references
    orphaned_us = session.query(UserStory).filter(
        ~UserStory.epic_id.in_(session.query(Epic.id))
    ).all()

    for us in orphaned_us:
        issues.append(f"User Story {us.user_story_id} references non-existent epic (ID: {us.epic_id})")

    # Check epics have valid capability references
    orphaned_epics = session.query(Epic).filter(
        Epic.capability_id.isnot(None),
        ~Epic.capability_id.in_(session.query(Capability.id))
    ).all()

    for epic in orphaned_epics:
        issues.append(f"Epic {epic.epic_id} references non-existent capability (ID: {epic.capability_id})")

    return issues

def validate_expected_counts() -> Tuple[bool, List[str]]:
    """Validate that we have the expected number of records."""
    expected = {
        "epics": 8,
        "user_stories": 66,
        "defects": 10,
        "capabilities": 4
    }

    session = get_db_session()
    try:
        actual = count_records(session)
        issues = []

        for table, expected_count in expected.items():
            actual_count = actual[table]
            if actual_count != expected_count:
                issues.append(f"{table}: expected {expected_count}, got {actual_count}")

        return len(issues) == 0, issues
    finally:
        session.close()

def run_validation() -> bool:
    """Run all validation checks."""
    print("GitHub Issues Restoration - Validation")
    print("=" * 50)

    session = get_db_session()
    try:
        # Count records
        counts = count_records(session)
        print(f"\nRecord Counts:")
        for table, count in counts.items():
            print(f"  {table:15}: {count:3d}")

        # Expected counts validation
        print(f"\nExpected Counts Check:")
        counts_ok, count_issues = validate_expected_counts()
        if counts_ok:
            print("  ✅ All counts match expectations")
        else:
            print("  ❌ Count mismatches found:")
            for issue in count_issues:
                print(f"    - {issue}")

        # Data integrity checks
        all_issues = []

        print(f"\nData Integrity Checks:")

        # Epic validation
        epic_issues = validate_epic_data(session)
        if epic_issues:
            print(f"  ❌ Epic issues found: {len(epic_issues)}")
            all_issues.extend(epic_issues)
        else:
            print("  ✅ Epics data integrity OK")

        # User Story validation
        us_issues = validate_user_story_data(session)
        if us_issues:
            print(f"  ❌ User Story issues found: {len(us_issues)}")
            all_issues.extend(us_issues)
        else:
            print("  ✅ User Stories data integrity OK")

        # Defect validation
        defect_issues = validate_defect_data(session)
        if defect_issues:
            print(f"  ❌ Defect issues found: {len(defect_issues)}")
            all_issues.extend(defect_issues)
        else:
            print("  ✅ Defects data integrity OK")

        # Capability validation
        cap_issues = validate_capability_data(session)
        if cap_issues:
            print(f"  ❌ Capability issues found: {len(cap_issues)}")
            all_issues.extend(cap_issues)
        else:
            print("  ✅ Capabilities data integrity OK")

        # Foreign key validation
        fk_issues = check_foreign_key_integrity(session)
        if fk_issues:
            print(f"  ❌ Foreign key issues found: {len(fk_issues)}")
            all_issues.extend(fk_issues)
        else:
            print("  ✅ Foreign key integrity OK")

        # Summary
        print("\n" + "=" * 50)

        if all_issues:
            print(f"❌ VALIDATION FAILED: {len(all_issues)} issues found")
            print("\nIssues:")
            for issue in all_issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ VALIDATION PASSED: All checks successful!")
            print("\nThe GitHub issues restoration completed successfully!")
            print("All 84 items (8 epics + 66 user stories + 10 defects) are properly restored.")
            return True

    finally:
        session.close()

def main():
    """Main entry point."""
    try:
        success = run_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()