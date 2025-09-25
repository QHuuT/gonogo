# BDD Scenario Template
# Complete template with RTM database integration and all test category markers

# Feature-level tags (apply to ALL scenarios in this feature)
@epic:EP-XXXXX @user_story:US-XXXXX @component:backend @test_type:bdd
Feature: [Feature Name]
  As a [type of user]
  I want [functionality]
  So that [business value]

  Background:
    Given the application is running
    And the database is clean
    And GDPR compliance is enabled

  # Smoke test - critical functionality
  @priority:high @test_category:smoke
  Scenario: [Happy path scenario name]
    Given [initial state/context]
    And [additional context if needed]
    When [action performed by user]
    And [additional action if needed]
    Then [expected outcome]
    And [additional verification]

  # Edge case test - boundary conditions
  @priority:low @test_category:edge
  Scenario: [Edge case scenario name]
    Given [edge case context]
    When [action that triggers edge case]
    Then [expected behavior for edge case]

  # Regression test - previously fixed issues
  @priority:medium @test_category:regression
  Scenario: [Regression scenario name]
    Given [context for previously fixed bug]
    When [action that previously failed]
    Then [expected correct behavior]
    And [verification that bug is fixed]

  # Performance test - response time validation
  @priority:medium @test_category:performance
  Scenario: [Performance scenario name]
    Given [performance test context]
    When [action to measure]
    Then [performance requirement met]
    And the response time should be less than [X] seconds

  # GDPR compliance test
  @priority:critical @test_category:compliance-gdpr
  Scenario: [GDPR compliance scenario]
    Given a user wants to [perform action involving personal data]
    And consent requirements are [defined state]
    When they [attempt the action]
    Then the system [enforces GDPR requirements]
    And [specific compliance verification]

  # RGAA compliance test - accessibility
  @priority:high @test_category:compliance-rgaa
  Scenario: [RGAA compliance scenario]
    Given a user with [accessibility need]
    When they [interact with the interface]
    Then [accessibility requirement is met]
    And [WCAG 2.1 AA compliance verified]

  # Documentation compliance test
  @priority:medium @test_category:compliance-doc
  Scenario: [Documentation compliance scenario]
    Given [documentation requirement context]
    When [documentation is checked]
    Then [required documentation exists]
    And [documentation is up to date]

  # Project management compliance test
  @priority:high @test_category:compliance-project-management
  Scenario: [Project management compliance scenario]
    Given [project management requirement context]
    When [project artifact is created]
    Then [required fields are enforced]
    And [traceability is maintained]

  # Error handling scenario
  @priority:medium @test_category:error-handling
  Scenario: [Error scenario name]
    Given [context that leads to error]
    When [action that should fail]
    Then [error handling behavior]
    And [user feedback provided]
    And the system remains stable

  # Security/Input validation scenario
  @priority:critical @test_category:compliance-gdpr
  Scenario: [Security scenario name]
    Given a user attempts to [potentially malicious action]
    When they input [malicious payload examples]
    Then the system [security response]
    And [logging/monitoring behavior]

  # Data Tables Example
  @priority:medium @test_category:regression
  Scenario Outline: [Data-driven scenario name]
    Given a user with role "<role>"
    When they try to "<action>"
    Then they should "<expected_result>"

    Examples:
      | role        | action              | expected_result |
      | guest       | view public posts   | succeed         |
      | guest       | comment on posts    | require consent |
      | author      | create posts        | succeed         |
      | admin       | delete comments     | succeed         |

# ============================================================================
# RTM Database Integration Tags
# ============================================================================

# Feature-level Tags (apply to ALL scenarios):
# @epic:EP-XXXXX           - Links to Epic in RTM database (REQUIRED)
# @user_story:US-XXXXX     - Links to User Story in RTM database (REQUIRED)
# @component:VALUE         - Component: backend, frontend, security, database
# @test_type:VALUE         - Test type: unit, integration, e2e, security, bdd

# Scenario-level Tags (apply to SPECIFIC scenario):
# @priority:VALUE          - Priority: critical, high, medium, low
# @test_category:VALUE     - Category: smoke, edge, regression, performance,
#                            error-handling, compliance-gdpr, compliance-rgaa,
#                            compliance-doc, compliance-project-management

# ============================================================================
# Test Category Guidelines
# ============================================================================

# Smoke Tests (@test_category:smoke)
# - Critical functionality that must work
# - Run on every build
# - Happy path scenarios
# - High priority

# Edge Tests (@test_category:edge)
# - Boundary conditions
# - Error handling
# - Unusual input scenarios
# - Low to medium priority

# Regression Tests (@test_category:regression)
# - Previously fixed bugs
# - Known issue scenarios
# - Validation that fixes remain in place
# - Medium priority

# Performance Tests (@test_category:performance)
# - Response time validation
# - Load testing scenarios
# - Resource usage checks
# - Medium to high priority

# Error Handling Tests (@test_category:error-handling)
# - Invalid input handling
# - System stability under errors
# - Graceful degradation
# - User error feedback
# - Medium priority

# Compliance Tests (@test_category:compliance-*)
# - compliance-gdpr: GDPR/privacy compliance
# - compliance-rgaa: RGAA/WCAG accessibility compliance
# - compliance-doc: Documentation requirements compliance
# - compliance-project-management: Project management/traceability compliance
# - Critical to high priority

# ============================================================================
# Priority Guidelines
# ============================================================================

# @priority:critical - Must pass, blocks release
# @priority:high     - Important functionality, should not fail
# @priority:medium   - Standard functionality, failures investigated
# @priority:low      - Nice to have, edge cases

# ============================================================================
# Naming Conventions
# ============================================================================

# - Use descriptive scenario names
# - Start with the main action/behavior
# - Include context when necessary
# - Keep scenarios focused on single behavior

# ============================================================================
# Best Practices
# ============================================================================

# Scenario Design:
# - One scenario = one behavior
# - Use business language, not technical jargon
# - Keep steps simple and atomic
# - Avoid implementation details
# - Focus on what, not how

# RTM Integration:
# - Always tag with epic and user_story at feature level
# - Use test_category for filtering and organization
# - Set appropriate priority for test execution order
# - Sync to database after adding tests:
#   python tools/test-db-integration.py discover scenarios

# GDPR Compliance:
# - Always include GDPR compliance scenarios
# - Test consent workflows
# - Verify data deletion capabilities
# - Document personal data handling

# Accessibility (RGAA):
# - Include keyboard navigation scenarios
# - Test screen reader compatibility
# - Verify WCAG 2.1 AA compliance
# - Test color contrast and visual indicators

# ============================================================================
# Example Complete Feature
# ============================================================================

# @epic:EP-00001 @user_story:US-00010 @component:backend @test_type:bdd
# Feature: User Authentication
#   As a blog visitor
#   I want to authenticate securely
#   So that I can access protected features
#
#   @priority:high @test_category:smoke
#   Scenario: User logs in successfully
#     Given a registered user with valid credentials
#     When they enter their username and password
#     Then they are successfully authenticated
#     And they see the authenticated dashboard
#
#   @priority:critical @test_category:compliance-gdpr
#   Scenario: User consent is required for tracking
#     Given an unauthenticated user
#     When they access the login page
#     Then they must provide consent before data is collected
#     And their consent choice is stored securely