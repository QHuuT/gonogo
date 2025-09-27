"""
GitHub Action Runner for Issue Label Assignment

Integrates the GitHub Label Mapper with GitHub Actions environment
to automatically assign labels to issues based on template responses.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from github_label_mapper import GitHubIssueLabelMapper, IssueData

# Configure logging for GitHub Actions
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class GitHubActionError(Exception):
    """Custom exception for GitHub Action errors."""

    pass


class GitHubActionRunner:
    """Handles GitHub Action integration for automatic label assignment."""

    def __init__(self) -> None:
        """Initialize with GitHub Action environment variables."""
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repository = os.getenv("GITHUB_REPOSITORY")
        self.github_event_path = os.getenv("GITHUB_EVENT_PATH")

        if not all([self.github_token, self.github_repository, self.github_event_path]):
            raise GitHubActionError(
                "Missing required GitHub Action environment variables. "
                "Ensure GITHUB_TOKEN, GITHUB_REPOSITORY, and GITHUB_EVENT_PATH are set."
            )

        # Initialize label mapper
        matrix_path = Path("docs/traceability/requirements-matrix.md")
        self.label_mapper = GitHubIssueLabelMapper(matrix_path)

    def load_github_event(self) -> Dict[str, Any]:
        """Load GitHub event data from the event file."""
        try:
            if self.github_event_path is None:
                raise GitHubActionError("GitHub event path is not set")
            with open(self.github_event_path, "r", encoding="utf-8") as f:
                event_data: Dict[str, Any] = json.load(f)
            return event_data
        except FileNotFoundError:
            raise GitHubActionError(f"GitHub event file not found: {self.github_event_path}")
        except json.JSONDecodeError as e:
            raise GitHubActionError(f"Invalid JSON in GitHub event file: {e}")

    def extract_issue_data(self, event_data: Dict[str, Any]) -> Optional[IssueData]:
        """Extract issue information from GitHub event data."""
        try:
            issue = event_data.get("issue")
            if not issue:
                logger.info("No issue found in event data")
                return None

            # Extract existing labels
            existing_labels = [label["name"] for label in issue.get("labels", [])]

            issue_data = IssueData(
                title=issue.get("title", ""),
                body=issue.get("body", ""),
                existing_labels=existing_labels,
                issue_number=issue.get("number", 0),
            )

            logger.info(f"Extracted issue data for #{issue_data.issue_number}: {issue_data.title}")
            return issue_data

        except KeyError as e:
            logger.error(f"Missing expected field in issue data: {e}")
            return None

    def set_github_output(self, name: str, value: str) -> None:
        """Set GitHub Action output variable."""
        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a", encoding="utf-8") as f:
                f.write(f"{name}={value}\n")
        else:
            # Fallback for older GitHub Actions
            print(f"::set-output name={name}::{value}")

    def run(self) -> None:
        """Main execution method for the GitHub Action."""
        try:
            logger.info("Starting GitHub Issue Label Assignment")

            # Load event data
            event_data = self.load_github_event()
            logger.info(f"Loaded GitHub event: {event_data.get('action', 'unknown')}")

            # Extract issue data
            issue_data = self.extract_issue_data(event_data)
            if not issue_data:
                logger.info("No issue to process, exiting")
                self.set_github_output("labels_changed", "false")
                return

            # Generate labels
            original_labels = set(issue_data.existing_labels)
            new_labels = self.label_mapper.generate_labels(issue_data)
            new_labels_set = set(new_labels)

            # Check if labels changed
            if original_labels == new_labels_set:
                logger.info("No label changes needed")
                self.set_github_output("labels_changed", "false")
                return

            # Output results for GitHub Action
            labels_json = json.dumps(new_labels)
            self.set_github_output("new_labels", labels_json)
            self.set_github_output("labels_changed", "true")

            added_labels = new_labels_set - original_labels
            removed_labels = original_labels - new_labels_set

            if added_labels:
                logger.info(f"Labels to add: {sorted(added_labels)}")
                self.set_github_output("added_labels", json.dumps(sorted(added_labels)))

            if removed_labels:
                logger.info(f"Labels to remove: {sorted(removed_labels)}")
                self.set_github_output("removed_labels", json.dumps(sorted(removed_labels)))

            logger.info("GitHub Issue Label Assignment completed successfully")

        except Exception as e:
            logger.error(f"Error in GitHub Action runner: {e}")
            self.set_github_output("error", str(e))
            sys.exit(1)


def main() -> None:
    """Entry point for the GitHub Action."""
    try:
        runner = GitHubActionRunner()
        runner.run()
    except GitHubActionError as e:
        logger.error(f"GitHub Action configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
