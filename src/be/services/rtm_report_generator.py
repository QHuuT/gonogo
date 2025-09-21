"""
RTM Report Generator Service

Generates dynamic RTM reports in multiple formats from database data.
Supports real-time reporting, filtering, and export capabilities.

Related Issue: US-00059 - Dynamic RTM generation and reporting
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ..models.traceability import Defect, Epic, Test, UserStory


class RTMReportGenerator:
    """Dynamic RTM report generator with multiple output formats."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def generate_json_matrix(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate RTM matrix in JSON format."""
        # Apply filters to get relevant data
        epics = self._get_filtered_epics(filters)

        matrix_data = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_epics": len(epics),
                "filters_applied": {k: v for k, v in filters.items() if v is not None},
            },
            "epics": [],
        }

        for epic in epics:
            epic_data = self._build_epic_data(epic, filters)
            matrix_data["epics"].append(epic_data)

        return matrix_data

    def generate_markdown_matrix(self, filters: Dict[str, Any]) -> str:
        """Generate RTM matrix in Markdown format."""
        epics = self._get_filtered_epics(filters)

        markdown = "# Dynamic Requirements Traceability Matrix\n\n"
        markdown += (
            f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        )
        markdown += f"**Total Epics**: {len(epics)}\n\n"

        # Epic to User Story mapping table
        markdown += "## Epic to User Story Mapping\n\n"
        markdown += "| Epic ID | Epic Name | User Stories | Story Points | Status | Progress |\n"
        markdown += "|---------|-----------|--------------|--------------|--------|----------|\n"

        for epic in epics:
            user_stories = (
                self.db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
            )
            us_list = ", ".join(
                [f"[{us.user_story_id}](#{us.user_story_id})" for us in user_stories]
            )
            total_points = sum(us.story_points for us in user_stories)
            completed_points = sum(
                us.story_points
                for us in user_stories
                if us.implementation_status in ["done", "completed"]
            )
            progress = (
                f"{(completed_points/total_points*100):.1f}%"
                if total_points > 0
                else "0%"
            )

            markdown += f"| **{epic.epic_id}** | {epic.title} | {us_list} | {total_points} | {epic.status} | {progress} |\n"

        # Test coverage section if requested
        if filters.get("include_tests", True):
            markdown += "\n## Test Coverage Summary\n\n"
            markdown += (
                "| Epic ID | Total Tests | Unit | Integration | BDD | Pass Rate |\n"
            )
            markdown += (
                "|---------|-------------|------|-------------|-----|-----------|\n"
            )

            for epic in epics:
                tests = self.db.query(Test).filter(Test.epic_id == epic.id).all()
                test_counts = self._get_test_counts(tests)
                pass_rate = self._calculate_pass_rate(tests)

                markdown += f"| {epic.epic_id} | {len(tests)} | {test_counts['unit']} | {test_counts['integration']} | {test_counts['bdd']} | {pass_rate:.1f}% |\n"

        # Defect tracking section if requested
        if filters.get("include_defects", True):
            markdown += "\n## Defect Tracking\n\n"
            markdown += (
                "| Epic ID | Total Defects | Critical | High | Open | Security |\n"
            )
            markdown += (
                "|---------|---------------|----------|------|------|----------|\n"
            )

            for epic in epics:
                defects = self.db.query(Defect).filter(Defect.epic_id == epic.id).all()
                defect_summary = self._get_defect_summary(defects)

                markdown += f"| {epic.epic_id} | {len(defects)} | {defect_summary['critical']} | {defect_summary['high']} | {defect_summary['open']} | {defect_summary['security']} |\n"

        return markdown

    def generate_html_matrix(self, filters: Dict[str, Any]) -> str:
        """Generate RTM matrix in HTML format with Python-based filtering."""
        # Extract filter parameters
        epic_filter = filters.get("epic_filter", "all")
        us_status_filter = filters.get("us_status_filter", "all")
        test_type_filter = filters.get(
            "test_type_filter", "all"
        )  # Default to all tests
        defect_priority_filter = filters.get("defect_priority_filter", "all")
        defect_status_filter = filters.get("defect_status_filter", "all")

        epics = self._get_filtered_epics(filters)

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dynamic RTM Matrix - GoNoGo</title>

    <!-- Design System and Component Styles -->
    <link rel="stylesheet" href="/static/css/design-system.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/rtm-components.css">

    <!-- Accessibility and SEO Meta Tags -->
    <meta name="description" content="Requirements Traceability Matrix for GoNoGo project - Interactive dashboard showing epic progress, user stories, tests, and defects">
    <meta name="keywords" content="RTM, requirements, traceability, matrix, GoNoGo, project management">
    <meta name="author" content="GoNoGo Project Team">
    <link rel="canonical" href="/rtm/matrix">

    <!-- Favicon and Touch Icons -->
    <link rel="icon" type="image/x-icon" href="/static/images/favicon.ico">
    <link rel="apple-touch-icon" sizes="180x180" href="/static/images/apple-touch-icon.png">

    <!-- Performance Optimizations -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="dns-prefetch" href="//fonts.googleapis.com">

    <!-- Open Graph Meta Tags for Social Sharing -->
    <meta property="og:title" content="RTM Matrix - GoNoGo Project">
    <meta property="og:description" content="Interactive Requirements Traceability Matrix dashboard">
    <meta property="og:type" content="website">
    <meta property="og:url" content="/rtm/matrix">

    <!-- Skip Link for Accessibility -->
    <style>
        .skip-link {{
            position: absolute;
            top: -40px;
            left: 6px;
            background: var(--color-bg-primary);
            color: var(--color-text-primary);
            padding: var(--space-sm) var(--space-base);
            border-radius: var(--radius-base);
            text-decoration: none;
            z-index: var(--z-tooltip);
            transition: top var(--transition-fast);
        }}
        .skip-link:focus {{
            top: 6px;
        }}
    </style>

    <!-- Enhanced RTM Interactive Features -->
    <script src="/static/js/rtm-interactions.js" defer></script>
