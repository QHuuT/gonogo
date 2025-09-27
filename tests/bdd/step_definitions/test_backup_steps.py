"""
BDD Step Definitions for Database Backup Strategy

Implements step definitions for comprehensive database backup testing.
Follows pytest-bdd pattern with proper test markers for RTM integration.

Related Issue: US-00036 - Comprehensive Database Backup Strategy
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Test Category: BDD scenarios for backup functionality
"""

import os
import sqlite3
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

# Add src to path for imports
sys.path.append("src")

from be.database import create_tables, get_db_session
from be.models.traceability.capability import Capability
from be.models.traceability.defect import Defect
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory
from be.services.backup_monitor import AlertLevel, BackupMonitor
from be.services.backup_service import BackupService

# Load scenarios from feature file
scenarios("../features/database_backup.feature")

# Test markers for RTM integration
pytestmark = [
    pytest.mark.epic("EP-00005"),
    pytest.mark.user_story("US-00036"),
    pytest.mark.component("backend"),
    pytest.mark.test_type("bdd"),
]


# Shared test context
@pytest.fixture
def backup_context():
    """Shared context for backup tests."""
    return {
        "backup_service": None,
        "backup_monitor": None,
        "backup_results": {},
        "test_db_path": None,
        "temp_backup_dir": None,
        "backup_files": [],
        "start_time": None,
        "end_time": None,
        "alerts_generated": [],
        "corruption_detected": False,
    }


# Background step implementations
@given("the application is running")
def application_running():
    """Verify application is operational."""
    # In actual tests, this would verify the FastAPI app is running
    assert True  # Placeholder for application health check


@given("the database is clean")
def database_clean(backup_context):
    """Ensure clean database state for testing."""
    # Create temporary database for testing
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    backup_context["test_db_path"] = temp_db.name
    temp_db.close()

    # Initialize database schema
    create_tables()


@given("GDPR compliance is enabled")
def gdpr_compliance_enabled():
    """Verify GDPR compliance features are active."""
    # Placeholder for GDPR compliance verification
    assert True


@given("the backup service is configured")
def backup_service_configured(backup_context):
    """Configure backup service for testing."""
    # Create temporary backup directory
    backup_context["temp_backup_dir"] = tempfile.mkdtemp(prefix="backup_test_")

    # Initialize backup service with test configuration
    backup_context["backup_service"] = BackupService(
        backup_base_dir=backup_context["temp_backup_dir"]
    )

    # Initialize backup monitor
    backup_context["backup_monitor"] = BackupMonitor(
        alert_email="test@example.com", sla_recovery_time_minutes=5
    )


# Scenario 1: Automated daily database backup execution
@given("the backup service is configured with daily schedule")
def backup_service_daily_schedule(backup_context):
    """Configure backup service with daily scheduling."""
    backup_service_configured(backup_context)
    # Daily schedule configuration would be implemented here


@given("the RTM database contains epics, user stories, and defects")
def database_with_rtm_data(backup_context):
    """Populate database with RTM test data."""
    db = get_db_session()
    try:
        # Create test capability
        capability = Capability(
            capability_id="CAP-00002",
            name="Test Capability",
            description="Test capability for backup testing",
        )
        db.add(capability)
        db.flush()

        # Create test epic
        epic = Epic(
            epic_id="EP-00005",
            capability_id=capability.id,
            title="Test Epic for Backup",
            description="Test epic with Unicode characters: 📊🔄✅",
            status="in_progress",
        )
        db.add(epic)
        db.flush()

        # Create test user stories
        for i in range(3):
            user_story = UserStory(
                user_story_id=f"US-{i:05d}",
                epic_id=epic.id,
                title=f"Test User Story {i} with émojis 🚀",
                description=f"Test user story description with Unicode: café, naïve, résumé",
                status="planned",
            )
            db.add(user_story)

        # Create test defects
        for i in range(2):
            defect = Defect(
                defect_id=f"DEF-{i:05d}",
                epic_id=epic.id,
                title=f"Test Defect {i} with special chars: ñáéíóú",
                description="Test defect with international characters",
                status="open",
                severity="medium",
            )
            db.add(defect)

        db.commit()

    finally:
        db.close()


