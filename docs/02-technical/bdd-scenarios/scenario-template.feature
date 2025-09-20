# BDD Scenario Template

@tag_category @priority_high @gdpr_compliant
Feature: [Feature Name]
  As a [type of user]
  I want [functionality]
  So that [business value]

  Background:
    Given the application is running
    And the database is clean
    And GDPR compliance is enabled

  @functional @smoke
  Scenario: [Happy path scenario name]
    Given [initial state/context]
    And [additional context if needed]
    When [action performed by user]
    And [additional action if needed]
    Then [expected outcome]
    And [additional verification]

  @functional @edge_case
  Scenario: [Edge case scenario name]
    Given [edge case context]
    When [action that triggers edge case]
    Then [expected behavior for edge case]

  @security @gdpr
  Scenario: [GDPR compliance scenario]
    Given a user wants to [perform action involving personal data]
    And consent requirements are [defined state]
    When they [attempt the action]
    Then the system [enforces GDPR requirements]
    And [specific compliance verification]

  @error_handling
  Scenario: [Error scenario name]
    Given [context that leads to error]
    When [action that should fail]
    Then [error handling behavior]
    And [user feedback provided]

  @security @input_validation
  Scenario: [Security scenario name]
    Given a user attempts to [potentially malicious action]
    When they input [malicious payload examples]
    Then the system [security response]
    And [logging/monitoring behavior]

  # Data Tables Example
  @data_driven
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

# Tags Explanation:
# @tag_category: functional, security, performance, gdpr, accessibility
# @priority: high, medium, low
# @gdpr_compliant: scenarios that test GDPR compliance
# @smoke: critical functionality tests
# @edge_case: boundary condition tests
# @error_handling: error scenario tests
# @data_driven: scenarios using data tables

# Naming Conventions:
# - Use descriptive scenario names
# - Start with the main action/behavior
# - Include context when necessary
# - Keep scenarios focused on single behavior

# Best Practices:
# - One scenario = one behavior
# - Use business language, not technical jargon
# - Keep steps simple and atomic
# - Avoid implementation details
# - Focus on what, not how