</head>
<body>
    <!-- Skip Link for Accessibility -->
    <a href="#main-content" class="skip-link">Skip to main content</a>

    <!-- Enhanced Page Header -->
    <header class="page-header" role="banner">
        <div class="page-header__content">
            <h1 class="page-header__title">Requirements Traceability Matrix</h1>
            <p class="page-header__subtitle">Interactive dashboard for GoNoGo project requirements tracking</p>
            <div class="page-header__meta">
                <div class="page-header__meta-item">
                    <span>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</span>
                </div>
                <div class="page-header__meta-item">
                    <span>Total Epics: {len(epics)}</span>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content Container -->
    <main id="main-content" class="rtm-container" role="main">

        <!-- Enhanced Filter Toolbar -->
        <div class="filter-toolbar" role="toolbar" aria-label="RTM Filters">
            <!-- TEMPORARILY DISABLED: Search feature needs proper implementation
            <div class="filter-group">
                <label class="filter-group__label" for="rtm-search">Search:</label>
                <div class="search-box">
                    <span class="search-box__icon">🔍</span>
                    <input
                        type="text"
                        id="rtm-search"
                        class="search-box__input"
                        placeholder="Search epics, user stories, tests, or defects..."
                        aria-label="Search RTM content"
                    >
                    <button class="search-box__clear" id="clear-search" type="button" aria-label="Clear search">✕</button>
                </div>
            </div>
            -->

            <div class="filter-group">
                <span class="filter-group__label">Epic Status:</span>
                <div class="filter-group__controls">
                    <button class="filter-button filter-button--active" onclick="filterByStatus('all')" data-filter-group="epic-status" data-filter-value="all">All</button>
                    <button class="filter-button" onclick="filterByStatus('planned')" data-filter-group="epic-status" data-filter-value="planned">Planned</button>
                    <button class="filter-button" onclick="filterByStatus('in_progress')" data-filter-group="epic-status" data-filter-value="in_progress">In Progress</button>
                    <button class="filter-button" onclick="filterByStatus('completed')" data-filter-group="epic-status" data-filter-value="completed">Completed</button>
                    <button class="filter-button" onclick="filterByStatus('blocked')" data-filter-group="epic-status" data-filter-value="blocked">Blocked</button>
                </div>
            </div>

            <div class="export-toolbar">
                <button class="export-button" data-export-format="csv" title="Export to CSV">
                    CSV
                </button>
                <button class="export-button" data-export-format="json" title="Export to JSON">
                    JSON
                </button>
            </div>
        </div>

        <!-- Search Results Count -->
        <div class="search-results-count" style="display: none;" role="status" aria-live="polite"></div>

        <!-- Section Separator -->
        <div class="section-separator">
            <span class="section-separator__content">Epic Progress Overview</span>
        </div>
"""

        for epic in epics:
            epic_data = self._build_epic_data(epic, filters)
            progress = epic_data["metrics"]["completion_percentage"]

            epic_title_link = self._render_epic_title_link(
                epic.epic_id, epic.title, epic.github_issue_number
            )
            clean_description = self._extract_epic_description(epic.description)

            # Extract metrics for easier use in template
            metrics = epic_data["metrics"]
            user_stories_count = metrics["user_stories_count"]
            completed_points = metrics["completed_story_points"]
            total_points = metrics["total_story_points"]
            tests_count = metrics["tests_count"]
            test_pass_rate = metrics["test_pass_rate"]
            tests_passed = metrics["tests_passed"]
            tests_failed = metrics["tests_failed"]
            tests_not_run = metrics["tests_not_run"]
            defects_count = metrics["defects_count"]

            html += f"""
        <!-- Epic Card with Enhanced Design -->
        <article class="epic-card" data-status="{epic.status}" data-epic-id="{epic.epic_id}" aria-labelledby="epic-{epic.epic_id}-title">
            <header class="epic-header" role="button" tabindex="0" aria-expanded="false" aria-controls="epic-{epic.epic_id}">
                <div class="epic-header__top">
                    <h2 id="epic-{epic.epic_id}-title" class="epic-title-link">
                        {epic_title_link}
                    </h2>
                    <span class="badge badge--status badge--status-{epic.status.replace('_', '-')}" aria-label="Epic status: {epic.status.replace('_', ' ').title()}">
                        {epic.status.replace('_', ' ').title()}
                    </span>
                </div>
                <!-- Epic Progress with Enhanced Visual Design (moved to header for visibility) -->
                <div class="epic-progress" aria-label="Epic Progress">
                    <div class="epic-progress__label">
                        <span>Progress</span>
                        <span><strong>{progress:.1f}% Complete</strong></span>
                    </div>
                    <div class="epic-progress__bar" role="progressbar" aria-valuenow="{progress:.1f}" aria-valuemin="0" aria-valuemax="100" aria-label="Epic completion progress">
                        <div class="epic-progress__fill" style="width: {progress}%"></div>
                    </div>
                </div>
            </header>

            <div class="epic-content" id="epic-{epic.epic_id}" aria-labelledby="epic-{epic.epic_id}-title" style="display: none;">
                <!-- Epic Description -->
                <section class="epic-description" aria-label="Epic Description">
                    <h3 class="sr-only">Description</h3>
                    <p>{clean_description.replace(chr(10), '<br>')}</p>
                </section>


                <!-- Enhanced Metrics Dashboard -->
                <section class="metrics-dashboard" aria-label="Epic Metrics Overview">
                    <h3 class="metrics-dashboard__title">Overview Metrics</h3>
                    <div class="metrics-grid">
                        <div class="metric-card metric-card--info" aria-label="User Stories count">
                            <div class="metric-card__number">{user_stories_count}</div>
                            <div class="metric-card__label">User Stories</div>
                            <div class="metric-card__description">Total stories in epic</div>
                        </div>
                        <div class="metric-card metric-card--{('success' if completed_points == total_points else 'warning' if completed_points > 0 else 'info')}" aria-label="Story Points progress">
                            <div class="metric-card__number">{completed_points}/{total_points}</div>
                            <div class="metric-card__label">Story Points</div>
                            <div class="metric-card__description">Completed vs Total</div>
                        </div>
                        <div class="metric-card metric-card--{('success' if tests_count > 0 else 'info')}" aria-label="Tests count">
                            <div class="metric-card__number">{tests_count}</div>
                            <div class="metric-card__label">Tests</div>
                            <div class="metric-card__description">Total test cases</div>
                        </div>
                        <div class="metric-card metric-card--{('success' if test_pass_rate >= 80 else 'warning' if test_pass_rate >= 60 else 'danger')}" aria-label="Test pass rate">
                            <div class="metric-card__number">{test_pass_rate:.1f}%</div>
                            <div class="metric-card__label">Pass Rate</div>
                            <div class="metric-card__description">{tests_passed} passed, {tests_failed} failed, {tests_not_run} not run</div>
                        </div>
                        <div class="metric-card metric-card--{('danger' if defects_count > 0 else 'success')}" aria-label="Defects count">
                            <div class="metric-card__number">{defects_count}</div>
                            <div class="metric-card__label">Defects</div>
                            <div class="metric-card__description">Open issues to resolve</div>
                        </div>
                    </div>
                </section>

                <!-- User Stories Collapsible Section -->
                <section class="collapsible" aria-label="User Stories">
                    <input type="checkbox" class="collapsible__toggle" id="toggle-user-stories-{epic.epic_id}">
                    <label for="toggle-user-stories-{epic.epic_id}" class="collapsible__header">
                        <h3 class="collapsible__title">User Stories ({user_stories_count})</h3>
                        <span class="collapsible__icon">▼</span>
                    </label>
                    <div class="collapsible__content" id="user-stories-{epic.epic_id}">
                        <div class="collapsible__body">
                            <!-- User Stories Filter Section -->
                            <div class="filter-section" role="group" aria-label="User Stories Filters">
                                <h4 class="filter-section__title">Filter User Stories:</h4>
                                <div class="filter-section__buttons">
                                    <button class="filter-button filter-button--us filter-button--active"
                                            data-us-status="all"
                                            data-filter-group="epic-{epic.epic_id}-us"
                                            data-filter-value="all"
                                            onclick="filterUserStoriesByStatus('{epic.epic_id}', 'all')"
                                            aria-pressed="true">All</button>
                                    <button class="filter-button filter-button--us"
                                            data-us-status="planned"
                                            data-filter-group="epic-{epic.epic_id}-us"
                                            data-filter-value="planned"
                                            onclick="filterUserStoriesByStatus('{epic.epic_id}', 'planned')"
                                            aria-pressed="false">Planned</button>
                                    <button class="filter-button filter-button--us"
                                            data-us-status="in_progress"
                                            data-filter-group="epic-{epic.epic_id}-us"
                                            data-filter-value="in_progress"
                                            onclick="filterUserStoriesByStatus('{epic.epic_id}', 'in_progress')"
                                            aria-pressed="false">In Progress</button>
                                    <button class="filter-button filter-button--us"
                                            data-us-status="completed"
                                            data-filter-group="epic-{epic.epic_id}-us"
                                            data-filter-value="completed"
                                            onclick="filterUserStoriesByStatus('{epic.epic_id}', 'completed')"
                                            aria-pressed="false">Completed</button>
                                    <button class="filter-button filter-button--us"
                                            data-us-status="blocked"
                                            data-filter-group="epic-{epic.epic_id}-us"
                                            data-filter-value="blocked"
                                            onclick="filterUserStoriesByStatus('{epic.epic_id}', 'blocked')"
                                            aria-pressed="false">Blocked</button>
                                </div>
                                <div class="us-count-display filter-count" role="status" aria-live="polite">Showing all user stories</div>
                            </div>

                            <!-- User Stories Table -->
                            <div class="rtm-table-container">
                                <table class="rtm-table" role="table" aria-label="User Stories for {epic.epic_id}">
                                <thead class="rtm-table__header">
                                    <tr><th scope="col">ID</th><th scope="col">Title</th><th scope="col">Story Points</th><th scope="col">Status</th></tr>
                                </thead>
                                <tbody class="rtm-table__body">
