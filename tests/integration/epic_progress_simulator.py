"""
Epic Progress Calculator Simulator for testing.

Simulates the Epic progress calculation logic from the GitHub Actions workflow
without requiring actual GitHub events.

Related Issue: US-00056 - GitHub Actions database integration
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

from src.be.models.traceability import Epic, UserStory


class EpicProgressCalculatorSimulator:
    """Simulates Epic progress calculation for testing."""

    def __init__(self, issue_number: int = 1):
        """Initialize simulator with optional issue number."""
        self.issue_number = issue_number

    def calculate_epic_progress(self, db, epic: Epic) -> float:
        """Calculate Epic completion percentage based on linked User Stories."""
        try:
            # Get all User Stories linked to this Epic
            user_stories = (
                db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
            )

            if not user_stories:
                return 0.0

            total_story_points = sum(us.story_points for us in user_stories)
            completed_story_points = sum(
                us.story_points
                for us in user_stories
                if us.implementation_status == "done"
            )

            if total_story_points == 0:
                # If no story points, use count-based calculation
                total_count = len(user_stories)
                completed_count = len(
                    [us for us in user_stories if us.implementation_status == "done"]
                )
                progress = (completed_count / total_count) * 100
            else:
                # Use story points for calculation
                progress = (completed_story_points / total_story_points) * 100

            return progress

        except Exception:
            return epic.completion_percentage or 0.0

    def update_affected_epics(self, db):
        """Update progress for all Epics that might be affected by this issue change."""
        try:
            # Find the User Story that corresponds to this issue
            user_story = (
                db.query(UserStory)
                .filter(UserStory.github_issue_number == self.issue_number)
                .first()
            )

            if not user_story:
                return

            # Find the Epic linked to this User Story
            if not user_story.epic_id:
                return

            epic = db.query(Epic).filter(Epic.id == user_story.epic_id).first()
            if not epic:
                return

            # Update progress for the Epic
            new_progress = self.calculate_epic_progress(db, epic)

            # Update Epic progress in database
            epic.completion_percentage = new_progress

            # Update Epic status based on progress
            if new_progress >= 100:
                epic.status = "completed"
            elif new_progress > 0:
                epic.status = "in_progress"
            else:
                epic.status = "planned"

            db.commit()

        except Exception:
            db.rollback()