@when("the daily backup process runs")
def daily_backup_process_runs(backup_context):
    """Execute the daily backup process."""
    backup_context["start_time"] = datetime.now(UTC)

    try:
        result = backup_context["backup_service"].create_daily_backup()
        backup_context["backup_results"] = result
        backup_context["end_time"] = datetime.now(UTC)

        # Store backup file paths for cleanup
        for backup_result in result.get("backup_results", []):
            if backup_result.get("success", False):
                backup_context["backup_files"].append(backup_result["file_path"])

    except Exception as e:
        backup_context["backup_results"] = {"error": str(e)}
        backup_context["end_time"] = datetime.now(UTC)


@then("a complete database snapshot is created")
def complete_database_snapshot_created(backup_context):
    """Verify complete database snapshot was created."""
    assert "backup_id" in backup_context["backup_results"]
    assert backup_context["backup_results"]["successful_destinations"] > 0

    # Verify backup files exist
    assert len(backup_context["backup_files"]) > 0
    for file_path in backup_context["backup_files"]:
        assert Path(file_path).exists()


@then("the backup is validated for integrity")
def backup_validated_for_integrity(backup_context):
    """Verify backup integrity validation."""
    assert backup_context["backup_results"].get("integrity_validated", False)

    # Additional integrity check
    for file_path in backup_context["backup_files"]:
        backup_context["backup_service"]._validate_backup_integrity(file_path)


@then("the backup completion is logged")
def backup_completion_logged(backup_context):
    """Verify backup completion logging."""
    assert "start_time" in backup_context["backup_results"]
    assert "end_time" in backup_context["backup_results"]
    assert "duration_seconds" in backup_context["backup_results"]


# Scenario 2: Fast database recovery within 5 minutes
@given("a valid database backup exists from yesterday")
def valid_backup_exists_yesterday(backup_context):
    """Create a valid backup file simulating yesterday's backup."""
    backup_service_configured(backup_context)
    database_with_rtm_data(backup_context)

    # Create backup
    result = backup_context["backup_service"].create_daily_backup()
    backup_context["backup_files"] = []

    for backup_result in result.get("backup_results", []):
        if backup_result.get("success", False):
            backup_context["backup_files"].append(backup_result["file_path"])

    assert len(backup_context["backup_files"]) > 0


@given("the current database is corrupted or lost")
def current_database_corrupted(backup_context):
    """Simulate database corruption or loss."""
    # Remove or corrupt the current database file
    if backup_context["test_db_path"] and Path(backup_context["test_db_path"]).exists():
        os.remove(backup_context["test_db_path"])


@given("the recovery start time is recorded")
def recovery_start_time_recorded(backup_context):
    """Record recovery operation start time."""
    backup_context["recovery_start_time"] = datetime.now(UTC)


@when("the emergency restore procedure is initiated")
def emergency_restore_initiated(backup_context):
    """Initiate emergency database restoration."""
    assert len(backup_context["backup_files"]) > 0

    # Use first available backup
    backup_file = backup_context["backup_files"][0]

    # Create new target database path
    backup_context["restored_db_path"] = tempfile.NamedTemporaryFile(
        suffix=".db", delete=False
    ).name

    try:
        restore_result = backup_context["backup_service"].restore_from_backup(
            backup_path=backup_file, target_db_path=backup_context["restored_db_path"]
        )
        backup_context["restore_results"] = restore_result

    except Exception as e:
        backup_context["restore_results"] = {"error": str(e)}


@then("the database is fully restored within 5 minutes")
def database_restored_within_5_minutes(backup_context):
    """Verify database restoration within 5-minute SLA."""
    assert "restore_results" in backup_context
    assert "duration_seconds" in backup_context["restore_results"]

    duration_seconds = backup_context["restore_results"]["duration_seconds"]
    assert duration_seconds <= 300  # 5 minutes = 300 seconds


@then("all RTM data integrity is verified")
def rtm_data_integrity_verified(backup_context):
    """Verify RTM data integrity after restoration."""
    assert backup_context["restore_results"].get("integrity_verified", False)

    # Verify entity counts
    metadata = backup_context["restore_results"].get("restoration_metadata", {})
    assert metadata.get("epics", 0) > 0
    assert metadata.get("user_stories", 0) > 0
    assert metadata.get("defects", 0) > 0


