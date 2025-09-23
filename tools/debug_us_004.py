#!/usr/bin/env python3
"""
Debug US-00004 Epic Relationship Issue
"""

import sys
sys.path.append('src')

from be.database import SessionLocal
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory

def debug_us_004():
    session = SessionLocal()

    print("=== DEBUG US-00004 Epic Relationship ===\n")

    # Get US-00004 directly
    us_004 = session.query(UserStory).filter(
        UserStory.user_story_id == 'US-00004'
    ).first()

    if us_004:
        print(f"US-00004 Database Record:")
        print(f"  user_story_id: {us_004.user_story_id}")
        print(f"  github_issue_number: {us_004.github_issue_number}")
        print(f"  epic_id (FK): {us_004.epic_id}")
        print(f"  component: {us_004.component}")

        # Check if epic relationship works
        if us_004.epic_id:
            print(f"\nEpic Relationship:")
            epic = session.query(Epic).filter(Epic.id == us_004.epic_id).first()
            if epic:
                print(f"  Epic found: {epic.epic_id}")
                print(f"  Epic title: {epic.title}")
                print(f"  Epic component: {epic.component}")
            else:
                print(f"  Epic with id={us_004.epic_id} NOT FOUND in database")

        # Check via relationship
        print(f"\nRelationship Access:")
        try:
            epic_via_relationship = us_004.epic
            if epic_via_relationship:
                print(f"  us_004.epic: {epic_via_relationship.epic_id}")
            else:
                print(f"  us_004.epic: None (relationship returns None)")
        except Exception as e:
            print(f"  ❌ Error accessing us_004.epic: {e}")

    else:
        print("❌ US-00004 not found in database")

    # Also check all User Stories with their epic relationships
    print(f"\n=== All User Stories Epic Relationships ===")
    all_us = session.query(UserStory).order_by(UserStory.user_story_id).all()

    for us in all_us:
        epic_info = "None"
        if us.epic_id:
            try:
                if us.epic:
                    epic_info = f"{us.epic.epic_id}"
                else:
                    epic_info = f"BROKEN FK: epic_id={us.epic_id} (epic not found)"
            except:
                epic_info = f"ERROR: epic_id={us.epic_id}"

        print(f"  {us.user_story_id} (#{us.github_issue_number}): epic_id={us.epic_id} -> {epic_info}")

    session.close()

if __name__ == "__main__":
    debug_us_004()