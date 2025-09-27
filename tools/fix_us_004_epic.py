#!/usr/bin/env python3
"""
Fix US-00004 Epic Relationship Bug

US-00004 has epic_id="EP-00005" (string) but should be epic_id=6 (integer FK to epics.id)
"""

import sys

sys.path.append("src")

from be.database import SessionLocal
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory


def fix_us_004_epic():
    session = SessionLocal()

    print("=== Fix US-00004 Epic Relationship ===\n")

    # Get US-00004
    us_004 = (
        session.query(UserStory).filter(UserStory.user_story_id == "US-00004").first()
    )

    if not us_004:
        print("US-00004 not found")
        return

    print("Current state:")
    print(f"  US-00004 epic_id: {us_004.epic_id} (type: {type(us_004.epic_id)})")

    # Get Epic EP-00005
    epic_005 = session.query(Epic).filter(Epic.epic_id == "EP-00005").first()

    if not epic_005:
        print("Epic EP-00005 not found")
        return

    print(f"  Epic EP-00005 database id: {epic_005.id}")

    # Fix the foreign key
    print("\nFixing foreign key...")
    us_004.epic_id = epic_005.id

    # Verify the fix
    session.flush()  # Make sure the change is available for querying

    if us_004.epic:
        print(f"✅ Fixed! US-00004 now linked to: {us_004.epic.epic_id}")
    else:
        print("❌ Fix failed - relationship still broken")
        return

    # Commit the change
    session.commit()
    print("✅ Changes committed to database")

    session.close()


if __name__ == "__main__":
    fix_us_004_epic()
