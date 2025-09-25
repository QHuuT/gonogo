# GitHub Integration BDD Scenarios
# User Story: US-00009 GitHub Issue Template Integration

@epic:EP-XXXXX @user_story:US-XXXXX @component:backend @test_type:bdd
Feature: GitHub Issue Template Integration
  As a project maintainer
  I want standardized GitHub issue templates
  So that contributors can report issues consistently and efficiently

  Background:
    Given the GitHub repository is configured
    And issue templates are available in .github/ISSUE_TEMPLATE/
    And the documentation structure is properly linked

  @priority:high @test_category:compliance-doc
  Scenario: GitHub issue templates reference correct documentation
    Given the issue templates are configured
    When a user opens any issue template
    Then all documentation links should be valid and accessible
    And links should point to the stable documentation in docs/context/
    And technical implementation links should point to docs/technical/

  @priority:high @test_category:compliance-project-management
  Scenario: Epic creation workflow with documentation integration
    Given a user creates an epic using the template
    When they fill in all required fields including documentation references
    And they submit the epic issue
    Then the epic should be properly labeled with "epic" tag
    And the epic should reference relevant ADRs from docs/context/decisions/
    And the epic should be trackable in the RTM database

  @priority:high @test_category:compliance-project-management
  Scenario: User story creation workflow with BDD integration
    Given a user creates a user story using the template
    When they fill in acceptance criteria and BDD requirements
    And they submit the user story
    Then the user story should be properly labeled with "user-story" tag
    And the story should be linked to parent epic

  @priority:medium @test_category:compliance-doc
  Scenario: Issue template handles missing documentation references
    Given a user creates an issue with incomplete documentation links
    When they submit the issue
    Then the system should validate required documentation fields
    And missing links should be flagged in the issue description
    And the issue should be labeled as "documentation-incomplete"

  @priority:high @test_category:compliance-project-management
  Scenario: GitHub Issues integrate with Database RTM System
    Given issues are created using the templates
    When the RTM database is synchronized with GitHub
    Then GitHub issue references should automatically link to database records
    And status changes in GitHub should reflect in the RTM database
    And bidirectional traceability should be maintained through database queries

  @priority:critical @test_category:compliance-doc
  Scenario: Issue templates stay synchronized with documentation structure
    Given the documentation structure evolves
    When documentation paths change
    Then issue templates should be updated accordingly
    And template validation should catch broken links
    And users should be notified of template changes

  @priority:high @test_category:compliance-project-management
  Scenario Outline: Different issue types follow naming conventions
    Given a user creates a "<issue_type>" issue
    When they use the "<template_name>" template
    Then the issue title should follow "<naming_pattern>" format
    And the issue should be labeled with "<expected_label>"

    Examples:
      | issue_type    | template_name | naming_pattern | expected_label |
      | Epic          | epic.yml      | EP-XXXXX       | epic           |
      | User Story    | user-story.yml| US-XXXXX       | user-story     |
      | Defect Report | defect-report.yml | DEF-XXXXX      | defect         |

  @priority:medium @test_category:performance
  Scenario: Issue template performance under load
    Given multiple users access issue templates simultaneously
    When the templates are loaded
    Then response time should be under 2 seconds
    And all template content should load completely
    And documentation links should remain accessible

  @priority:medium @test_category:compliance-gdpr
  Scenario: Issue templates handle personal data appropriately
    Given a user creates an issue that might contain personal data
    When they use any issue template
    Then the template should warn about personal data exposure
    And users should be guided to redact sensitive information
    And GDPR compliance should be verified before issue submission

  @priority:high @test_category:compliance-project-management
  Scenario: Epic issues receive automatic labels based on traceability matrix mapping
    Given the traceability matrix defines epic-to-component mappings
    And a user creates an epic issue using the epic template
    When they set a valid priority level
    And they provide a valid epic ID from the traceability matrix
    And they submit the issue
    Then the issue should automatically receive the corresponding priority label
    And the issue should automatically receive the epic label based on the traceability matrix
    And the issue should automatically receive the component label based on the traceability matrix
    And the "needs-triage" label should be removed

  @priority:high @test_category:compliance-project-management
  Scenario: User story issues inherit labels from parent epic mapping
    Given the traceability matrix defines epic-to-component relationships
    And a user creates a user story using the user story template
    When they reference a valid parent epic from the traceability matrix
    And they set a priority level
    And they submit the issue
    Then the issue should receive labels corresponding to the parent epic's mapping
    And the component label should match the epic's component in the traceability matrix
    And the release label should be determined by priority and epic mapping rules

  @priority:high @test_category:gdpr
  Scenario: GDPR-related issues receive appropriate GDPR labels
    Given a user creates an issue using any template
    When they indicate GDPR involvement through template checkboxes
    And they submit the issue
    Then the issue should automatically receive corresponding GDPR labels
    And the labels should match the GDPR considerations selected

  @priority:high @test_category:compliance-project-management
  Scenario Outline: Issues receive correct priority labels
    Given a user creates an issue with priority "<priority_level>"
    When they submit the issue
    Then the issue should automatically receive the priority label "<expected_label>"

    Examples:
      | priority_level | expected_label     |
      | Critical       | priority/critical  |
      | High           | priority/high      |
      | Medium         | priority/medium    |
      | Low            | priority/low       |

  @priority:medium @test_category:compliance-project-management
  Scenario: Issues receive appropriate initial status labels
    Given a user creates an issue using any template
    When they submit the issue
    Then the issue should receive an appropriate initial status label
    And the status should be "backlog" unless specific readiness indicators are present
    And status should be "ready" if readiness indicators are detected in the issue content

  @priority:medium @test_category:compliance-project-management
  Scenario: Label assignment handles invalid or missing traceability data
    Given a user creates an issue with invalid epic references
    When they submit the issue
    Then the system should gracefully handle the invalid references
    And no invalid component mappings should be applied
    And valid labels should still be assigned where possible
    And the system should log appropriate warnings for missing mappings

  @priority:medium @test_category:compliance-project-management
  Scenario: Only existing repository labels are assigned
    Given the repository has a defined set of labels
    When the automatic labeling system processes any issue
    Then only labels that exist in the repository should be assigned
    And attempts to assign non-existent labels should be handled gracefully
    And the labeling process should not fail due to missing labels