"""
            for us in epic_data["user_stories"]:
                user_story_link = self._render_user_story_id_link(
                    us["user_story_id"], us.get("github_issue_number")
                )
                status_normalized = us["implementation_status"].replace("_", "-")
                html += f"""
                                    <tr class="rtm-table__row us-row" data-us-status="{us['implementation_status']}">
                                        <td>{user_story_link}</td>
                                        <td>{us["title"]}</td>
                                        <td>{us["story_points"]}</td>
                                        <td><span class="badge badge--status badge--status-{status_normalized}">{us["implementation_status"].replace('_', ' ').title()}</span></td>
                                    </tr>
"""

            # Add dynamic empty state row for user stories
            html += """
                                    <!-- Empty state row for user stories (hidden by default, shown when filtered count = 0) -->
                                    <tr class="empty-state-row" style="display: none;">
                                        <td colspan="4" style="text-align: center; color: #7f8c8d; font-style: italic;">No user stories match the current filter</td>
                                    </tr>
                                </tbody>
                            </table>
                            </div>
                </section>
"""

            html += f"""
                <!-- Tests Collapsible Section -->
                <section class="collapsible" aria-label="Tests">
                    <input type="checkbox" class="collapsible__toggle" id="toggle-tests-{epic.epic_id}">
                    <label for="toggle-tests-{epic.epic_id}" class="collapsible__header">
                        <h3 class="collapsible__title">Test Coverage ({tests_count})</h3>
                        <span class="collapsible__icon">▼</span>
                    </label>
                    <div class="collapsible__content" id="tests-{epic.epic_id}">
                        <div class="collapsible__body">
                            <!-- Enhanced Test Metrics Dashboard -->
                            <div class="metrics-dashboard">
                                <h4 class="metrics-dashboard__title">Test Metrics</h4>
                                <div class="metrics-grid">
                                    <div class="metric-card metric-card--info" aria-label="Total tests count">
                                                    <div class="metric-card__number">{tests_count}</div>
                                        <div class="metric-card__label">Total Tests</div>
                                        <div class="metric-card__description">Across all test types</div>
                                    </div>
                                    <div class="metric-card metric-card--{('success' if test_pass_rate >= 80 else 'warning' if test_pass_rate >= 60 else 'danger')}" aria-label="Test pass rate">
                                                    <div class="metric-card__number">{test_pass_rate:.1f}%</div>
                                        <div class="metric-card__label">Pass Rate</div>
                                        <div class="metric-card__description">Overall success rate</div>
                                    </div>
                                    <div class="metric-card metric-card--success" aria-label="Passed tests">
                                        <div class="metric-card__number">{tests_passed}</div>
                                        <div class="metric-card__label">Passed</div>
                                        <div class="metric-card__description">Successfully executed</div>
                                    </div>
                                    <div class="metric-card metric-card--danger" aria-label="Failed tests">
                                        <div class="metric-card__number">{tests_failed}</div>
                                        <div class="metric-card__label">Failed</div>
                                        <div class="metric-card__description">Need attention</div>
                                    </div>
                                    <div class="metric-card metric-card--warning" aria-label="Tests not run">
                                        <div class="metric-card__number">{tests_not_run}</div>
                                        <div class="metric-card__label">Not Run</div>
                                        <div class="metric-card__description">Pending execution</div>
                                    </div>
                                </div>

                                <!-- Test Type Breakdown -->
                                <div class="test-breakdown">
                                    <h5 class="test-breakdown__title">Test Distribution by Type</h5>"""

            # Add test type breakdown HTML
            html += self._generate_test_type_breakdown_html(epic_data.get("tests", []))

            html += f"""
                                </div>
                            </div>

                            <!-- Test Filter Section -->
                            <div class="filter-section" role="group" aria-label="Test Filters">
                                <h4 class="filter-section__title">Filter Tests:</h4>
                                <div class="filter-section__buttons">
                                    <button class="filter-button filter-button--test"
                                            data-test-type="e2e"
                                            data-filter-group="epic-{epic.epic_id}-test"
                                            data-filter-value="e2e"
                                            onclick="filterTestsByType('{epic.epic_id}', 'e2e')"
                                            aria-pressed="false">E2E Only</button>
                                    <button class="filter-button filter-button--test"
                                            data-test-type="unit"
                                            data-filter-group="epic-{epic.epic_id}-test"
                                            data-filter-value="unit"
                                            onclick="filterTestsByType('{epic.epic_id}', 'unit')"
                                            aria-pressed="false">Unit</button>
                                    <button class="filter-button filter-button--test"
                                            data-test-type="integration"
                                            data-filter-group="epic-{epic.epic_id}-test"
                                            data-filter-value="integration"
                                            onclick="filterTestsByType('{epic.epic_id}', 'integration')"
                                            aria-pressed="false">Integration</button>
                                    <button class="filter-button filter-button--test"
                                            data-test-type="security"
                                            data-filter-group="epic-{epic.epic_id}-test"
                                            data-filter-value="security"
                                            onclick="filterTestsByType('{epic.epic_id}', 'security')"
                                            aria-pressed="false">Security</button>
                                    <button class="filter-button filter-button--test filter-button--active"
                                            data-test-type="all"
                                            data-filter-group="epic-{epic.epic_id}-test"
                                            data-filter-value="all"
                                            onclick="filterTestsByType('{epic.epic_id}', 'all')"
                                            aria-pressed="true">All Tests</button>
                                </div>
                                <div class="test-count-display filter-count" role="status" aria-live="polite">Showing all tests</div>
                            </div>

                            <!-- Test Traceability Table -->
                            <div class="rtm-table-container">
                            <table class="rtm-table" role="table" aria-label="Test Traceability for {epic.epic_id}">
                                <thead class="rtm-table__header">
                                    <tr><th scope="col">Test Type</th><th scope="col">Function/Scenario</th><th scope="col">Last Execution</th><th scope="col">Status</th><th scope="col">File Path</th></tr>
                                </thead>
                                <tbody class="rtm-table__body">
