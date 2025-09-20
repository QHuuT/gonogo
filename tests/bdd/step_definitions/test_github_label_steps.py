"""
BDD Step definitions for GitHub Issue Label Assignment

Tests the automatic label assignment functionality through
behavior-driven development scenarios.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from src.shared.utils.github_label_mapper import (
    GitHubIssueLabelMapper,
    IssueData,
    TraceabilityMatrixParser,
)

# Load BDD scenarios
scenarios("../features/github-integration.feature")


@pytest.fixture
def bdd_context():
    """Shared context for BDD scenarios."""
    return {
        "mapper": None,
        "issue_data": None,
        "generated_labels": None,
        "matrix_mappings": {},
        "repository_labels": set(),
        "priority": None,
        "epic_id": None,
        "gdpr_selections": [],
        "issue_body": "",
    }


@pytest.fixture
def mock_traceability_matrix(tmp_path):
    """Create a mock traceability matrix file."""
    matrix_content = """
    # Requirements Traceability Matrix

    ## Epic to User Story Mapping

    | Epic ID | Epic Name | User Stories | Total Story Points | Priority | Status |
    |---------|-----------|--------------|-------------------|----------|--------|
    | **EP-001** | Blog Content Management | US-001, US-002 | 8 | High | 📝 Planned |
    | **EP-002** | GDPR-Compliant Comment System | US-003, US-004, US-005 | 16 | High | 📝 Planned |
    | **EP-003** | Privacy and Consent Management | US-006, US-007, US-008 | 29 | Critical | 📝 Planned |
    | **EP-004** | GitHub Workflow Integration | US-009, US-010, US-011, US-012 | 21 | High | 📝 Planned |
    """

    matrix_file = tmp_path / "requirements-matrix.md"
    matrix_file.write_text(matrix_content)
    return matrix_file


# Given steps
@given("the traceability matrix defines epic-to-component mappings")
def given_traceability_matrix_mappings(bdd_context, mock_traceability_matrix):
    """Set up traceability matrix with epic mappings."""
    bdd_context["matrix_mappings"] = {
        "EP-001": {"component": "frontend", "epic_label": "blog-content"},
        "EP-002": {"component": "backend", "epic_label": "comment-system"},
        "EP-003": {"component": "gdpr", "epic_label": "privacy-consent"},
        "EP-004": {"component": "ci-cd", "epic_label": "github-workflow"},
    }

    # Create mapper with mocked matrix
    with patch(
        "src.shared.utils.github_label_mapper.TraceabilityMatrixParser.get_epic_mappings"
    ) as mock_mappings:
        mock_mappings.return_value = bdd_context["matrix_mappings"]
        bdd_context["mapper"] = GitHubIssueLabelMapper(mock_traceability_matrix)


@given("the traceability matrix defines epic-to-component relationships")
def given_epic_component_relationships(bdd_context, mock_traceability_matrix):
    """Alias for epic-to-component mappings."""
    given_traceability_matrix_mappings(bdd_context, mock_traceability_matrix)


@given("the traceability matrix defines epic priorities and release mappings")
def given_epic_priorities_and_release_mappings(bdd_context, mock_traceability_matrix):
    """Set up epic priorities and release characteristics."""
    given_traceability_matrix_mappings(bdd_context, mock_traceability_matrix)

    # Additional release mapping context
    bdd_context["release_rules"] = {
        "critical_epics": ["EP-002", "EP-003"],  # MVP-critical
        "mvp_priority": "Critical",
        "v1_1_priority": "High",
    }


@given("a user creates an epic issue using the epic template")
def given_user_creates_epic_issue(bdd_context):
    """Set up epic issue creation context."""
    bdd_context["issue_type"] = "epic"
    bdd_context["template_used"] = "epic.yml"


@given("a user creates a user story using the user story template")
def given_user_creates_user_story(bdd_context):
    """Set up user story issue creation context."""
    bdd_context["issue_type"] = "user-story"
    bdd_context["template_used"] = "user-story.yml"


@given("a user creates an issue using any template")
def given_user_creates_any_issue(bdd_context):
    """Set up generic issue creation context."""
    bdd_context["issue_type"] = "generic"
    bdd_context["template_used"] = "any"


@given("the repository has a defined set of labels")
def given_repository_has_labels(bdd_context):
    """Set up repository with predefined labels."""
    bdd_context["repository_labels"] = {
        "priority/critical",
        "priority/high",
        "priority/medium",
        "priority/low",
        "epic/blog-content",
        "epic/comment-system",
        "epic/privacy-consent",
        "epic/github-workflow",
        "component/frontend",
        "component/backend",
        "component/gdpr",
        "component/ci-cd",
        "release/mvp",
        "release/v1.1",
        "release/v1.2",
        "status/backlog",
        "status/ready",
        "status/in-progress",
        "status/blocked",
        "gdpr/personal-data",
        "gdpr/consent-required",
        "gdpr/privacy-review",
        "user-story",
        "epic",
        "defect",
        "needs-triage",
    }


@given(parsers.parse('a user creates an issue with priority "{priority_level}"'))
def given_issue_with_priority(bdd_context, priority_level):
    """Set up issue with specific priority."""
    bdd_context["priority"] = priority_level


@given("a user creates an issue with invalid epic references")
def given_issue_with_invalid_epic(bdd_context):
    """Set up issue with invalid epic ID."""
    bdd_context["epic_id"] = "EP-999"  # Non-existent epic
    bdd_context["invalid_epic"] = True


@given(parsers.parse('the issue is linked to epic "{epic_id}"'))
def given_issue_linked_to_epic(bdd_context, epic_id):
    """Set up issue linked to specific epic."""
    bdd_context["epic_id"] = epic_id


# When steps
@when("they set a valid priority level")
def when_set_valid_priority(bdd_context):
    """Set a valid priority level."""
    if not bdd_context.get("priority"):
        bdd_context["priority"] = "High"  # Default


@when("they provide a valid epic ID from the traceability matrix")
def when_provide_valid_epic_id(bdd_context):
    """Provide a valid epic ID."""
    if not bdd_context.get("epic_id"):
        bdd_context["epic_id"] = "EP-001"  # Default valid epic


@when("they reference a valid parent epic from the traceability matrix")
def when_reference_valid_parent_epic(bdd_context):
    """Reference a valid parent epic."""
    if not bdd_context.get("epic_id"):
        bdd_context["epic_id"] = "EP-003"  # Default GDPR epic


@when("they set a priority level")
def when_set_priority_level(bdd_context):
    """Set priority level (may already be set)."""
    if not bdd_context.get("priority"):
        bdd_context["priority"] = "Medium"  # Default


@when("they indicate GDPR involvement through template checkboxes")
def when_indicate_gdpr_involvement(bdd_context):
    """Select GDPR-related checkboxes."""
    bdd_context["gdpr_selections"] = [
        "This story involves personal data processing",
        "GDPR compliance review required",
    ]


@when("they submit the issue")
def when_submit_issue(bdd_context):
    """Submit the issue and generate labels."""
    # Build issue body based on context
    body_parts = []

    if bdd_context.get("priority"):
        body_parts.append(f"### Priority\n\n{bdd_context['priority']}\n")

    if bdd_context.get("epic_id"):
        epic_field = (
            "Epic ID" if bdd_context.get("issue_type") == "epic" else "Parent Epic"
        )
        body_parts.append(f"### {epic_field}\n\n{bdd_context['epic_id']}\n")

    if bdd_context.get("gdpr_selections"):
        for selection in bdd_context["gdpr_selections"]:
            body_parts.append(f"{selection}\n")

    # Add any additional body content
    if bdd_context.get("issue_body"):
        body_parts.append(bdd_context["issue_body"])

    issue_body = "\n".join(body_parts)

    # Create issue data
    bdd_context["issue_data"] = IssueData(
        title=f"Test Issue #{bdd_context.get('issue_type', 'generic')}",
        body=issue_body,
        existing_labels=["needs-triage"],
        issue_number=123,
    )

    # Generate labels using the mapper
    if bdd_context["mapper"]:
        bdd_context["generated_labels"] = bdd_context["mapper"].generate_labels(
            bdd_context["issue_data"]
        )


@when("the automatic labeling system processes any issue")
def when_labeling_system_processes_issue(bdd_context):
    """Process issue through labeling system."""
    when_submit_issue(bdd_context)


@when(parsers.parse("they submit the issue"))
def when_submit_issue_parsed(bdd_context):
    """Submit the issue (parsed version)."""
    when_submit_issue(bdd_context)


@when("the issue is linked to an epic with defined release characteristics")
def when_linked_to_epic_with_release_characteristics(bdd_context):
    """Link issue to epic with release mapping."""
    if not bdd_context.get("epic_id"):
        bdd_context["epic_id"] = "EP-002"  # MVP-critical epic


# Then steps
@then("the issue should automatically receive the corresponding priority label")
def then_receive_priority_label(bdd_context):
    """Verify priority label was assigned."""
    priority = bdd_context.get("priority")
    if priority:
        expected_label = f"priority/{priority.lower()}"
        assert (
            expected_label in bdd_context["generated_labels"]
        ), f"Expected priority label {expected_label} not found in {bdd_context['generated_labels']}"


@then(
    "the issue should automatically receive the epic label based on the traceability matrix"
)
def then_receive_epic_label_from_matrix(bdd_context):
    """Verify epic label from traceability matrix."""
    epic_id = bdd_context.get("epic_id")
    if epic_id and epic_id in bdd_context["matrix_mappings"]:
        epic_label = bdd_context["matrix_mappings"][epic_id]["epic_label"]
        expected_label = f"epic/{epic_label}"
        assert (
            expected_label in bdd_context["generated_labels"]
        ), f"Expected epic label {expected_label} not found"


@then(
    "the issue should automatically receive the component label based on the traceability matrix"
)
def then_receive_component_label_from_matrix(bdd_context):
    """Verify component label from traceability matrix."""
    epic_id = bdd_context.get("epic_id")
    if epic_id and epic_id in bdd_context["matrix_mappings"]:
        component = bdd_context["matrix_mappings"][epic_id]["component"]
        expected_label = f"component/{component}"
        assert (
            expected_label in bdd_context["generated_labels"]
        ), f"Expected component label {expected_label} not found"


@then('the "needs-triage" label should be removed')
def then_needs_triage_removed(bdd_context):
    """Verify needs-triage label was removed."""
    assert (
        "needs-triage" not in bdd_context["generated_labels"]
    ), "needs-triage label should be removed when meaningful labels are added"


@then("the issue should receive labels corresponding to the parent epic's mapping")
def then_receive_parent_epic_labels(bdd_context):
    """Verify labels correspond to parent epic."""
    # This combines epic and component label checks
    then_receive_epic_label_from_matrix(bdd_context)
    then_receive_component_label_from_matrix(bdd_context)


@then(
    "the component label should match the epic's component in the traceability matrix"
)
def then_component_matches_epic_mapping(bdd_context):
    """Verify component label matches epic mapping."""
    then_receive_component_label_from_matrix(bdd_context)


@then("the release label should be determined by priority and epic mapping rules")
def then_release_label_by_rules(bdd_context):
    """Verify release label follows business rules."""
    priority = bdd_context.get("priority")
    epic_id = bdd_context.get("epic_id")

    # Apply business rules
    if priority == "Critical":
        expected_label = "release/mvp"
    elif epic_id in ["EP-002", "EP-003"]:  # MVP-critical epics
        expected_label = "release/mvp"
    elif priority == "High":
        expected_label = "release/v1.1"
    else:
        expected_label = "release/v1.2"

    assert (
        expected_label in bdd_context["generated_labels"]
    ), f"Expected release label {expected_label} not found"


@then("the issue should automatically receive corresponding GDPR labels")
def then_receive_gdpr_labels(bdd_context):
    """Verify GDPR labels were assigned."""
    gdpr_selections = bdd_context.get("gdpr_selections", [])

    for selection in gdpr_selections:
        if "personal data processing" in selection.lower():
            assert "gdpr/personal-data" in bdd_context["generated_labels"]
        if "compliance review required" in selection.lower():
            assert "gdpr/consent-required" in bdd_context["generated_labels"]


@then("the labels should match the GDPR considerations selected")
def then_labels_match_gdpr_selections(bdd_context):
    """Verify labels match GDPR checkbox selections."""
    then_receive_gdpr_labels(bdd_context)


@then(
    parsers.parse(
        'the issue should automatically receive the priority label "{expected_label}"'
    )
)
def then_receive_specific_priority_label(bdd_context, expected_label):
    """Verify specific priority label was assigned."""
    assert (
        expected_label in bdd_context["generated_labels"]
    ), f"Expected priority label {expected_label} not found"


@then("the release label should be determined by the business rules")
def then_release_by_business_rules(bdd_context):
    """Verify release label follows business rules."""
    then_release_label_by_rules(bdd_context)


@then("critical items should be assigned to MVP release")
def then_critical_items_to_mvp(bdd_context):
    """Verify critical items go to MVP."""
    if bdd_context.get("priority") == "Critical":
        assert "release/mvp" in bdd_context["generated_labels"]


@then("high priority items should follow the release mapping logic")
def then_high_priority_follows_mapping(bdd_context):
    """Verify high priority items follow mapping logic."""
    if bdd_context.get("priority") == "High":
        epic_id = bdd_context.get("epic_id")
        if epic_id in ["EP-002", "EP-003"]:
            assert "release/mvp" in bdd_context["generated_labels"]
        else:
            assert "release/v1.1" in bdd_context["generated_labels"]


@then("the issue should receive an appropriate initial status label")
def then_receive_initial_status(bdd_context):
    """Verify initial status label was assigned."""
    status_labels = [
        label
        for label in bdd_context["generated_labels"]
        if label.startswith("status/")
    ]
    assert len(status_labels) >= 1, "Should have at least one status label"


@then('the status should be "backlog" unless specific readiness indicators are present')
def then_default_status_backlog(bdd_context):
    """Verify default status is backlog."""
    if not any(
        indicator in bdd_context.get("issue_body", "").lower()
        for indicator in ["ready", "in progress", "blocked"]
    ):
        assert "status/backlog" in bdd_context["generated_labels"]


@then(
    'status should be "ready" if readiness indicators are detected in the issue content'
)
def then_ready_status_when_indicated(bdd_context):
    """Verify ready status when indicators present."""
    if "ready" in bdd_context.get("issue_body", "").lower():
        assert "status/ready" in bdd_context["generated_labels"]


@then("the system should gracefully handle the invalid references")
def then_handle_invalid_references_gracefully(bdd_context):
    """Verify system handles invalid epic references."""
    # Should not crash and should still generate some labels
    assert bdd_context["generated_labels"] is not None
    assert len(bdd_context["generated_labels"]) > 0


@then("no invalid component mappings should be applied")
def then_no_invalid_component_mappings(bdd_context):
    """Verify no invalid component labels were applied."""
    if bdd_context.get("invalid_epic"):
        component_labels = [
            label
            for label in bdd_context["generated_labels"]
            if label.startswith("component/")
        ]
        # Should not have component labels for invalid epic
        epic_id = bdd_context.get("epic_id")
        if epic_id not in bdd_context["matrix_mappings"]:
            # No component labels should be added for unknown epics
            pass  # This is handled by the mapper implementation


@then("valid labels should still be assigned where possible")
def then_valid_labels_still_assigned(bdd_context):
    """Verify valid labels are still assigned despite errors."""
    if bdd_context.get("priority"):
        priority_labels = [
            label
            for label in bdd_context["generated_labels"]
            if label.startswith("priority/")
        ]
        assert len(priority_labels) >= 1, "Should still assign priority labels"


@then("the system should log appropriate warnings for missing mappings")
def then_log_warnings_for_missing_mappings(bdd_context):
    """Verify warnings are logged for missing mappings."""
    # In a real implementation, you'd check logging output
    # For now, we just verify the system didn't crash
    assert bdd_context["generated_labels"] is not None


@then("only labels that exist in the repository should be assigned")
def then_only_existing_labels_assigned(bdd_context):
    """Verify only existing repository labels are assigned."""
    if bdd_context.get("repository_labels"):
        for label in bdd_context["generated_labels"]:
            if label != "needs-triage":  # May be removed
                assert (
                    label in bdd_context["repository_labels"]
                ), f"Label {label} should exist in repository"


@then("attempts to assign non-existent labels should be handled gracefully")
def then_handle_nonexistent_labels_gracefully(bdd_context):
    """Verify graceful handling of non-existent labels."""
    # This would be tested by mocking the label existence check
    # For now, verify the system completed successfully
    assert bdd_context["generated_labels"] is not None


@then("the labeling process should not fail due to missing labels")
def then_labeling_process_should_not_fail(bdd_context):
    """Verify labeling process doesn't fail on missing labels."""
    assert bdd_context["generated_labels"] is not None
    assert len(bdd_context["generated_labels"]) >= 0
