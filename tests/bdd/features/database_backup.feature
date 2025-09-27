# Feature-level tags (apply to ALL scenarios in this feature)
@epic:EP-00005 @user_story:US-00036 @component:backend @test_type:bdd
Feature: Comprehensive Database Backup Strategy
    As a system administrator
    I want a comprehensive automated backup and disaster recovery system
    So that I can quickly restore the RTM database in case of data loss

    Background:
        Given the application is running
        And the database is clean
        And GDPR compliance is enabled
        And the backup service is configured

    # Smoke test - critical functionality
    @priority:critical @test_category:smoke
    Scenario: Automated daily database backup execution
        Given the backup service is configured with daily schedule
        And the RTM database contains epics, user stories, and defects
        When the daily backup process runs
        Then a complete database snapshot is created
        And the backup file is stored in the configured location
        And the backup is validated for integrity
        And the backup completion is logged with timestamp

    # Performance test - 5-minute recovery requirement
    @priority:critical @test_category:performance
    Scenario: Fast database recovery within 5 minutes
        Given a valid database backup exists from yesterday
        And the current database is corrupted or lost
        And the recovery start time is recorded
        When the emergency restore procedure is initiated
        Then the database is fully restored within 5 minutes
        And all RTM data integrity is verified
        And the GitHub sync status is preserved
        And all epic, user story, and defect relationships are intact

    # Compliance test - GDPR requirements
    @priority:critical @test_category:compliance-gdpr
    Scenario: GDPR-compliant backup data handling
        Given personal data exists in GDPR consent records
        And sensitive user information is stored in the database
        When a database backup is created
        Then all personal data is encrypted in the backup file
        And GDPR retention policies are enforced
        And access controls are properly applied to backup files
        And audit logs record the backup operation with user consent status

    # Error handling - backup corruption detection
    @priority:high @test_category:error-handling
    Scenario: Backup corruption detection and alerting
        Given a corrupted backup file exists in the backup location
        And administrator email alerts are configured
        When the backup validation process runs
        Then the corruption is immediately detected
        And administrator alerts are triggered via email
        And alternative backup sources are identified
        And the system logs the corruption details
        And the backup process retries with alternative storage

    # Edge case - multiple backup destinations
    @priority:medium @test_category:edge
    Scenario: Multiple backup destination functionality
        Given multiple backup destinations are configured (local, cloud, network)
        And all destinations are accessible
        When a backup operation executes
        Then backups are stored in all configured destinations
        And each destination backup is independently validated
        And destination availability is monitored
        And failed destinations are reported without stopping the backup

    # Regression test - Unicode encoding issues (addresses existing GitHub sync issues)
    @priority:medium @test_category:regression
    Scenario: Unicode encoding handling in backups
        Given database contains Unicode characters in epic titles and descriptions
        And user story titles contain special characters and emojis
        And defect descriptions include international characters
        When a backup and restore operation is performed
        Then all Unicode data is preserved correctly
        And no encoding errors occur during the backup process
        And no encoding errors occur during the restore process
        And all special characters are readable after restoration

    # Security test - backup access control
    @priority:high @test_category:compliance-gdpr
    Scenario: Backup file access control and security
        Given backup files contain sensitive RTM and GDPR data
        And proper file permissions are configured
        When backup files are created
        Then only authorized system accounts can access backup files
        And backup files are encrypted at rest
        And backup file transfers use secure protocols
        And access attempts are logged for audit purposes

    # Performance test - large database backup
    @priority:medium @test_category:performance
    Scenario: Large database backup performance
        Given the RTM database contains over 1000 user stories
        And the database contains extensive epic dependency data
        And GDPR consent records span multiple years
        When a full backup operation is initiated
        Then the backup completes within acceptable time limits
        And system performance is not significantly impacted during backup
        And the backup file size is optimized
        And backup progress is reported to administrators

    # Error handling - storage space validation
    @priority:medium @test_category:error-handling
    Scenario: Insufficient storage space handling
        Given backup storage locations have limited space available
        And a backup operation is initiated
        When storage space is insufficient for the backup
        Then the system detects the space limitation
        And alternative storage locations are attempted
        And administrators are alerted about storage issues
        And the backup operation fails gracefully with proper error logging

    # Compliance test - backup retention policy
    @priority:medium @test_category:compliance-gdpr
    Scenario: Automated backup retention policy enforcement
        Given backup retention policy is set to 30 days
        And old backup files exist beyond the retention period
        When the backup cleanup process runs
        Then backups older than 30 days are automatically removed
        And GDPR-compliant data deletion is performed
        And retention policy compliance is logged
        And critical backup files are preserved according to legal requirements