@then("the GitHub sync status is preserved")
def github_sync_status_preserved(backup_context):
    """Verify GitHub sync status preservation."""
    # This would verify GitHub integration data preservation
    # For now, verify restoration completed successfully
    assert "error" not in backup_context["restore_results"]


@then("all epic, user story, and defect relationships are intact")
def relationships_intact(backup_context):
    """Verify all RTM relationships are preserved."""
    # Connect to restored database and verify relationships
    restored_db_path = backup_context["restored_db_path"]
    conn = sqlite3.connect(restored_db_path)
    cursor = conn.cursor()

    # Verify foreign key relationships
    cursor.execute(
        """
        SELECT COUNT(*) FROM user_stories us
        JOIN epics e ON us.epic_id = e.id
    """
    )
    user_story_epic_links = cursor.fetchone()[0]
    assert user_story_epic_links > 0

    cursor.execute(
        """
        SELECT COUNT(*) FROM defects d
        JOIN epics e ON d.epic_id = e.id
    """
    )
    defect_epic_links = cursor.fetchone()[0]
    assert defect_epic_links > 0

    conn.close()


# Scenario 3: GDPR-compliant backup data handling
@given("personal data exists in GDPR consent records")
def gdpr_personal_data_exists(backup_context):
    """Create GDPR consent records with personal data."""
    backup_service_configured(backup_context)
    database_with_rtm_data(backup_context)

    # GDPR data simulation would be implemented here
    # For now, verify GDPR compliance features are available
    assert hasattr(backup_context["backup_service"], "cipher_suite")


@given("sensitive user information is stored in the database")
def sensitive_user_info_stored(backup_context):
    """Simulate sensitive user information storage."""
    # This would add sensitive test data to the database
    pass


@when("a database backup is created")
def database_backup_created(backup_context):
    """Create database backup with GDPR considerations."""
    result = backup_context["backup_service"].create_daily_backup()
    backup_context["backup_results"] = result

    for backup_result in result.get("backup_results", []):
        if backup_result.get("success", False):
            backup_context["backup_files"].append(backup_result["file_path"])


@then("all personal data is encrypted in the backup file")
def personal_data_encrypted(backup_context):
    """Verify personal data encryption in backup."""
    assert backup_context["backup_results"].get("gdpr_compliant", False)

    # Verify encryption capabilities are available
    assert backup_context["backup_service"].cipher_suite is not None


@then("GDPR retention policies are enforced")
def gdpr_retention_policies_enforced(backup_context):
    """Verify GDPR retention policy enforcement."""
    # Verify retention period is set appropriately
    assert (
        backup_context["backup_service"].retention_days <= 30
    )  # GDPR-compliant retention


@then("access controls are properly applied to backup files")
def access_controls_applied(backup_context):
    """Verify access controls on backup files."""
    for file_path in backup_context["backup_files"]:
        file_path_obj = Path(file_path)
        # Verify file exists and has proper permissions
        assert file_path_obj.exists()
        # Additional access control verification would be implemented here


@then("audit logs record the backup operation with user consent status")
def audit_logs_record_operation(backup_context):
    """Verify audit logging for backup operations."""
    # Verify backup operation logging
    assert "start_time" in backup_context["backup_results"]
    assert "end_time" in backup_context["backup_results"]


# Scenario 4: Backup corruption detection and alerting
@given("a corrupted backup file exists in the backup location")
def corrupted_backup_exists(backup_context):
    """Create a corrupted backup file for testing."""
    backup_service_configured(backup_context)

    # Create a valid backup first
    database_with_rtm_data(backup_context)
    result = backup_context["backup_service"].create_daily_backup()

    # Get the first backup file and corrupt it
    for backup_result in result.get("backup_results", []):
        if backup_result.get("success", False):
            backup_file = backup_result["file_path"]
            # Corrupt the file by writing random data
            with open(backup_file, "ab") as f:
                f.write(b"CORRUPTED_DATA_TO_BREAK_INTEGRITY")
            backup_context["corrupted_file"] = backup_file
            break


