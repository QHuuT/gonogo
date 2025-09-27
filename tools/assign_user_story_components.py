#!/usr/bin/env python3
"""
Manual User Story Component Assignment Tool

Allows manual assignment of components to user stories.
"""

import sys

sys.path.append("src")

from be.database import SessionLocal
from be.models.traceability.user_story import UserStory


def list_missing_components():
    """List user stories that need component assignment."""
    session = SessionLocal()

    print("=== User Stories Missing Components ===\n")

    us_missing = session.query(UserStory).filter(UserStory.component.is_(None)).all()

    for us in us_missing:
        epic_info = f"Epic: {us.epic.epic_id}" if us.epic else "No Epic"
        print(f"{us.user_story_id} (#{us.github_issue_number}): {epic_info}")
        if us.epic:
            print(f"  Available components: {us.epic.component}")
        print()

    session.close()
    return len(us_missing)


def assign_component(user_story_id: str, component: str, dry_run: bool = True):
    """Assign a component to a user story."""
    session = SessionLocal()

    try:
        us = (
            session.query(UserStory)
            .filter(UserStory.user_story_id == user_story_id)
            .first()
        )

        if not us:
            print(f"❌ User story {user_story_id} not found")
            return False

        print(f"Assigning component '{component}' to {user_story_id}")

        if not dry_run:
            us.component = component
            session.commit()
            print("✅ Component assigned successfully")
        else:
            print(f"🔍 DRY RUN - Would assign component '{component}'")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def interactive_assignment():
    """Interactive component assignment."""
    print("=== Interactive Component Assignment ===\n")

    # Available components
    components = [
        "frontend",
        "backend",
        "database",
        "security",
        "testing",
        "ci-cd",
        "documentation",
    ]

    while True:
        # List missing components
        missing_count = list_missing_components()
        if missing_count == 0:
            print("✅ All user stories have components assigned!")
            break

        print("Available components:")
        for i, comp in enumerate(components, 1):
            print(f"  {i}. {comp}")
        print("  0. Exit")

        # Get user story
        us_id = input("\nEnter User Story ID (e.g., US-00003) or '0' to exit: ").strip()
        if us_id == "0":
            break

        # Get component choice
        try:
            comp_choice = int(input("Enter component number: "))
            if comp_choice == 0:
                break
            if 1 <= comp_choice <= len(components):
                component = components[comp_choice - 1]

                # Confirm
                confirm = (
                    input(f"Assign '{component}' to {us_id}? (y/n): ").strip().lower()
                )
                if confirm == "y":
                    assign_component(us_id, component, dry_run=False)
                    print()
            else:
                print("Invalid component number")
        except ValueError:
            print("Invalid input")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Assign components to user stories")
    parser.add_argument(
        "--list", action="store_true", help="List user stories missing components"
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Interactive assignment mode"
    )
    parser.add_argument("--user-story", help="User story ID to assign component to")
    parser.add_argument("--component", help="Component to assign")
    parser.add_argument(
        "--dry-run", action="store_true", default=True, help="Dry run mode (default)"
    )
    parser.add_argument("--execute", action="store_true", help="Execute the assignment")

    args = parser.parse_args()

    if args.list:
        list_missing_components()
    elif args.interactive:
        interactive_assignment()
    elif args.user_story and args.component:
        dry_run = args.dry_run and not args.execute
        assign_component(args.user_story, args.component, dry_run)
    else:
        print("Usage examples:")
        print("  python assign_user_story_components.py --list")
        print("  python assign_user_story_components.py --interactive")
        print(
            "  python assign_user_story_components.py --user-story US-00003 --component backend --execute"
        )


if __name__ == "__main__":
    main()
