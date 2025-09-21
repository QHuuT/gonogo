#!/usr/bin/env python3
"""
GitHub Issue Creation for Test Failures

Automated GitHub issue creation from test failures with pre-filled context,
logs, environment information, and reproduction guides.

Related to: US-00027 GitHub issue creation integration for test failures
Parent Epic: EP-00006 Test Logging and Reporting
"""

import json
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .failure_tracker import FailureTracker
from .log_failure_correlator import FailureContext, LogFailureCorrelator


@dataclass
class IssueCreationResult:
    """Result of GitHub issue creation."""

    success: bool
    issue_number: Optional[int]
    issue_url: Optional[str]
    error_message: Optional[str]
    labels_applied: List[str]
    auto_assigned: bool


@dataclass
class IssueTemplate:
    """Template for GitHub issue creation from test failure."""

    title: str
    body: str
    labels: List[str]
    assignees: List[str]
    template_type: str  # 'defect', 'flaky-test', 'infrastructure'


class TestFailureIssueCreator:
    """Service for creating GitHub issues from test failures."""

    def __init__(
        self,
        correlator: Optional[LogFailureCorrelator] = None,
        owner: str = "QHuuT",
        repo: str = "gonogo",
    ):
        """Initialize the issue creator."""
        self.correlator = correlator or LogFailureCorrelator()
        self.owner = owner
        self.repo = repo

        # Validate GitHub CLI access
        self._validate_github_cli()

    def _validate_github_cli(self) -> bool:
        """Validate GitHub CLI is available and authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise RuntimeError("GitHub CLI not authenticated. Run 'gh auth login'")
            return True
        except FileNotFoundError:
            raise RuntimeError(
                "GitHub CLI not installed. Install from https://cli.github.com/"
            )

    def create_issue_from_failure(
        self, failure_id: int, auto_assign: bool = True, dry_run: bool = False
    ) -> IssueCreationResult:
        """
        Create a GitHub issue from a test failure.

        Args:
            failure_id: ID of the failure in the failure tracking database
            auto_assign: Whether to auto-assign the issue
            dry_run: If True, generate template but don't create issue

        Returns:
            Result of issue creation with details
        """
        # Get failure context
        context = self.correlator.correlate_failure_with_logs(failure_id)
        if not context:
            return IssueCreationResult(
                success=False,
                issue_number=None,
                issue_url=None,
                error_message=f"No context found for failure ID {failure_id}",
                labels_applied=[],
                auto_assigned=False,
            )

        # Generate issue template
        template = self._generate_issue_template(context)

        if dry_run:
            # Save template to file for review
            output_path = Path("quality/reports") / f"issue_template_{failure_id}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# Issue Template (Dry Run)\n\n")
                f.write(f"**Title:** {template.title}\n\n")
                f.write(f"**Labels:** {', '.join(template.labels)}\n\n")
                f.write(f"**Template Type:** {template.template_type}\n\n")
                f.write(f"**Body:**\n\n{template.body}")

            return IssueCreationResult(
                success=True,
                issue_number=None,
                issue_url=str(output_path),
                error_message=None,
                labels_applied=template.labels,
                auto_assigned=auto_assign,
            )

        # Create the GitHub issue
        return self._create_github_issue(template, auto_assign)

    def create_batch_issues_from_failures(
        self, failure_ids: List[int], auto_assign: bool = True, dry_run: bool = False
    ) -> List[IssueCreationResult]:
        """
        Create GitHub issues for multiple failures.

        Args:
            failure_ids: List of failure IDs to create issues for
            auto_assign: Whether to auto-assign issues
            dry_run: If True, generate templates but don't create issues

        Returns:
            List of issue creation results
        """
        results = []

        for failure_id in failure_ids:
            try:
                result = self.create_issue_from_failure(
                    failure_id, auto_assign, dry_run
                )
                results.append(result)

                # Brief pause between creations to avoid rate limiting
                if not dry_run and result.success:
                    import time

                    time.sleep(1)

            except Exception as e:
                results.append(
                    IssueCreationResult(
                        success=False,
                        issue_number=None,
                        issue_url=None,
                        error_message=f"Exception creating issue for failure {failure_id}: {str(e)}",
                        labels_applied=[],
                        auto_assigned=False,
                    )
                )

        return results

    def get_recent_failure_candidates(
        self, days: int = 7, min_occurrences: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get recent failures that are candidates for GitHub issue creation.

        Args:
            days: Number of days to look back
            min_occurrences: Minimum failure occurrences to consider

        Returns:
            List of failure candidates with metadata
        """
        # Use correlator to get recent failures
        recent_failures = self.correlator._get_recent_failures(days)

        candidates = []
        for failure in recent_failures:
            # Filter by occurrence count
            if failure.get("occurrence_count", 0) >= min_occurrences:
                # Check if already has a GitHub issue
                if not self._has_existing_issue(failure):
                    candidates.append(
                        {
                            "failure_id": failure["id"],
                            "test_name": failure["test_name"],
                            "category": failure["category"],
                            "severity": failure["severity"],
                            "occurrence_count": failure["occurrence_count"],
                            "last_seen": failure["last_seen"],
                            "recommended_labels": self._get_recommended_labels(failure),
                        }
                    )

        # Sort by severity and occurrence count
        candidates.sort(
            key=lambda x: (
                x["severity"] == "critical",
                x["severity"] == "high",
                x["occurrence_count"],
            ),
            reverse=True,
        )

        return candidates

    def _generate_issue_template(self, context: FailureContext) -> IssueTemplate:
        """Generate GitHub issue template from failure context."""
        # Determine issue type and labels
        labels = self._determine_labels(context)
        template_type = self._determine_template_type(context)

        # Generate title
        title = self._generate_issue_title(context)

        # Generate body
        body = self._generate_issue_body(context)

        # Determine assignees
        assignees = self._determine_assignees(context)

        return IssueTemplate(
            title=title,
            body=body,
            labels=labels,
            assignees=assignees,
            template_type=template_type,
        )

    def _determine_labels(self, context: FailureContext) -> List[str]:
        """Determine appropriate labels based on failure context."""
        labels = ["defect", "automated-issue"]

        # Add category-based labels
        category_labels = {
            "assertion_error": "test-failure",
            "import_error": "dependencies",
            "unicode_error": "encoding",
            "timeout_error": "performance",
            "network_error": "infrastructure",
            "database_error": "database",
            "permission_error": "infrastructure",
        }

        failure_message = context.failure_message.lower()
        for category, label in category_labels.items():
            if (
                category in failure_message
                or category.replace("_", " ") in failure_message
            ):
                labels.append(label)
                break

        # Add priority labels based on severity and occurrences
        if "critical" in failure_message or "fatal" in failure_message:
            labels.append("priority/high")
        elif len(context.related_failures) >= 3:
            labels.append("priority/medium")
        else:
            labels.append("priority/low")

        # Add component labels based on test file path
        if "test_authentication" in context.test_name:
            labels.append("component/auth")
        elif "test_gdpr" in context.test_name:
            labels.append("component/gdpr")
        elif "test_database" in context.test_name:
            labels.append("component/database")
        elif "/unit/" in context.test_name:
            labels.append("component/testing")
        elif "/integration/" in context.test_name:
            labels.append("component/integration")

        return labels

    def _determine_template_type(self, context: FailureContext) -> str:
        """Determine the type of issue template to use."""
        if len(context.related_failures) >= 3:
            return "flaky-test"
        elif (
            "timeout" in context.failure_message.lower()
            or "network" in context.failure_message.lower()
        ):
            return "infrastructure"
        else:
            return "defect"

    def _generate_issue_title(self, context: FailureContext) -> str:
        """Generate concise issue title."""
        # Extract key error type
        error_type = "Test Failure"
        failure_msg = context.failure_message

        if "AssertionError" in failure_msg:
            error_type = "Assertion Failure"
        elif "ModuleNotFoundError" in failure_msg:
            error_type = "Import Error"
        elif "TimeoutError" in failure_msg:
            error_type = "Timeout Error"
        elif "UnicodeError" in failure_msg:
            error_type = "Unicode Error"
        elif "ConnectionError" in failure_msg:
            error_type = "Connection Error"

        # Create title with test name and error type
        test_name_short = (
            context.test_name.split("::")[-1]
            if "::" in context.test_name
            else context.test_name
        )

        return f"{error_type} in {test_name_short}"

    def _generate_issue_body(self, context: FailureContext) -> str:
        """Generate comprehensive issue body with failure context."""
        body_parts = [
            "## Automated Issue Creation",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Source:** Test failure tracking system",
            f"**Failure ID:** {context.failure_id}",
            "",
            "## Failure Summary",
            "",
            f"**Test:** `{context.test_name}`",
            f"**Error:** {context.failure_message}",
            "",
            "## Stack Trace",
            "",
            "```",
            context.stack_trace or "No stack trace available",
            "```",
            "",
            "## Environment Context",
        ]

        if context.environment_info:
            body_parts.append("")
            for key, value in context.environment_info.items():
                body_parts.append(f"- **{key}**: {value}")
        else:
            body_parts.extend(["", "No environment context available"])

        body_parts.extend(
            [
                "",
                "## Log Analysis",
                "",
                f"**Setup logs:** {len(context.setup_logs)}",
                f"**Execution logs:** {len(context.execution_logs)}",
                f"**Teardown logs:** {len(context.teardown_logs)}",
            ]
        )

        if context.debugging_hints:
            body_parts.extend(["", "## Debugging Hints", ""])
            for hint in context.debugging_hints:
                body_parts.append(f"- {hint}")

        body_parts.extend(
            [
                "",
                "## Reproduction Guide",
                "",
                "```bash",
                context.reproduction_guide.replace("\n## ", "\n# ").replace(
                    "\n### ", "\n## "
                ),
                "```",
            ]
        )

        if context.related_failures:
            body_parts.extend(
                ["", f"## Related Failures ({len(context.related_failures)})", ""]
            )
            for related in context.related_failures[:5]:  # Limit to top 5
                body_parts.append(
                    f"- **{related.get('test_name', 'Unknown')}**: {related.get('failure_message', 'No message')[:100]}..."
                )

        body_parts.extend(
            [
                "",
                "## Next Steps",
                "",
                "- [ ] Review failure context and logs",
                "- [ ] Run reproduction steps locally",
                "- [ ] Identify root cause",
                "- [ ] Implement fix",
                "- [ ] Verify fix with test execution",
                "",
                "---",
                "",
                f"**Auto-generated from test failure tracking system**",
                f"**View correlation report:** `quality/reports/log_correlation_report.json`",
                f"**Reproduction script:** `quality/reports/reproduction_script_{context.failure_id}.py`",
            ]
        )

        return "\n".join(body_parts)

    def _determine_assignees(self, context: FailureContext) -> List[str]:
        """Determine who should be assigned to the issue."""
        # For now, return empty list (manual assignment)
        # Future enhancement: could analyze code ownership, recent commits, etc.
        return []

    def _create_github_issue(
        self, template: IssueTemplate, auto_assign: bool
    ) -> IssueCreationResult:
        """Create the actual GitHub issue."""
        try:
            # Create temporary file for issue body
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False, encoding="utf-8"
            ) as f:
                f.write(template.body)
                body_file = f.name

            # Build gh issue create command
            cmd = [
                "gh",
                "issue",
                "create",
                "--title",
                template.title,
                "--body-file",
                body_file,
                "--repo",
                f"{self.owner}/{self.repo}",
            ]

            # Add labels
            for label in template.labels:
                cmd.extend(["--label", label])

            # Add assignees
            for assignee in template.assignees:
                cmd.extend(["--assignee", assignee])

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Parse issue URL from output
            issue_url = result.stdout.strip()
            issue_number = int(issue_url.split("/")[-1]) if issue_url else None

            # Clean up temporary file
            Path(body_file).unlink()

            return IssueCreationResult(
                success=True,
                issue_number=issue_number,
                issue_url=issue_url,
                error_message=None,
                labels_applied=template.labels,
                auto_assigned=auto_assign and bool(template.assignees),
            )

        except subprocess.CalledProcessError as e:
            return IssueCreationResult(
                success=False,
                issue_number=None,
                issue_url=None,
                error_message=f"GitHub CLI error: {e.stderr}",
                labels_applied=[],
                auto_assigned=False,
            )
        except Exception as e:
            return IssueCreationResult(
                success=False,
                issue_number=None,
                issue_url=None,
                error_message=f"Unexpected error: {str(e)}",
                labels_applied=[],
                auto_assigned=False,
            )
        finally:
            # Ensure cleanup
            try:
                if "body_file" in locals():
                    Path(body_file).unlink(missing_ok=True)
            except:
                pass

    def _has_existing_issue(self, failure: Dict[str, Any]) -> bool:
        """Check if failure already has a GitHub issue."""
        try:
            # Search for existing issues with test name
            test_name = failure.get("test_name", "")
            search_query = f"repo:{self.owner}/{self.repo} {test_name} in:title"

            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "list",
                    "--search",
                    search_query,
                    "--json",
                    "number,title",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            issues = json.loads(result.stdout)
            return len(issues) > 0

        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return False  # Assume no existing issue if search fails

    def _get_recommended_labels(self, failure: Dict[str, Any]) -> List[str]:
        """Get recommended labels for a failure candidate."""
        labels = ["defect", "automated-issue"]

        category = failure.get("category", "")
        if category == "assertion_error":
            labels.append("test-failure")
        elif category == "import_error":
            labels.append("dependencies")
        elif category == "timeout_error":
            labels.append("performance")
        elif category in ["network_error", "database_error"]:
            labels.append("infrastructure")

        severity = failure.get("severity", "")
        if severity == "critical":
            labels.append("priority/high")
        elif severity == "high":
            labels.append("priority/medium")
        else:
            labels.append("priority/low")

        return labels

    def generate_batch_creation_report(self, results: List[IssueCreationResult]) -> str:
        """Generate a report for batch issue creation."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        report_lines = [
            "# GitHub Issue Creation Report",
            f"**Generated:** {datetime.now().isoformat()}",
            "",
            f"## Summary",
            f"- **Total failures processed:** {len(results)}",
            f"- **Issues created successfully:** {len(successful)}",
            f"- **Failed creations:** {len(failed)}",
            (
                f"- **Success rate:** {len(successful)/len(results)*100:.1f}%"
                if results
                else "0%"
            ),
            "",
        ]

        if successful:
            report_lines.extend(["## ✅ Successfully Created Issues", ""])
            for result in successful:
                report_lines.append(
                    f"- [#{result.issue_number}]({result.issue_url}) - Labels: {', '.join(result.labels_applied)}"
                )

        if failed:
            report_lines.extend(["", "## ❌ Failed Issue Creations", ""])
            for result in failed:
                report_lines.append(f"- Error: {result.error_message}")

        return "\n".join(report_lines)