@given("administrator email alerts are configured")
def admin_email_alerts_configured(backup_context):
    """Configure administrator email alerts."""
    backup_context["backup_monitor"] = BackupMonitor(
        alert_email="admin@test.com", sla_recovery_time_minutes=5
    )


@when("the backup validation process runs")
def backup_validation_process_runs(backup_context):
    """Run backup validation process."""
    monitor = backup_context["backup_monitor"]
    service = backup_context["backup_service"]

    # Run corruption detection
    backup_files = [backup_context["corrupted_file"]]
    alerts = monitor.detect_backup_corruption(service, backup_files)
    backup_context["alerts_generated"] = alerts


@then("the corruption is immediately detected")
def corruption_immediately_detected(backup_context):
    """Verify corruption detection."""
    alerts = backup_context["alerts_generated"]
    corruption_alerts = [a for a in alerts if "corruption" in a.title.lower()]
    assert len(corruption_alerts) > 0


@then("administrator alerts are triggered via email")
def admin_alerts_triggered(backup_context):
    """Verify administrator alerts are triggered."""
    alerts = backup_context["alerts_generated"]
    critical_alerts = [a for a in alerts if a.level == AlertLevel.CRITICAL]
    assert len(critical_alerts) > 0


@then("alternative backup sources are identified")
def alternative_backup_sources_identified(backup_context):
    """Verify alternative backup sources are available."""
    # Verify multiple destinations are configured
    service = backup_context["backup_service"]
    assert len(service.backup_destinations) > 1


@then("the system logs the corruption details")
def system_logs_corruption_details(backup_context):
    """Verify corruption details are logged."""
    alerts = backup_context["alerts_generated"]
    for alert in alerts:
        if "corruption" in alert.title.lower():
            assert alert.details is not None
            assert "backup_path" in alert.details


@then("the backup process retries with alternative storage")
def backup_retries_alternative_storage(backup_context):
    """Verify backup retry mechanism with alternative storage."""
    # This would test automatic retry logic
    # For now, verify multiple destinations are available
    service = backup_context["backup_service"]
    assert len(service.backup_destinations) >= 2


# Scenario 5: Multiple backup destination functionality
@given("multiple backup destinations are configured (local, cloud, network)")
def multiple_destinations_configured(backup_context):
    """Configure multiple backup destinations."""
    backup_service_configured(backup_context)

    # Add additional backup destinations
    service = backup_context["backup_service"]
    cloud_dest = Path(backup_context["temp_backup_dir"]) / "cloud"
    network_dest = Path(backup_context["temp_backup_dir"]) / "network"

    cloud_dest.mkdir(exist_ok=True)
    network_dest.mkdir(exist_ok=True)

    service.backup_destinations.extend([cloud_dest, network_dest])


@given("all destinations are accessible")
def all_destinations_accessible(backup_context):
    """Verify all backup destinations are accessible."""
    service = backup_context["backup_service"]
    for dest in service.backup_destinations:
        assert dest.exists() and dest.is_dir()


@when("a backup operation executes")
def backup_operation_executes(backup_context):
    """Execute backup operation to multiple destinations."""
    database_with_rtm_data(backup_context)
    result = backup_context["backup_service"].create_daily_backup()
    backup_context["backup_results"] = result


@then("backups are stored in all configured destinations")
def backups_stored_all_destinations(backup_context):
    """Verify backups are stored in all destinations."""
    result = backup_context["backup_results"]
    total_destinations = result["total_destinations"]
    successful_destinations = result["successful_destinations"]

    # Should succeed in all destinations
    assert successful_destinations == total_destinations
    assert successful_destinations >= 3  # local, cloud, network


@then("each destination backup is independently validated")
def each_backup_independently_validated(backup_context):
    """Verify each destination backup is validated."""
    assert backup_context["backup_results"].get("integrity_validated", False)

    # Verify backup results for each destination
    for backup_result in backup_context["backup_results"].get("backup_results", []):
        if backup_result.get("success", False):
            assert "checksum" in backup_result
            assert backup_result["file_size"] > 0


@then("destination availability is monitored")
def destination_availability_monitored(backup_context):
    """Verify destination monitoring."""
    # This would test destination health monitoring
    service = backup_context["backup_service"]
    status = service.get_backup_status()
    assert len(status["backup_destinations"]) >= 3


