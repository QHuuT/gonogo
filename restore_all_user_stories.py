import sys

sys.path.append("src")
from be.database import get_db_session
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory
from be.models.traceability.defect import Defect

session = get_db_session()

# Clear all user stories first
session.query(UserStory).delete()
session.commit()

# Get epic mapping
epic_map = {}
for epic in session.query(Epic).all():
    epic_map[epic.epic_id] = epic.id
    print(f"Epic: {epic.epic_id} -> {epic.id}")

# UNIQUE USER STORIES from JSON (no duplicates)
all_user_stories = [
    (
        "US-00001",
        "Enhanced RTM filtering system with user story status, test metrics, "
        "and defect management",
        65,
        "EP-00005",
    ),
    ("US-00002", "Enhanced RTM Report UX/UI Design", 66, "EP-00001"),
    ("US-00003", "Implement Comprehensive RTM Search Functionality", 67, "EP-00005"),
    ("US-00004", "Enhanced CLI Test Specification Support", 68, "EP-00007"),
    ("US-00005", "Implement RTM Component Data API and Filtering", 82, "EP-00005"),
    (
        "US-00006",
        "Implement Automated Epic Label Management and Inheritance System",
        87,
        "EP-00005",
    ),
    ("US-00007", "Add Component Columns to RTM Subtables", 84, "EP-00005"),
    ("US-00008", "Enable Horizontal Scrolling for RTM Matrix Tables", 85, "EP-00005"),
    ("US-00009", "GitHub Issue Template Integration", 2, "EP-00004"),
    ("US-00010", "Automated Component Label Management", 77, "EP-00004"),
    ("US-00011", "Fix Defect-User Story Relationship Links", 74, "EP-00005"),
    ("US-00012", "Bidirectional Status Synchronization", 78, "EP-00005"),
    (
        "US-00013",
        "Auto-detect environment information for defect reports",
        6,
        "EP-00004",
    ),
    ("US-00014", "Document RTM link management process", 8, "EP-00005"),
    ("US-00015", "Automated RTM link generation and validation", 9, "EP-00005"),
    ("US-00016", "GitHub Action for automated RTM validation", 10, "EP-00004"),
    ("US-00017", "Comprehensive testing and extensibility framework", 11, "EP-00007"),
    ("US-00018", "Enhanced CLAUDE.md GitHub-First Protocol", 14, "EP-00004"),
    ("US-00019", "Comprehensive GitHub Issue Creation Guide", 15, "EP-00004"),
    ("US-00020", "GitHub Project Management Automation Tool", 16, "EP-00006"),
    ("US-00021", "Test runner with execution modes", 18, "EP-00007"),
    ("US-00022", "Structured logging system", 19, "EP-00007"),
    ("US-00023", "HTML report generation system", 20, "EP-00007"),
    ("US-00024", "Coverage statistics integration", 21, "EP-00007"),
    ("US-00025", "Test failure tracking and reporting", 22, "EP-00007"),
    ("US-00026", "Log-failure association system", 23, "EP-00007"),
    ("US-00027", "GitHub issue creation integration", 24, "EP-00004"),
    ("US-00028", "Test report archiving system", 25, "EP-00007"),
    ("US-00029", "Documentation and user guides", 26, "EP-00004"),
    ("US-00030", "GDPR sanitization strategy", 27, "EP-00003"),
    (
        "US-00031",
        "Complete test runner plugin integration and fix Unicode encoding issues",
        29,
        "EP-00007",
    ),
    (
        "US-00032",
        "Enhanced archive management with current report tracking and automated cleanup",
        34,
        "EP-00007",
    ),
    (
        "US-00033",
        "GitHub Actions automation for issue management and epic linking",
        37,
        "EP-00004",
    ),
    (
        "US-00034",
        "Enhance RTM Matrix Filters with Dropdown and Multiple Criteria Selection",
        86,
        "EP-00005",
    ),
    ("US-00035", "Implement Component Inheritance System", 76, "EP-00005"),
    (
        "US-00037",
        "Design RTM Component Display UI and Responsive Layout",
        81,
        "EP-00005",
    ),
    ("US-00039", "Add Component Field to Epic Database Schema", 73, "EP-00005"),
    ("US-00040", "Enhance Defect Template with Parent Relationships", 72, "EP-00004"),
    ("US-00041", "Add Component Field to User Story Template", 71, "EP-00004"),
    ("US-00042", "Add Component Field to Epic Creation Template", 70, "EP-00004"),
    (
        "US-00043",
        "Complete cleanup of legacy RTM system files and infrastructure",
        69,
        "EP-00005",
    ),
    (
        "US-00051",
        "Requirements analysis and impact assessment for database RTM migration",
        51,
        "EP-00005",
    ),
    (
        "US-00052",
        "Database schema design for traceability relationships",
        52,
        "EP-00005",
    ),
    ("US-00053", "GitHub integration impact analysis", 53, "EP-00004"),
    ("US-00054", "Database models and migration foundation", 54, "EP-00005"),
    ("US-00055", "CLI tools for database RTM management", 55, "EP-00005"),
    ("US-00056", "GitHub Actions database integration", 56, "EP-00004"),
    ("US-00057", "Test execution integration with database", 57, "EP-00007"),
    ("US-00058", "Legacy script migration and deprecation", 58, "EP-00005"),
    ("US-00059", "Dynamic RTM generation and reporting", 59, "EP-00005"),
    ("US-00060", "Comprehensive documentation update for database RTM", 60, "EP-00005"),
    ("US-00061", "Enhanced RTM HTML report with improved traceability", 61, "EP-00005"),
    (
        "US-00062",
        "Program Areas/Capabilities - Epic Grouping and Strategic Management",
        98,
        "EP-00010",
    ),
    ("US-00069", "Audit et deduplication des tests DB", 89, "EP-00007"),
    ("US-00070", "Epic functional dependencies model", 90, "EP-00010"),
    ("US-00071", "Extend Epic model for metrics", 91, "EP-00010"),
    ("US-00072", "Multi-persona project health dashboard", 92, "EP-00010"),
    ("US-00073", "Epic view with visual dependencies", 93, "EP-00010"),
    ("US-00074", "Predefined views & intelligent alerts", 94, "EP-00010"),
    ("US-00075", "Interface responsive personnalisable", 95, "EP-00010"),
    ("US-00076", "Refactoring & cleanup code obsolete", 96, "EP-00005"),
    ("US-00077", "Systeme de tracking velocite historique reel", 97, "EP-00010"),
    (
        "US-00078",
        "Visual Filtering Enhancement for Epic Dependencies Graph",
        99,
        "EP-00010",
    ),
    (
        "US-00079",
        "Enhance RTM Dashboard Component Display and UI Layout",
        80,
        "EP-00005",
    ),
    ("US-00080", "Implement Blocked Flag System for All Issue Types", 79, "EP-00005"),
    (
        "US-00081",
        "Enhance Component Badge Placement in RTM Epic Headers",
        83,
        "EP-00005",
    ),
]

# Create all user stories
created_count = 0
for us_id, title, github_num, epic_id in all_user_stories:
    if epic_id in epic_map:
        us = UserStory(
            user_story_id=us_id,
            epic_id=epic_map[epic_id],
            github_issue_number=github_num,
            title=title,
            description=f"User Story: {title}",
            status="planned",
            github_issue_url=f"https://github.com/QHuuT/gonogo/issues/{github_num}",
            priority="medium",
            component="backend",
            story_points=3,
            implementation_status="todo",
            has_bdd_scenarios=False,
            affects_gdpr=False,
            github_issue_state="open",
        )
        session.add(us)
        created_count += 1
    else:
        print(f"MISSING EPIC: {epic_id} for US {us_id}")

session.commit()

# Final count
total_us = session.query(UserStory).count()
total_epics = session.query(Epic).count()
total_defects = session.query(Defect).count()
print("")
print("COMPLETE DATABASE RESTORED:")
print(f"{total_epics} epics, {total_us} user stories, {total_defects} defects")
print(f"TOTAL: {total_epics + total_us + total_defects} items")
session.close()