"""

            # Add test information
            tests_list = epic_data.get("tests", [])

            for test in tests_list:

                # Format last execution time
                last_execution = test.get("last_execution_time", "")
                if last_execution:
                    try:
                        if isinstance(last_execution, str):
                            exec_time = datetime.fromisoformat(
                                last_execution.replace("Z", "+00:00")
                            )
                        else:
                            exec_time = last_execution
                        formatted_time = exec_time.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_time = str(last_execution)
                else:
                    formatted_time = "Never"

                # Get test function or BDD scenario name
                test_name = test.get("test_function_name") or test.get(
                    "bdd_scenario_name", ""
                )

                # Status styling
                status = test.get("last_execution_status", "unknown")
                status_class = (
                    "passed"
                    if status == "passed"
                    else "failed" if status == "failed" else "skipped"
                )
                # Test status icons removed for accessibility

                test_type_lower = test.get("test_type", "").lower()
                file_path = test.get("test_file_path", "")

                html += f"""
                        <tr class="test-row" data-test-type="{test_type_lower}">
                            <td><span class="badge badge--test-type">{test.get("test_type", "").upper()}</span></td>
                            <td class="function-cell">{test_name}</td>
                            <td>{formatted_time}</td>
                            <td><span class="badge badge--status badge--status-{status_class}">{status.title()}</span></td>
                            <td>
                                <div class="file-path-container">
                                    <button class="copy-btn" onclick="copyToClipboard('{file_path.replace(chr(92), chr(92) + chr(92))}', this)" title="Copy full path" aria-label="Copy full file path">
                                        <span class="copy-btn__text">COPY</span>
                                    </button>
                                    <span class="copy-feedback" id="feedback-{test.get('test_id', '')}" style="display: none;">Copied!</span>
                                </div>
                            </td>
                        </tr>
"""

            # If no tests, show message
            if not epic_data.get("tests", []):
                html += """
                        <tr>
                            <td colspan="5" style="text-align: center; color: #7f8c8d; font-style: italic;">No tests available for this epic</td>
                        </tr>