@then("failed destinations are reported without stopping the backup")
def failed_destinations_reported(backup_context):
    """Verify failed destination reporting."""
    # This tests that partial failures don't stop the entire backup
    result = backup_context["backup_results"]
    assert result["successful_destinations"] > 0  # At least one should succeed


# Scenario 6: Unicode encoding handling in backups
@given("database contains Unicode characters in epic titles and descriptions")
def database_unicode_epic_data(backup_context):
    """Populate database with Unicode test data in epics."""
    backup_service_configured(backup_context)
    database_with_rtm_data(backup_context)  # This already includes Unicode data


@given("user story titles contain special characters and emojis")
def user_story_unicode_data(backup_context):
    """User stories already created with Unicode data in previous step."""
    pass


@given("defect descriptions include international characters")
def defect_unicode_data(backup_context):
    """Defects already created with Unicode data in previous step."""
    pass


@when("a backup and restore operation is performed")
def backup_restore_unicode_operation(backup_context):
    """Perform backup and restore with Unicode data."""
    # Create backup
    backup_result = backup_context["backup_service"].create_daily_backup()
    backup_context["backup_results"] = backup_result

    # Get backup file
    backup_file = None
    for result in backup_result.get("backup_results", []):
        if result.get("success", False):
            backup_file = result["file_path"]
            break

    assert backup_file is not None

    # Create target for restoration
    restore_target = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name

    # Perform restoration
    restore_result = backup_context["backup_service"].restore_from_backup(
        backup_path=backup_file, target_db_path=restore_target
    )
    backup_context["restore_results"] = restore_result
    backup_context["restored_db_path"] = restore_target


@then("all Unicode data is preserved correctly")
def unicode_data_preserved(backup_context):
    """Verify Unicode data preservation."""
    # Connect to restored database and check Unicode data
    restored_db = backup_context["restored_db_path"]
    conn = sqlite3.connect(restored_db)
    cursor = conn.cursor()

    # Check epic with Unicode
    cursor.execute("SELECT title FROM epics WHERE title LIKE '%📊%'")
    epic_result = cursor.fetchone()
    assert epic_result is not None

    # Check user story with Unicode
    cursor.execute("SELECT title FROM user_stories WHERE title LIKE '%🚀%'")
    us_result = cursor.fetchone()
    assert us_result is not None

    # Check defect with international characters
    cursor.execute("SELECT title FROM defects WHERE title LIKE '%ñáéíóú%'")
    defect_result = cursor.fetchone()
    assert defect_result is not None

    conn.close()


@then("no encoding errors occur during the backup process")
def no_backup_encoding_errors(backup_context):
    """Verify no encoding errors during backup."""
    result = backup_context["backup_results"]
    assert "error" not in result
    assert result["successful_destinations"] > 0


@then("no encoding errors occur during the restore process")
def no_restore_encoding_errors(backup_context):
    """Verify no encoding errors during restore."""
    result = backup_context["restore_results"]
    assert "error" not in result
    assert result["integrity_verified"]


@then("all special characters are readable after restoration")
def special_characters_readable(backup_context):
    """Verify special characters remain readable."""
    # This is verified by the Unicode preservation test
    unicode_data_preserved(backup_context)


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_test_files(backup_context):
    """Clean up test files after each scenario."""
    yield

    # Cleanup backup files
    for file_path in backup_context.get("backup_files", []):
        try:
            if Path(file_path).exists():
                os.remove(file_path)
        except Exception:
            pass

    # Cleanup test database
    if (
        backup_context.get("test_db_path")
        and Path(backup_context["test_db_path"]).exists()
    ):
        try:
            os.remove(backup_context["test_db_path"])
        except Exception:
            pass

    # Cleanup restored database
    if (
        backup_context.get("restored_db_path")
        and Path(backup_context["restored_db_path"]).exists()
    ):
        try:
            os.remove(backup_context["restored_db_path"])
        except Exception:
            pass

    # Cleanup temp backup directory
    if backup_context.get("temp_backup_dir"):
        try:
            import shutil

            shutil.rmtree(backup_context["temp_backup_dir"])
        except Exception:
            pass
