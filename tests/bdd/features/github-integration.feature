# GitHub Integration BDD Scenarios
# User Story: US-00009 GitHub Issue Template Integration

@integration @infrastructure @priority_high
Feature: GitHub Issue Template Integration
  As a project maintainer
  I want standardized GitHub issue templates
  So that contributors can report issues consistently and efficiently

  Background:
    Given the GitHub repository is configured
    And issue templates are available in .github/ISSUE_TEMPLATE/
    And the documentation structure is properly linked

  @functional @smoke
  Scenario: User creates an epic using the epic template
    Given a user wants to create a new epic
    When they navigate to GitHub Issues
    And they select "Epic" from the issue templates
    Then they should see the epic template with all required sections
    And the template should include links to relevant documentation
    And the template should enforce the EP-XXXXX naming convention

  @functional @smoke
  Scenario: User creates a user story using the user story template
    Given a user wants to create a new user story
    When they navigate to GitHub Issues
    And they select "User Story" from the issue templates
    Then they should see the user story template with acceptance criteria
    And the template should include BDD scenario requirements
    And the template should enforce the US-XXXXX naming convention

  @functional @smoke
  Scenario: User creates a defect report using the defect template
    Given a user wants to report a defect
    When they navigate to GitHub Issues
    And they select "Defect Report" from the issue templates
    Then they should see the defect template with all diagnostic fields
    And the template should include GDPR impact assessment
    And the template should enforce the DEF-XXXXX naming convention

  @functional @validation
  Scenario: GitHub issue templates reference correct documentation
    Given the issue templates are configured
    When a user opens any issue template
    Then all documentation links should be valid and accessible
    And links should point to the stable documentation in docs/context/
    And technical implementation links should point to docs/technical/

  @integration @workflow
  Scenario: Epic creation workflow with documentation integration
    Given a user creates an epic using the template
    When they fill in all required fields including documentation references
    And they submit the epic issue
    Then the epic should be properly labeled with "epic" tag
    And the epic should reference relevant ADRs from docs/context/decisions/
    And the epic should be trackable in the Requirements Matrix

  @integration @workflow
  Scenario: User story creation workflow with BDD integration
    Given a user creates a user story using the template
    When they fill in acceptance criteria and BDD requirements
    And they submit the user story
    Then the user story should be properly labeled with "user-story" tag
    And the story should be linked to parent epic
    And BDD scenarios should be required before implementation

  @functional @edge_case
  Scenario: Issue template handles missing documentation references
    Given a user creates an issue with incomplete documentation links
    When they submit the issue
    Then the system should validate required documentation fields
    And missing links should be flagged in the issue description
    And the issue should be labeled as "documentation-incomplete"

  @security @access_control
  Scenario: Issue templates maintain security standards
    Given issue templates are configured
    When users create issues involving security or GDPR
    Then sensitive information should not be exposed in templates
    And GDPR impact assessment should be mandatory for data-related issues
    And security issues should be properly labeled and triaged

  @integration @traceability
  Scenario: GitHub Issues integrate with Requirements Traceability Matrix
    Given issues are created using the templates
    When the RTM is updated
    Then GitHub issue references should automatically link to implementation
    And status changes in GitHub should reflect in documentation
    And bidirectional traceability should be maintained

  @maintenance @template_updates
  Scenario: Issue templates stay synchronized with documentation structure
    Given the documentation structure evolves
    When documentation paths change
    Then issue templates should be updated accordingly
    And template validation should catch broken links
    And users should be notified of template changes

# Data-driven validation
  @validation @data_driven
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

# Performance and reliability
  @performance @load_testing
  Scenario: Issue template performance under load
    Given multiple users access issue templates simultaneously
    When the templates are loaded
    Then response time should be under 2 seconds
    And all template content should load completely
    And documentation links should remain accessible

# GDPR compliance for issue management
  @security @gdpr
  Scenario: Issue templates handle personal data appropriately
    Given a user creates an issue that might contain personal data
    When they use any issue template
    Then the template should warn about personal data exposure
    And users should be guided to redact sensitive information
    And GDPR compliance should be verified before issue submission