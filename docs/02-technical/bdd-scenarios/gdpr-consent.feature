# BDD Scenarios: GDPR Consent Management
# Linked to: US-006, US-007, US-008 (Privacy and Consent Epic)

@gdpr_consent @legal_compliance @critical
Feature: GDPR Consent Management
  As a website visitor
  I want to understand and control how my data is used
  So that I can make informed decisions about my privacy

  Background:
    Given the blog application is running
    And GDPR compliance is enabled
    And French CNIL requirements are implemented

  @smoke @consent_banner @critical
  Scenario: First visit consent banner display
    Given I am a new visitor to the website
    And I have never given or refused consent
    When I visit any page on the website
    Then I should see a GDPR consent banner
    And the banner should not block access to content
    And the banner should explain data collection purposes
    And I should see options for "Accept All", "Reject All", and "Customize"

  @consent_acceptance @functional
  Scenario: Accept all cookies and tracking
    Given I see the GDPR consent banner
    When I click "Accept All"
    Then my consent should be recorded with timestamp
    And the consent banner should disappear
    And analytics tracking should be enabled
    And functional cookies should be set
    And my consent preferences should be stored

  @consent_rejection @functional
  Scenario: Reject all non-essential cookies
    Given I see the GDPR consent banner
    When I click "Reject All"
    Then only essential cookies should be allowed
    And no analytics tracking should occur
    And no marketing cookies should be set
    And the consent banner should disappear
    And I should still have full access to the blog

  @consent_customization @functional
  Scenario: Customize consent preferences
    Given I see the GDPR consent banner
    When I click "Customize"
    Then I should see detailed consent options
    And I should see categories: Essential, Functional, Analytics, Marketing
    And each category should have clear explanations
    And I should be able to toggle each category independently
    And Essential cookies should not be toggleable

  @consent_customization @functional
  Scenario Outline: Granular consent selection
    Given I am customizing my consent preferences
    When I enable "<category>" cookies
    And I disable "<disabled_category>" cookies
    And I save my preferences
    Then "<category>" functionality should be active
    And "<disabled_category>" functionality should be disabled
    And my choices should be respected across the site

    Examples:
      | category   | disabled_category |
      | Analytics  | Marketing        |
      | Functional | Analytics        |
      | Analytics  | Functional       |

  @consent_withdrawal @gdpr_rights
  Scenario: Withdraw consent easily
    Given I have previously given consent for analytics
    And I am browsing the website
    When I access the privacy preferences page
    And I withdraw consent for analytics
    Then analytics tracking should stop immediately
    And my previous analytics data should be scheduled for deletion
    And I should receive confirmation of consent withdrawal

  @consent_versioning @legal_compliance
  Scenario: Handle consent policy updates
    Given I have given consent under version 1.0 of the privacy policy
    When the privacy policy is updated to version 1.1
    And the data processing purposes change
    Then I should be prompted to review and re-consent
    And my old consent should be marked as invalid
    And I should see what has changed in the policy

  @consent_proof @audit_trail
  Scenario: Maintain consent proof for audits
    Given I give consent for analytics tracking
    When my consent is recorded
    Then the system should store:
      | Field | Value |
      | User ID | Pseudonymized identifier |
      | Consent Type | Analytics |
      | Timestamp | Exact date and time |
      | IP Hash | Anonymized IP |
      | Consent Version | Policy version number |
      | User Agent Hash | Anonymized browser info |

  @consent_persistence @functional
  Scenario: Remember consent across sessions
    Given I have given consent for analytics
    And I close my browser
    When I return to the website later
    Then my consent preferences should be remembered
    And I should not see the consent banner again
    And analytics should work according to my previous choices

  @consent_expiry @gdpr_compliance
  Scenario: Consent expiration after one year
    Given I gave consent for marketing cookies one year ago
    When the consent reaches its expiration date
    Then I should be prompted to renew my consent
    And marketing tracking should stop until I re-consent
    And the expired consent should be archived

  @french_cnil @legal_compliance
  Scenario: French CNIL specific requirements
    Given I am visiting from France
    When I see the consent banner
    Then the banner should be in French language
    And it should comply with CNIL guidelines
    And it should mention my right to complain to CNIL
    And it should provide a link to the CNIL website

  @consent_technical @non_functional
  Scenario: Consent banner performance
    Given I am a new visitor
    When the consent banner loads
    Then it should not delay page rendering
    And it should be fully functional within 1 second
    And it should work without JavaScript (graceful degradation)
    And it should be accessible to screen readers