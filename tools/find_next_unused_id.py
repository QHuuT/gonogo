#!/usr/bin/env python3
"""
Find the next unused ID for epics, user stories, or defects in the RTM database.

Usage:
    python tools/find_next_unused_id.py --type user-story
    python tools/find_next_unused_id.py --type epic
    python tools/find_next_unused_id.py --type defect
"""

import argparse
import re
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.be.database import get_db_session
from src.be.models.traceability import Defect, Epic, UserStory


def get_existing_ids(entity_type: str) -> set[int]:
    """Get all existing IDs for the given entity type from database."""
    db = get_db_session()

    try:
        if entity_type == "epic":
            entities = db.query(Epic).all()
            id_pattern = r"EP-(\d+)"
            id_field = "epic_id"
        elif entity_type == "user-story":
            entities = db.query(UserStory).all()
            id_pattern = r"US-(\d+)"
            id_field = "user_story_id"
        elif entity_type == "defect":
            entities = db.query(Defect).all()
            id_pattern = r"DEF-(\d+)"
            id_field = "defect_id"
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")

        existing_ids = set()
        for entity in entities:
            id_value = getattr(entity, id_field)
            match = re.match(id_pattern, id_value)
            if match:
                existing_ids.add(int(match.group(1)))

        return existing_ids

    finally:
        db.close()


def find_next_unused_id(entity_type: str) -> str:
    """Find the next unused ID for the given entity type."""
    existing_ids = get_existing_ids(entity_type)

    # Find the lowest unused number starting from 1
    next_id = 1
    while next_id in existing_ids:
        next_id += 1

    # Format according to type
    if entity_type == "epic":
        return f"EP-{next_id:05d}"
    elif entity_type == "user-story":
        return f"US-{next_id:05d}"
    elif entity_type == "defect":
        return f"DEF-{next_id:05d}"


def main():
    parser = \
        argparse.ArgumentParser(description="Find next unused ID for RTM entities")
    parser.add_argument(
        "--type",
        choices=["epic", "user-story", "defect"],
        required=True,
        help="Type of entity to find next ID for",
    )
    parser.add_argument(
        "--show-gaps", action="store_true", help="Show all gaps in ID sequence"
    )

    args = parser.parse_args()

    if args.show_gaps:
        existing_ids = get_existing_ids(args.type)
        if existing_ids:
            max_id = max(existing_ids)
            all_ids = set(range(1, max_id + 1))
            gaps = sorted(all_ids - existing_ids)

            print(f"Existing {args.type} IDs: {sorted(existing_ids)}")
            print(f"Gaps in sequence: {gaps}")
            print(f"Next unused ID: {find_next_unused_id(args.type)}")
        else:
            print(f"No {args.type} entities found in database")
    else:
        next_id = find_next_unused_id(args.type)
        print(next_id)


if __name__ == "__main__":
    main()
