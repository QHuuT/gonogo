#!/usr/bin/env python3
"""
Check Empty Fields in Database

Shows which database fields are empty and could potentially be populated
from GitHub issue content.
"""

import sys
sys.path.append('src')

from be.database import SessionLocal
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory
from be.models.traceability.defect import Defect

def check_empty_fields():
    """Check which fields are empty across all entities."""
    session = SessionLocal()

    try:
        print("=== Empty Field Analysis ===\n")

        # Check User Stories
        print("User Stories:")
        user_stories = session.query(UserStory).all()
        if user_stories:
            empty_counts = {}
            for us in user_stories:
                for field in ['business_value', 'acceptance_criteria', 'sprint', 'target_release_version',
                             'gdpr_considerations', 'depends_on_issues', 'blocks_issues', 'bdd_feature_files']:
                    value = getattr(us, field, None)
                    if not value or value in ['[]', '{}', '', 'None']:
                        empty_counts[field] = empty_counts.get(field, 0) + 1

            print(f"  Total User Stories: {len(user_stories)}")
            for field, count in sorted(empty_counts.items()):
                print(f"  {field}: {count}/{len(user_stories)} empty ({count/len(user_stories)*100:.1f}%)")
        else:
            print("  No user stories found")

        print()

        # Check Defects
        print("Defects:")
        defects = session.query(Defect).all()
        if defects:
            empty_counts = {}
            for defect in defects:
                for field in ['steps_to_reproduce', 'expected_behavior', 'actual_behavior', 'resolution_details',
                             'root_cause', 'environment', 'browser_version', 'os_version', 'estimated_hours',
                             'actual_hours', 'found_in_phase', 'customer_impact_details', 'gdpr_impact_details']:
                    value = getattr(defect, field, None)
                    if not value or value in ['[]', '{}', '', 'None']:
                        empty_counts[field] = empty_counts.get(field, 0) + 1

            print(f"  Total Defects: {len(defects)}")
            for field, count in sorted(empty_counts.items()):
                print(f"  {field}: {count}/{len(defects)} empty ({count/len(defects)*100:.1f}%)")
        else:
            print("  No defects found")

        print()

        # Check Epics
        print("Epics:")
        epics = session.query(Epic).all()
        if epics:
            empty_counts = {}
            for epic in epics:
                for field in ['business_value', 'success_criteria', 'gdpr_considerations']:
                    value = getattr(epic, field, None)
                    if not value or value in ['[]', '{}', '', 'None']:
                        empty_counts[field] = empty_counts.get(field, 0) + 1

            print(f"  Total Epics: {len(epics)}")
            for field, count in sorted(empty_counts.items()):
                print(f"  {field}: {count}/{len(epics)} empty ({count/len(epics)*100:.1f}%)")
        else:
            print("  No epics found")

    finally:
        session.close()

if __name__ == '__main__':
    check_empty_fields()