"""

            # For now, keep the original tests table structure until we refactor the test rows generation
            # test_headers = "<tr><th scope='col'>Test Type</th><th scope='col'>Function/Scenario</th><th scope='col'>Last Execution</th><th scope='col'>Status</th><th scope='col'>File Path</th></tr>"
            # tests_is_expanded = filters.get(f'tests_{epic.epic_id}') == 'expand'
            # tests_table = self._generate_table_with_row_limiting(
            #     "",  # We'll need to refactor the test rows generation
            #     "tests",
            #     len(epic_data.get("tests", [])),
            #     test_headers,
            #     f"Test Traceability for {epic.epic_id}",
            #     epic.epic_id,
            #     tests_is_expanded
            # )
            # For now, let's keep the original structure and add the enhancement later
            # Add dynamic empty state row for tests
            html += (
                """
                                    <!-- Empty state row for tests (hidden by default, shown when filtered count = 0) -->
                                    <tr class="empty-state-row" style="display: none;">
                                        <td colspan="5" style="text-align: center; color: #7f8c8d; font-style: italic;">No tests match the current filter</td>
                                    </tr>
                    </tbody>
                </table>
                </div>
                        </div>
                    </div>
                </section>

                <!-- Defect Management Collapsible Section -->
                <section class="collapsible" aria-label="Defect Management">
                    <input type="checkbox" class="collapsible__toggle" id="toggle-defects-"""
                + epic.epic_id
                + """">
                    <label for="toggle-defects-"""
                + epic.epic_id
                + """" class="collapsible__header">
                        <h3 class="collapsible__title">Defect Management ("""
                + str(defects_count)
                + """)</h3>
                        <span class="collapsible__icon">▼</span>
                    </label>
                    <div class="collapsible__content" id="defects-"""
                + epic.epic_id
                + """">
                        <div class="collapsible__body">
                            <!-- Enhanced Defect Metrics Dashboard -->
                            <div class="metrics-dashboard">
                                <h4 class="metrics-dashboard__title">Defect Metrics</h4>
                                <div class="metrics-grid">"""
            )

            # Add defect metrics here
            defects = epic_data.get("defects", [])
            critical_count = sum(1 for d in defects if d.get("priority") == "critical")
            high_count = sum(1 for d in defects if d.get("priority") == "high")
            open_count = sum(
                1 for d in defects if d.get("status") in ["open", "in_progress"]
            )
            security_count = sum(
                1 for d in defects if d.get("is_security_issue", False)
            )

            html += f"""
                                    <div class="metric-card metric-card--{('danger' if defects_count > 0 else 'success')}" aria-label="Total defects">
                                                    <div class="metric-card__number">{defects_count}</div>
                                        <div class="metric-card__label">Total Defects</div>
                                        <div class="metric-card__description">Across all priorities</div>
                                    </div>
                                    <div class="metric-card metric-card--{('danger' if critical_count > 0 else 'success')}" aria-label="Critical defects">
                                        <div class="metric-card__number">{critical_count}</div>
                                        <div class="metric-card__label">Critical</div>
                                        <div class="metric-card__description">Highest priority issues</div>
                                    </div>
                                    <div class="metric-card metric-card--{('warning' if high_count > 0 else 'success')}" aria-label="High priority defects">
                                        <div class="metric-card__number">{high_count}</div>
                                        <div class="metric-card__label">High Priority</div>
                                        <div class="metric-card__description">Important issues</div>
                                    </div>
                                    <div class="metric-card metric-card--{('danger' if open_count > 0 else 'success')}" aria-label="Open defects">
                                        <div class="metric-card__number">{open_count}</div>
                                        <div class="metric-card__label">Open</div>
                                        <div class="metric-card__description">Need attention</div>
                                    </div>
                                    <div class="metric-card metric-card--{('danger' if security_count > 0 else 'success')}" aria-label="Security defects">
                                        <div class="metric-card__number">{security_count}</div>
                                        <div class="metric-card__label">Security</div>
                                        <div class="metric-card__description">Security-related issues</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Defect Filter Section -->
                            <div class="filter-section" role="group" aria-label="Defect Filters">
                                <h4 class="filter-section__title">Filter Defects:</h4>
                                <div class="filter-section__buttons">
                                    <button class="filter-button filter-button--defect filter-button--active"
                                            data-defect-filter="all"
                                            data-filter-group="epic-{epic.epic_id}-defect"
                                            data-filter-value="all"
                                            onclick="filterDefects('{epic.epic_id}', 'all', 'all')"
                                            aria-pressed="true">All</button>
                                    <button class="filter-button filter-button--defect"
                                            data-defect-filter="priority:critical"
                                            data-filter-group="epic-{epic.epic_id}-defect"
                                            data-filter-value="critical"
                                            onclick="filterDefects('{epic.epic_id}', 'priority', 'critical')"
                                            aria-pressed="false">Critical</button>
                                    <button class="filter-button filter-button--defect"
                                            data-defect-filter="priority:high"
                                            data-filter-group="epic-{epic.epic_id}-defect"
                                            data-filter-value="high"
                                            onclick="filterDefects('{epic.epic_id}', 'priority', 'high')"
                                            aria-pressed="false">High Priority</button>
                                    <button class="filter-button filter-button--defect"
                                            data-defect-filter="status:open"
                                            data-filter-group="epic-{epic.epic_id}-defect"
                                            data-filter-value="open"
                                            onclick="filterDefects('{epic.epic_id}', 'status', 'open')"
                                            aria-pressed="false">Open</button>
                                    <button class="filter-button filter-button--defect"
                                            data-defect-filter="status:in_progress"
                                            data-filter-group="epic-{epic.epic_id}-defect"
                                            data-filter-value="in_progress"
                                            onclick="filterDefects('{epic.epic_id}', 'status', 'in_progress')"
                                            aria-pressed="false">In Progress</button>
                                </div>
                                <div class="defect-count-display filter-count" role="status" aria-live="polite">Showing all defects</div>
                            </div>

                            <!-- Defect Traceability Table -->
                            <div class="rtm-table-container">
                                <table class="rtm-table" role="table" aria-label="Defect Traceability for {epic.epic_id}">
                                    <thead class="rtm-table__header">
                                        <tr><th scope="col">ID</th><th scope="col">Title</th><th scope="col">Priority</th><th scope="col">Status</th><th scope="col">Severity</th></tr>
                                    </thead>
                                    <tbody class="rtm-table__body">
"""

            # Add defect information - sorted by priority and unsolved first
            defects = epic_data.get("defects", [])
            priority_order = {"critical": 1, "high": 2, "medium": 3, "low": 4}
            status_order = {"open": 1, "in_progress": 2, "resolved": 3, "closed": 4}

            # Sort: unsolved issues first, then by priority
            sorted_defects = sorted(
                defects,
                key=lambda d: (
                    status_order.get(d.get("status", "open"), 5),
                    priority_order.get(d.get("priority", "medium"), 5),
                ),
            )

            for defect in sorted_defects:
                defect_id = defect.get("defect_id", "")
                title = defect.get("title", "")
                priority = defect.get("priority", "medium")
                status = defect.get("status", "open")
                severity = defect.get("severity", "medium")
                github_issue = defect.get("github_issue_number")

                # Badge icons removed for accessibility

                # Defect ID with GitHub link
                defect_id_link = (
                    f'<a href="https://github.com/QHuuT/gonogo/issues/{github_issue}" target="_blank" style="color: #3498db; text-decoration: none;" title="Open {defect_id} in GitHub"><strong>{defect_id}</strong></a>'
                    if github_issue
                    else f"<strong>{defect_id}</strong>"
                )

                html += f"""
                        <tr class="defect-row" data-defect-priority="{priority}" data-defect-status="{status}" data-defect-severity="{severity}">
                            <td>{defect_id_link}</td>
                            <td>{title}</td>
                            <td><span class="badge badge--priority badge--priority-{priority}">{priority.title()}</span></td>
                            <td><span class="badge badge--status badge--status-{status.replace('_', '-')}">{status.replace('_', ' ').title()}</span></td>
                            <td><span class="badge badge--severity badge--severity-{severity}">{severity.title()}</span></td>
                        </tr>
"""

            # If no defects, show message
            if not defects:
                html += """
                        <tr>
                            <td colspan="5" style="text-align: center; color: #7f8c8d; font-style: italic;">No defects tracked for this epic</td>
                        </tr>
"""

            # Add dynamic empty state row for defects
            html += """
                                    <!-- Empty state row for defects (hidden by default, shown when filtered count = 0) -->
                                    <tr class="empty-state-row" style="display: none;">
                                        <td colspan="5" style="text-align: center; color: #7f8c8d; font-style: italic;">No defects match the current filter</td>
                                    </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    </article>
"""

        # Close the main container and HTML after all epics
        html += """
    </div>
</body>
</html>
"""
        return html

    def generate_epic_progress_json(
        self, include_charts: bool = True
    ) -> Dict[str, Any]:
        """Generate epic progress report in JSON format."""
        epics = self._get_filtered_epics({"include_demo_data": False})

        report = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_epics": len(epics),
                "include_charts": include_charts,
            },
            "epic_progress": [],
        }

        for epic in epics:
            epic_data = self._build_epic_data(
                epic, {"include_tests": True, "include_defects": True}
            )

            # Add time-series data for charts if requested
            if include_charts:
                epic_data["chart_data"] = self._get_epic_chart_data(epic)

            report["epic_progress"].append(epic_data)

        # Overall summary
        total_points = sum(self._get_epic_story_points(epic) for epic in epics)
        completed_points = sum(self._get_epic_completed_points(epic) for epic in epics)

        report["summary"] = {
            "overall_completion": (
                (completed_points / total_points * 100) if total_points > 0 else 0
            ),
            "total_story_points": total_points,
            "completed_story_points": completed_points,
            "epics_by_status": self._get_epic_status_distribution(),
        }

        return report

    def generate_epic_progress_html(self, include_charts: bool = True) -> str:
        """Generate epic progress report in HTML format with charts."""
        json_data = self.generate_epic_progress_json(include_charts)

        html = (
            """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Epic Progress Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .chart-container { width: 100%; height: 400px; margin: 20px 0; }
        .epic-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .epic-card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; }
        .progress-circle { width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 Epic Progress Report</h1>

        <div style="background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <strong>Generated:</strong> """
            + json_data["metadata"]["generated_at"]
            + """<br>
            <strong>Overall Completion:</strong> """
            + f"{json_data['summary']['overall_completion']:.1f}%"
            + """<br>
            <strong>Total Story Points:</strong> """
            + str(json_data["summary"]["total_story_points"])
            + """
        </div>

        <div class="chart-container">
            <canvas id="overallProgressChart"></canvas>
        </div>

        <div class="epic-grid">
"""
        )

        for epic_data in json_data["epic_progress"]:
            progress = epic_data["metrics"]["completion_percentage"]
            progress_color = (
                "#27ae60"
                if progress >= 80
                else "#f39c12" if progress >= 50 else "#e74c3c"
            )

            # Extract epic and metrics data for template
            epic_id = epic_data["epic"]["epic_id"]
            epic_title = epic_data["epic"]["title"]
            completed_points = epic_data["metrics"]["completed_story_points"]
            total_points = epic_data["metrics"]["total_story_points"]
            user_stories_count = epic_data["metrics"]["user_stories_count"]
            tests_count = epic_data["metrics"]["tests_count"]
            test_pass_rate = epic_data["metrics"]["test_pass_rate"]

            html += f"""
            <div class="epic-card">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div class="progress-circle" style="background: {progress_color};">
                        {progress:.0f}%
                    </div>
                    <div style="margin-left: 15px;">
                        <h3 style="margin: 0;">{epic_id}</h3>
                        <p style="margin: 5px 0; color: #666;">{epic_title}</p>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px;">
                    <div><strong>Story Points:</strong> {completed_points}/{total_points}</div>
                    <div><strong>User Stories:</strong> {user_stories_count}</div>
                    <div><strong>Tests:</strong> {tests_count}</div>
                    <div><strong>Test Pass Rate:</strong> {test_pass_rate:.1f}%</div>
                </div>
            </div>
"""

        html += (
            """
        </div>
    </div>

    <script>
        // Overall progress chart
        const ctx = document.getElementById('overallProgressChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'Remaining'],
                datasets: [{
                    data: ["""
            + str(json_data["summary"]["completed_story_points"])
            + """, """
            + str(
                json_data["summary"]["total_story_points"]
                - json_data["summary"]["completed_story_points"]
            )
            + """],
                    backgroundColor: ['#27ae60', '#ecf0f1'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Overall Project Progress',
                        font: { size: 16 }
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    </script>
</body>
</html>
"""
        )
        return html

    def export_full_matrix(self, format: str) -> Tuple[bytes, str, str]:
        """Export full RTM matrix in specified format."""
        if format == "csv":
            return (
                self._export_csv(),
                "text/csv",
                f"rtm_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            )
        elif format == "xlsx":
            return (
                self._export_xlsx(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                f"rtm_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            )
        elif format == "pdf":
            return (
                self._export_pdf(),
                "application/pdf",
                f"rtm_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            )
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _get_filtered_epics(self, filters: Dict[str, Any]) -> List[Epic]:
        """Get epics based on applied filters."""
        query = self.db.query(Epic)

        # Filter out demo data unless explicitly requested
        if not filters.get("include_demo_data", False):
            query = query.filter(~Epic.epic_id.like("EP-DEMO-%"))

        if filters.get("epic_id"):
            query = query.filter(Epic.epic_id == filters["epic_id"])
        if filters.get("status"):
            query = query.filter(Epic.status == filters["status"])
        if filters.get("priority"):
            query = query.filter(Epic.priority == filters["priority"])

        return query.order_by(Epic.epic_id).all()

    def _build_epic_data(self, epic: Epic, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive epic data including metrics."""
        user_stories = (
            self.db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
        )
        tests = self.db.query(Test).filter(Test.epic_id == epic.id).all()
        defects = self.db.query(Defect).filter(Defect.epic_id == epic.id).all()

        # Calculate metrics - Progress based on GitHub-derived status for user stories and defects
        total_story_points = sum(us.story_points for us in user_stories)
        completed_story_points = sum(
            us.story_points
            for us in user_stories
            if us.get_github_derived_status() in ["done", "completed"]
        )

        # Count total items (user stories + defects) and completed items for progress calculation
        total_items = len(user_stories) + len(defects)
        completed_user_stories = sum(
            1
            for us in user_stories
            if us.get_github_derived_status() in ["done", "completed"]
        )
        completed_defects = sum(
            1 for d in defects if d.status in ["closed", "resolved", "done"]
        )
        completed_items = completed_user_stories + completed_defects

        test_pass_rate = 0.0
        tests_passed = 0
        tests_failed = 0
        tests_skipped = 0
        tests_not_run = 0
        if tests:
            tests_passed = sum(
                1 for test in tests if test.last_execution_status == "passed"
            )
            tests_failed = sum(
                1 for test in tests if test.last_execution_status == "failed"
            )
            tests_skipped = sum(
                1 for test in tests if test.last_execution_status == "skipped"
            )
            tests_not_run = sum(
                1
                for test in tests
                if test.last_execution_status in ["not_run", "pending", None]
            )
            # Only calculate pass rate for tests that have been executed
            executed_tests = tests_passed + tests_failed + tests_skipped
            test_pass_rate = (
                (tests_passed / executed_tests * 100) if executed_tests > 0 else 0
            )

        # Build base data
        epic_data = {
            "epic": epic.to_dict(),
            "user_stories": [us.to_dict() for us in user_stories],
            "tests": (
                [test.to_dict() for test in tests]
                if filters.get("include_tests", True)
                else []
            ),
            "defects": (
                [defect.to_dict() for defect in defects]
                if filters.get("include_defects", True)
                else []
            ),
            "metrics": {
                "total_story_points": total_story_points,
                "completed_story_points": completed_story_points,
                "completion_percentage": (
                    (completed_items / total_items * 100) if total_items > 0 else 0
                ),
                "total_items": total_items,
                "completed_items": completed_items,
                "completed_user_stories": completed_user_stories,
                "completed_defects": completed_defects,
                "user_stories_count": len(user_stories),
                "tests_count": len(tests),
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "tests_skipped": tests_skipped,
                "tests_not_run": tests_not_run,
                "test_pass_rate": test_pass_rate,
                "defects_count": len(defects),
                "critical_defects": sum(1 for d in defects if d.severity == "critical"),
                "open_defects": sum(
                    1 for d in defects if d.status in ["open", "in_progress"]
                ),
            },
        }

        # Apply server-side filtering if filtering parameters are present
        filter_params = {
            "us_status_filter": filters.get("us_status_filter"),
            "test_type_filter": filters.get("test_type_filter"),
            "defect_priority_filter": filters.get("defect_priority_filter"),
            "defect_status_filter": filters.get("defect_status_filter"),
        }

        # Only apply filtering if any filter parameters are set
        if any(v and v != "all" for v in filter_params.values()):
            epic_data = self._apply_server_side_filters(epic_data, filter_params)

        return epic_data

    def _get_test_counts(self, tests: List[Test]) -> Dict[str, int]:
        """Get test counts by type."""
        return {
            "unit": sum(1 for t in tests if t.test_type == "unit"),
            "integration": sum(1 for t in tests if t.test_type == "integration"),
            "bdd": sum(1 for t in tests if t.test_type == "bdd"),
        }

    def _generate_test_type_breakdown_html(self, tests) -> str:
        """Generate HTML for test type breakdown with visual bars."""
        if not tests:
            return '<div class="no-tests">No tests available</div>'

        # Count tests by type - handle both Test objects and dictionaries
        type_counts = {}
        for test in tests:
            if isinstance(test, dict):
                test_type = test.get("test_type", "unknown").lower()
            else:
                test_type = test.test_type.lower()
            type_counts[test_type] = type_counts.get(test_type, 0) + 1

        total_tests = len(tests)
        html = ""

        # Define colors for each test type
        type_colors = {
            "unit": "#3498db",
            "integration": "#e74c3c",
            "e2e": "#f39c12",
            "security": "#9b59b6",
            "bdd": "#1abc9c",
        }

        for test_type, count in sorted(type_counts.items()):
            percentage = (count / total_tests) * 100
            color = type_colors.get(test_type, "#95a5a6")

            html += f"""
                <div class="test-type-stat">
                    <div class="test-type-header">
                        <span class="test-type-label">{test_type.upper()}</span>
                        <span class="test-type-count">{count} ({percentage:.1f}%)</span>
                    </div>
                    <div class="test-type-bar">
                        <div class="test-type-progress" style="width: {percentage}%; background-color: {color};"></div>
                    </div>
                </div>
            """

        return html

    def _get_us_filter_display_text(
        self, epic_data: Dict[str, Any], us_status_filter: str
    ) -> str:
        """Generate display text for user story filter."""
        total_us = len(epic_data.get("user_stories", []))
        if us_status_filter == "all":
            return f"Showing all user stories ({total_us} total)"
        else:
            filtered_us = [
                us
                for us in epic_data.get("user_stories", [])
                if us.get("implementation_status") == us_status_filter
            ]
            status_display = us_status_filter.replace("_", " ").title()
            return f"Showing {len(filtered_us)} {status_display} user stories ({total_us} total)"

    def _apply_server_side_filters(
        self, epic_data: Dict[str, Any], filters: Dict[str, str]
    ) -> Dict[str, Any]:
        """Apply server-side filtering to epic data."""
        filtered_data = epic_data.copy()

        # Filter user stories
        us_status_filter = filters.get("us_status_filter", "all")
        if us_status_filter != "all":
            filtered_data["user_stories"] = [
                us
                for us in epic_data.get("user_stories", [])
                if us.get("implementation_status") == us_status_filter
            ]

        # Filter tests
        test_type_filter = filters.get("test_type_filter", "all")
        if test_type_filter != "all":
            filtered_data["tests"] = [
                test
                for test in epic_data.get("tests", [])
                if test.get("test_type", "").lower() == test_type_filter.lower()
            ]

        # Filter defects
        defect_priority_filter = filters.get("defect_priority_filter", "all")
        defect_status_filter = filters.get("defect_status_filter", "all")

        filtered_defects = epic_data.get("defects", [])

        if defect_priority_filter and defect_priority_filter != "all":
            filtered_defects = [
                defect
                for defect in filtered_defects
                if defect.get("priority", "").lower() == defect_priority_filter.lower()
            ]

        if defect_status_filter and defect_status_filter != "all":
            filtered_defects = [
                defect
                for defect in filtered_defects
                if defect.get("status", "").lower() == defect_status_filter.lower()
            ]

        filtered_data["defects"] = filtered_defects

        return filtered_data

    def _calculate_pass_rate(self, tests: List[Test]) -> float:
        """Calculate test pass rate."""
        if not tests:
            return 0.0
        passed = sum(1 for t in tests if t.last_execution_status == "passed")
        return (passed / len(tests)) * 100

    def _get_defect_summary(self, defects: List[Defect]) -> Dict[str, int]:
        """Get defect summary by severity and status."""
        return {
            "critical": sum(1 for d in defects if d.severity == "critical"),
            "high": sum(1 for d in defects if d.severity == "high"),
            "open": sum(1 for d in defects if d.status in ["open", "in_progress"]),
            "security": sum(1 for d in defects if d.is_security_issue),
        }

    def _get_filter_summary(self, filters: Dict[str, Any]) -> str:
        """Generate a concise filter summary for the header."""
        active_filters = {
            k: v
            for k, v in filters.items()
            if v is not None
            and v != ""
            and k not in ["include_tests", "include_defects"]
        }
        if not active_filters:
            return "None"

        # Create a more user-friendly summary
        summary_parts = []
        for k, v in active_filters.items():
            if k == "us_status_filter":
                summary_parts.append(f"US: {v}")
            elif k == "test_type_filter":
                summary_parts.append(f"Tests: {v}")
            elif k == "defect_priority_filter":
                summary_parts.append(f"Defects: {v}")
            else:
                summary_parts.append(f"{k}: {v}")

        return ", ".join(summary_parts)

    def _get_filter_info_html(self, filters: Dict[str, Any]) -> str:
        """Generate HTML filter information."""
        active_filters = {
            k: v
            for k, v in filters.items()
            if v is not None
            and v != ""
            and k not in ["include_tests", "include_defects"]
        }
        if not active_filters:
            return ""  # Remove "No filters applied" text

        filter_text = ", ".join([f"{k}: {v}" for k, v in active_filters.items()])
        return f"<span class='filter-info'>Filters: {filter_text}</span>"

    def _get_github_issue_link(self, github_issue_number: int) -> str:
        """Generate GitHub issue link."""
        if not github_issue_number:
            return ""
        # Using the gonogo repository
        return f"https://github.com/QHuuT/gonogo/issues/{github_issue_number}"

    def _render_user_story_id_link(
        self, user_story_id: str, github_issue_number: int
    ) -> str:
        """Render user story ID as clickable GitHub link if available."""
        if github_issue_number and github_issue_number > 0:
            github_url = self._get_github_issue_link(github_issue_number)
            return f'<a href="{github_url}" target="_blank" style="color: #3498db; text-decoration: none;" title="Open {user_story_id} in GitHub"><strong>{user_story_id}</strong></a>'
        return f"<strong>{user_story_id}</strong>"

    def _render_epic_title_link(
        self, epic_id: str, title: str, github_issue_number: int
    ) -> str:
        """Render epic title as GitHub link if available."""
        # Clean title by stripping whitespace and normalizing spaces
        clean_title = " ".join(title.strip().split()) if title else "No title"

        if github_issue_number and github_issue_number > 0:
            github_url = self._get_github_issue_link(github_issue_number)
            return f'<a href="{github_url}" target="_blank" class="epic-title-link" title="Click to open {epic_id} in GitHub">{epic_id}: {clean_title}</a>'
        return f"{epic_id}: {clean_title}"

    def _extract_epic_description(self, github_body: str) -> str:
        """Extract just the Epic Description field from GitHub issue template."""
        if not github_body:
            return "No description provided"

        # Look for the Epic Description section
        import re

        # Pattern to match Epic Description section from GitHub issue template
        epic_desc_pattern = r"### Epic Description\s*\n(.*?)(?=\n### |$)"
        match = re.search(epic_desc_pattern, github_body, re.DOTALL)

        if match:
            description = match.group(1).strip()
            # Clean up markdown formatting
            description = self._clean_markdown(description)
            return description

        # Fallback: look for older format with ## Epic Description
        epic_desc_pattern = r"## Epic Description\s*\n(.*?)(?=\n## |$)"
        match = re.search(epic_desc_pattern, github_body, re.DOTALL)

        if match:
            description = match.group(1).strip()
            description = self._clean_markdown(description)
            return description

        # If no Epic Description section found, return first paragraph or truncated text
        lines = github_body.split("\n")
        clean_lines = [
            line.strip() for line in lines if line.strip() and not line.startswith("#")
        ]
        if clean_lines:
            description = "\n".join(
                clean_lines[:5]
            )  # First 5 non-empty, non-header lines
            description = self._clean_markdown(description)
            return description

        return "No description provided"

    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting from text."""
        if not text:
            return ""

        import re

        # Remove markdown headers
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

        # Remove bold/italic
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # **bold**
        text = re.sub(r"\*(.*?)\*", r"\1", text)  # *italic*

        # Remove links but keep text
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # [text](url)

        # Remove inline code
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Remove bullet points
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)

        # Clean up extra whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)  # Multiple blank lines to double
        text = text.strip()

        return text

    def _get_epic_chart_data(self, epic: Epic) -> Dict[str, Any]:
        """Get chart data for epic progress over time."""
        # This would typically query historical data
        # For now, return current state
        return {
            "completion_trend": [0, 25, 50, 75, 80],  # Mock data
            "test_execution_trend": [0, 20, 60, 85, 90],  # Mock data
            "defect_trend": [0, 2, 5, 3, 2],  # Mock data
        }

    def _get_epic_story_points(self, epic: Epic) -> int:
        """Get total story points for an epic."""
        return sum(
            us.story_points
            for us in self.db.query(UserStory)
            .filter(UserStory.epic_id == epic.id)
            .all()
        )

    def _get_epic_completed_points(self, epic: Epic) -> int:
        """Get completed story points for an epic."""
        user_stories = (
            self.db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
        )
        return sum(
            us.story_points
            for us in user_stories
            if us.implementation_status in ["done", "completed"]
        )

    def _get_epic_status_distribution(self) -> Dict[str, int]:
        """Get distribution of epics by status."""
        status_query = (
            self.db.query(Epic.status, func.count(Epic.id).label("count"))
            .group_by(Epic.status)
            .all()
        )

        return {status: count for status, count in status_query}

    def _export_csv(self) -> bytes:
        """Export RTM data as CSV."""
        # Simplified CSV export - would implement full CSV generation
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Headers
        writer.writerow(
            [
                "Epic ID",
                "Epic Title",
                "Status",
                "User Stories",
                "Story Points",
                "Tests",
                "Defects",
            ]
        )

        # Data
        epics = self._get_filtered_epics({"include_demo_data": False})
        for epic in epics:
            user_stories = (
                self.db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
            )
            tests = self.db.query(Test).filter(Test.epic_id == epic.id).all()
            defects = self.db.query(Defect).filter(Defect.epic_id == epic.id).all()

            writer.writerow(
                [
                    epic.epic_id,
                    epic.title,
                    epic.status,
                    len(user_stories),
                    sum(us.story_points for us in user_stories),
                    len(tests),
                    len(defects),
                ]
            )

        return output.getvalue().encode("utf-8")

    def _export_xlsx(self) -> bytes:
        """Export RTM data as Excel file."""
        # Would implement Excel export using openpyxl
        return b"Excel export not yet implemented"

    def _export_pdf(self) -> bytes:
        """Export RTM data as PDF."""
        # Would implement PDF export using reportlab
        return b"PDF export not yet implemented"
