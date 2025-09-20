# BDD Scenarios: GDPR Data Subject Rights
# Linked to: US-007, US-008 (Privacy Rights Management)

@gdpr_rights @legal_compliance @critical
Feature: GDPR Data Subject Rights Management
  As a data subject
  I want to exercise my GDPR privacy rights
  So that I can control my personal data according to EU law

  Background:
    Given the blog application is running
    And GDPR compliance is fully implemented
    And there is personal data in the system for user "user@example.com"

  @data_access @article_15 @gdpr
  Scenario: Right of Access - Request personal data
    Given I am a data subject with email "user@example.com"
    And I have commented on blog posts
    And I have given various consents
    When I submit a data access request
    And I verify my identity via email confirmation
    Then I should receive within 30 days:
      | Data Category | Content |
      | Personal information | Name, email address |
      | Comments | All comments I have posted |
      | Consent records | History of consent given/withdrawn |
      | Processing purposes | Why data was collected |
      | Legal basis | Basis for each processing activity |
      | Retention periods | How long data will be kept |
      | Data recipients | Who has access to the data |

  @data_rectification @article_16 @gdpr
  Scenario: Right to Rectification - Correct inaccurate data
    Given I have personal data stored in the system
    And some of the data is inaccurate
    When I submit a rectification request with:
      | Field | Current Value | Correct Value |
      | Name | Jon Smith | John Smith |
      | Email | old@example.com | new@example.com |
    And I provide evidence of the correct information
    Then the incorrect data should be updated within 30 days
    And I should be notified of the changes
    And the changes should be logged for audit

  @data_erasure @article_17 @gdpr
  Scenario: Right to Erasure - "Right to be Forgotten"
    Given I have personal data stored in the system
    And I want to withdraw from the platform completely
    When I submit an erasure request
    And I confirm my identity
    And I confirm I understand the consequences
    Then within 30 days all my personal data should be deleted:
      | Data Type | Action |
      | Comments | Content anonymized, personal details removed |
      | Email address | Completely deleted |
      | Consent records | Marked as withdrawn and archived |
      | IP addresses | Already anonymized |
    And I should receive confirmation of erasure

  @data_portability @article_20 @gdpr
  Scenario: Right to Data Portability - Export data in structured format
    Given I have personal data stored in the system
    When I request data portability
    And I verify my identity
    Then I should receive my data in machine-readable format (JSON)
    And the export should include:
      | Data Category | Format |
      | Comments | Structured JSON with metadata |
      | Consent history | Timestamped consent records |
      | Profile information | Key-value pairs |
    And the export should be provided within 30 days

  @processing_restriction @article_18 @gdpr
  Scenario: Right to Restriction of Processing
    Given I have disputed the accuracy of my personal data
    When I request restriction of processing
    And the dispute is being investigated
    Then my data should be marked as restricted
    And no further processing should occur except for:
      | Allowed Processing | Reason |
      | Storage | Data preservation |
      | Legal claims | Defense of legal claims |
      | Other person protection | Protection of others' rights |
    And I should be notified before restriction is lifted

  @objection_right @article_21 @gdpr
  Scenario: Right to Object to Processing
    Given my data is being processed for legitimate interests
    When I object to the processing
    And I provide reasons for my objection
    Then the data controller should:
      | Action | Timeframe |
      | Stop processing | Immediately |
      | Assess objection | Within 30 days |
      | Provide response | Within 30 days |
    And processing should only continue if compelling legitimate grounds exist

  @automated_decision_making @article_22 @gdpr
  Scenario: Rights related to Automated Decision-Making
    Given the system uses automated comment moderation
    When I submit a comment that is automatically rejected
    Then I should be informed that automated processing was used
    And I should have the right to:
      | Right | Description |
      | Human intervention | Request human review |
      | Express point of view | Provide my perspective |
      | Contest decision | Challenge the automated decision |

  @request_verification @security
  Scenario: Identity verification for rights requests
    Given someone submits a rights request claiming to be me
    When the request is received
    Then the system should verify identity by:
      | Verification Method | Requirement |
      | Email confirmation | Link sent to registered email |
      | Security questions | Additional verification if needed |
      | Account access | Verification through existing account |
    And no personal data should be disclosed without verification

  @request_tracking @audit_trail
  Scenario: Track rights request processing
    Given I have submitted a data access request
    When the request is being processed
    Then I should be able to track the status:
      | Status | Description | Timeframe |
      | Received | Request logged in system | Immediate |
      | Under review | Identity verification in progress | 1-3 days |
      | Processing | Data compilation in progress | 5-25 days |
      | Completed | Response sent to user | Within 30 days |
    And each status change should be logged for audit

  @request_extension @legal_compliance
  Scenario: Request processing extension
    Given I have submitted a complex data access request
    And the request requires additional time to process
    When the 30-day deadline approaches
    Then I should be notified of the extension
    And the extension should not exceed additional 60 days
    And the reason for extension should be clearly explained
    And my rights should not be prejudiced by the extension

  @third_party_notification @data_sharing
  Scenario: Notify third parties of data changes
    Given my personal data has been shared with third parties
    And I have exercised my right to rectification
    When my data is corrected
    Then all third parties who received the data should be notified
    And they should update their records accordingly
    And I should be informed which third parties were notified

  @rights_fee_waiver @accessibility
  Scenario: Free exercise of rights
    Given I want to exercise any of my GDPR rights
    When I submit a rights request
    Then the request should be processed free of charge
    And no fees should be requested for:
      | Right | Frequency |
      | First request | Always free |
      | Subsequent requests | Free unless manifestly unfounded |
      | Rectification | Always free |
      | Erasure | Always free |

  @complaint_procedure @article_77 @gdpr
  Scenario: Right to lodge a complaint
    Given I am unsatisfied with how my rights request was handled
    When I want to file a complaint
    Then I should be provided with information about:
      | Information | Details |
      | Supervisory authority | CNIL (French data protection authority) |
      | Contact details | CNIL website and contact information |
      | Complaint procedure | How to file a complaint |
      | My rights | Right to judicial remedy |

  @response_timeframe @sla
  Scenario Outline: Rights request response timeframes
    Given I submit a "<request_type>" request
    When the request is processed
    Then I should receive a response within "<timeframe>"
    And the response should be in "<format>"

    Examples:
      | request_type | timeframe | format |
      | Access | 30 days | Structured data export |
      | Rectification | 30 days | Confirmation of changes |
      | Erasure | 30 days | Confirmation of deletion |
      | Portability | 30 days | Machine-readable format |
      | Restriction | Immediately | Confirmation of restriction |