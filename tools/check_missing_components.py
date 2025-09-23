#!/usr/bin/env python3
"""
Quick tool to check which entities are missing components
"""

import sys
sys.path.append('src')

from be.database import SessionLocal
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory
from be.models.traceability.defect import Defect
from be.models.traceability.test import Test

def check_missing_components():
    session = SessionLocal()

    print("=== MISSING COMPONENTS ANALYSIS ===\n")

    # Check User Stories
    print("User Stories missing components:")
    us_missing = session.query(UserStory).filter(
        UserStory.component.is_(None)
    ).all()

    for us in us_missing:
        epic_info = f"Epic: {us.epic.epic_id} (component: {us.epic.component})" if us.epic else "No Epic"
        print(f"  {us.user_story_id} (#{us.github_issue_number}): {epic_info}")
    print(f"Total: {len(us_missing)}/37 user stories missing components\n")

    # Check Defects
    print("Defects missing components:")
    def_missing = session.query(Defect).filter(
        Defect.component.is_(None)
    ).all()

    for defect in def_missing:
        epic_info = f"Epic: {defect.epic.epic_id} (component: {defect.epic.component})" if defect.epic else "No Epic"
        print(f"  {defect.defect_id} (#{defect.github_issue_number}): {epic_info}")
    print(f"Total: {len(def_missing)}/9 defects missing components\n")

    # Check Tests
    print("Tests missing components:")
    test_missing = session.query(Test).filter(
        Test.component.is_(None)
    ).all()

    # Sample first 10
    for test in test_missing[:10]:
        epic_info = f"Epic: {test.epic.epic_id} (component: {test.epic.component})" if test.epic else "No Epic"
        print(f"  {test.test_file_path}: {epic_info}")

    if len(test_missing) > 10:
        print(f"  ... and {len(test_missing) - 10} more")
    print(f"Total: {len(test_missing)}/433 tests missing components\n")

    session.close()

if __name__ == "__main__":
    check_missing_components()