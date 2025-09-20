# BDD Scenarios: Comment System with GDPR Compliance
# Linked to: US-003, US-004, US-005 (Comment System Epic)

@comment_system @gdpr_compliant @functional
Feature: GDPR-Compliant Comment System
  As a blog reader
  I want to leave comments on blog posts with proper privacy protection
  So that I can engage with content while maintaining control over my personal data

  Background:
    Given the blog application is running
    And there is a published blog post titled "Sample Post"
    And GDPR compliance is enabled
    And comment moderation is active

  @comment_display @functional
  Scenario: View existing comments
    Given the blog post has approved comments
    When I navigate to the blog post
    And I scroll to the comments section
    Then I should see all approved comments
    And each comment should display:
      | Field | Visibility |
      | Commenter name | Visible |
      | Comment content | Visible |
      | Comment date | Visible |
      | Email address | Hidden |

  @comment_submission @minimal_data @gdpr
  Scenario: Submit comment with minimal data (name only)
    Given I am reading a blog post
    And I have not given email consent
    When I fill in the comment form with:
      | Field | Value |
      | Name | John Doe |
      | Comment | This is a great post! |
      | Email | (left empty) |
    And I submit the comment
    Then the comment should be submitted for moderation
    And only my name and comment should be stored
    And no email address should be collected
    And I should see a confirmation message

  @comment_submission @email_consent @gdpr
  Scenario: Submit comment with email for notifications
    Given I am reading a blog post
    When I fill in the comment form with:
      | Field | Value |
      | Name | Jane Smith |
      | Comment | Interesting perspective |
      | Email | jane@example.com |
    And I check the box "Notify me of replies"
    And I confirm email consent by checking consent checkbox
    And I submit the comment
    Then the comment should be submitted for moderation
    And my email should be stored with proper consent
    And I should receive a confirmation email
    And the consent should be recorded with timestamp

  @comment_validation @security
  Scenario: Validate comment input for security
    Given I am submitting a comment
    When I enter potentially malicious content:
      | Input Type | Content |
      | XSS Script | <script>alert('xss')</script> |
      | SQL Injection | '; DROP TABLE comments; -- |
      | HTML Injection | <iframe src="evil.com"></iframe> |
    Then the malicious content should be sanitized
    And the comment should be safely stored
    And no script execution should occur
    And the comment should be flagged for additional review

  @comment_moderation @admin_workflow
  Scenario: Admin moderates comments
    Given there are pending comments awaiting moderation
    And I am logged in as an administrator
    When I access the comment moderation panel
    Then I should see all pending comments
    And for each comment I should be able to:
      | Action | Effect |
      | Approve | Comment becomes visible |
      | Reject | Comment is deleted |
      | Edit | Comment content can be modified |
      | Mark as spam | Comment is flagged and hidden |

  @comment_gdpr_rights @data_subject_rights
  Scenario: User requests comment deletion (Right to Erasure)
    Given I have submitted a comment with email "user@example.com"
    And the comment has been approved and is visible
    When I submit a data erasure request for my email
    And the request is verified and approved
    Then my comment should be deleted from the system
    And my email should be removed from the database
    And any notification subscriptions should be cancelled
    And an audit log should record the deletion

  @comment_gdpr_rights @data_rectification
  Scenario: User requests comment correction (Right to Rectification)
    Given I have submitted a comment
    And I notice an error in my comment
    When I submit a rectification request
    And provide the corrected information
    And verify my identity
    Then the comment should be updated with correct information
    And the change should be logged for audit purposes
    And I should be notified of the successful update

  @comment_data_export @data_portability
  Scenario: User requests comment data export (Right to Data Portability)
    Given I have submitted multiple comments with email "user@example.com"
    When I request a data export
    And verify my identity
    Then I should receive a JSON file containing:
      | Data Field | Content |
      | Comments | All my comment texts |
      | Timestamps | When comments were posted |
      | Post associations | Which posts I commented on |
      | Consent records | My consent history |
    And the export should be in a machine-readable format

  @comment_consent_withdrawal @gdpr_compliance
  Scenario: User withdraws email consent
    Given I previously consented to email notifications
    And I have an active email subscription for comment replies
    When I withdraw my email consent
    Then email notifications should stop immediately
    And my email should be scheduled for deletion
    And existing comments should remain but without email association
    And I should receive a final confirmation email

  @comment_retention @data_minimization
  Scenario: Automatic comment data retention
    Given comments are older than the retention period (3 years)
    When the automated retention job runs
    Then personal data should be anonymized:
      | Field | Action |
      | Email addresses | Deleted |
      | IP addresses | Already anonymized after 30 days |
      | Names | Replaced with "Anonymous User" |
      | Comment content | Retained (not personal data) |
    And the anonymization should be logged

  @comment_spam_protection @security
  Scenario: Prevent comment spam
    Given I am submitting comments rapidly
    When I try to submit more than 3 comments in 5 minutes
    Then I should be rate-limited
    And subsequent comments should be temporarily blocked
    And I should see a message about rate limiting
    And the blocking should not affect other users

  @comment_email_validation @functional
  Scenario Outline: Email validation for notifications
    Given I want to receive email notifications
    When I enter "<email>" in the email field
    And I submit the comment
    Then the email validation should "<result>"
    And the comment processing should "<action>"

    Examples:
      | email | result | action |
      | valid@example.com | pass | proceed normally |
      | invalid-email | fail | show validation error |
      | user@nonexistent.domain | fail | show validation error |
      | (empty) | pass | proceed without email |

  @comment_notification @email_workflow
  Scenario: Email notification workflow
    Given I have consented to email notifications
    And my comment has been approved
    When another user replies to my comment
    And their reply is approved
    Then I should receive an email notification
    And the email should contain:
      | Content | Description |
      | Reply text | The actual reply content |
      | Post link | Link to the blog post |
      | Unsubscribe link | Easy way to stop notifications |
      | Privacy reminder | How to manage data preferences |

  @comment_accessibility @non_functional
  Scenario: Comment form accessibility
    Given I am using assistive technology
    When I interact with the comment form
    Then all form fields should have proper labels
    And error messages should be announced to screen readers
    And the form should be navigable via keyboard only
    And color should not be the only way to convey information
    And the form should meet WCAG 2.1 AA standards