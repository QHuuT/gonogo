"""
RTM Report Generator Service

Generates dynamic RTM reports in multiple formats from database data.
Supports real-time reporting, filtering, and export capabilities.

Related Issue: US-00059 - Dynamic RTM generation and reporting
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..models.traceability import Epic, UserStory, Test, Defect


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
                "filters_applied": {k: v for k, v in filters.items() if v is not None}
            },
            "epics": []
        }

        for epic in epics:
            epic_data = self._build_epic_data(epic, filters)
            matrix_data["epics"].append(epic_data)

        return matrix_data

    def generate_markdown_matrix(self, filters: Dict[str, Any]) -> str:
        """Generate RTM matrix in Markdown format."""
        epics = self._get_filtered_epics(filters)

        markdown = "# Dynamic Requirements Traceability Matrix\n\n"
        markdown += f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        markdown += f"**Total Epics**: {len(epics)}\n\n"

        # Epic to User Story mapping table
        markdown += "## Epic to User Story Mapping\n\n"
        markdown += "| Epic ID | Epic Name | User Stories | Story Points | Status | Progress |\n"
        markdown += "|---------|-----------|--------------|--------------|--------|----------|\n"

        for epic in epics:
            user_stories = self.db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
            us_list = ", ".join([f"[{us.user_story_id}](#{us.user_story_id})" for us in user_stories])
            total_points = sum(us.story_points for us in user_stories)
            completed_points = sum(us.story_points for us in user_stories
                                 if us.implementation_status in ["done", "completed"])
            progress = f"{(completed_points/total_points*100):.1f}%" if total_points > 0 else "0%"

            status_emoji = {
                "planned": "📝",
                "in_progress": "⏳",
                "completed": "✅",
                "blocked": "🚫"
            }.get(epic.status, "❓")

            markdown += f"| **{epic.epic_id}** | {epic.title} | {us_list} | {total_points} | {status_emoji} {epic.status} | {progress} |\n"

        # Test coverage section if requested
        if filters.get("include_tests", True):
            markdown += "\n## Test Coverage Summary\n\n"
            markdown += "| Epic ID | Total Tests | Unit | Integration | BDD | Pass Rate |\n"
            markdown += "|---------|-------------|------|-------------|-----|-----------|\n"

            for epic in epics:
                tests = self.db.query(Test).filter(Test.epic_id == epic.id).all()
                test_counts = self._get_test_counts(tests)
                pass_rate = self._calculate_pass_rate(tests)

                markdown += f"| {epic.epic_id} | {len(tests)} | {test_counts['unit']} | {test_counts['integration']} | {test_counts['bdd']} | {pass_rate:.1f}% |\n"

        # Defect tracking section if requested
        if filters.get("include_defects", True):
            markdown += "\n## Defect Tracking\n\n"
            markdown += "| Epic ID | Total Defects | Critical | High | Open | Security |\n"
            markdown += "|---------|---------------|----------|------|------|----------|\n"

            for epic in epics:
                defects = self.db.query(Defect).filter(Defect.epic_id == epic.id).all()
                defect_summary = self._get_defect_summary(defects)

                markdown += f"| {epic.epic_id} | {len(defects)} | {defect_summary['critical']} | {defect_summary['high']} | {defect_summary['open']} | {defect_summary['security']} |\n"

        return markdown

    def generate_html_matrix(self, filters: Dict[str, Any]) -> str:
        """Generate RTM matrix in HTML format with Python-based filtering."""
        # Extract filter parameters
        epic_filter = filters.get('epic_filter', 'all')
        us_status_filter = filters.get('us_status_filter', 'all')
        test_type_filter = filters.get('test_type_filter', 'e2e')  # Default to E2E
        defect_priority_filter = filters.get('defect_priority_filter', 'all')
        defect_status_filter = filters.get('defect_status_filter', 'all')

        epics = self._get_filtered_epics(filters)

        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dynamic RTM Matrix</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .metadata { background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .epic-card { border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; overflow: hidden; }
        .epic-header { background: #3498db; color: white; padding: 15px; }
        .epic-content { padding: 15px; }
        .progress-bar { background: #ecf0f1; height: 20px; border-radius: 10px; overflow: hidden; margin-top: 10px; }
        .progress-fill { background: linear-gradient(90deg, #27ae60, #2ecc71); height: 100%; border-radius: 10px; transition: width 0.3s ease; }
        .status-badge { padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .status-planned { background: #f39c12; color: white; }
        .status-in-progress { background: #e67e22; color: white; }
        .status-completed { background: #27ae60; color: white; }
        .status-blocked { background: #e74c3c; color: white; }
        .test-summary, .defect-summary { display: flex; gap: 15px; margin-top: 10px; }
        .metric { text-align: center; padding: 10px; background: #f8f9fa; border-radius: 5px; flex: 1; }
        .metric-value { font-size: 18px; font-weight: bold; color: #2c3e50; }
        .metric-label { font-size: 12px; color: #7f8c8d; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: 600; }
        .filter-info { font-style: italic; color: #7f8c8d; }
        .test-type-badge { background: #34495e; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: bold; }
        .test-filter-section { margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        .test-filter-button { padding: 6px 12px; margin: 0 5px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; font-size: 12px; }
        .test-filter-button.active { background: #3498db; color: white; border-color: #3498db; }
        .test-filter-button:hover { background: #e9ecef; }
        .test-filter-button.active:hover { background: #2980b9; }
        .test-row { transition: opacity 0.3s ease; }
        .test-row.hidden { display: none; }
        .us-filter-section { margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        .us-filter-button { padding: 6px 12px; margin: 0 5px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; font-size: 12px; }
        .us-filter-button.active { background: #27ae60; color: white; border-color: #27ae60; }
        .us-filter-button:hover { background: #e9ecef; }
        .us-filter-button.active:hover { background: #229954; }
        .us-row { transition: opacity 0.3s ease; }
        .us-row.hidden { display: none; }
        .test-metrics-dashboard { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-icon { font-size: 24px; margin-bottom: 8px; }
        .metric-number { font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 4px; }
        .metric-title { font-size: 12px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 0.5px; }
        .test-type-breakdown h5 { margin: 0 0 15px 0; color: #2c3e50; }
        .test-type-stat { margin-bottom: 12px; }
        .test-type-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; font-size: 12px; }
        .test-type-label { font-weight: bold; text-transform: uppercase; }
        .test-type-count { color: #7f8c8d; }
        .test-type-bar { height: 8px; background: #ecf0f1; border-radius: 4px; overflow: hidden; }
        .test-type-progress { height: 100%; transition: width 0.3s ease; }
        .no-tests { text-align: center; color: #7f8c8d; font-style: italic; padding: 20px; }
        .defect-filter-section { margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        .defect-filter-button { padding: 6px 12px; margin: 0 5px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; font-size: 12px; }
        .defect-filter-button.active { background: #e74c3c; color: white; border-color: #e74c3c; }
        .defect-filter-button:hover { background: #e9ecef; }
        .defect-filter-button.active:hover { background: #c0392b; }
        .defect-row { transition: opacity 0.3s ease; }
        .defect-row.hidden { display: none; }
        .priority-badge { padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; color: white; }
        .priority-critical { background: #e74c3c; }
        .priority-high { background: #f39c12; }
        .priority-medium { background: #f1c40f; color: #2c3e50; }
        .priority-low { background: #27ae60; }
        .defect-status-open { background: #e74c3c; color: white; }
        .defect-status-in-progress { background: #f39c12; color: white; }
        .defect-status-resolved { background: #27ae60; color: white; }
        .defect-status-closed { background: #95a5a6; color: white; }
        .severity-badge { padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; border: 2px solid; }
        .severity-critical { color: #e74c3c; border-color: #e74c3c; background: #fdedec; }
        .severity-high { color: #f39c12; border-color: #f39c12; background: #fef9e7; }
        .severity-medium { color: #f1c40f; border-color: #f1c40f; background: #fcf3cf; }
        .severity-low { color: #27ae60; border-color: #27ae60; background: #eafaf1; }
        .epic-title-link { color: #f8f9fa !important; text-decoration: none; transition: all 0.2s ease; }
        .epic-title-link:hover { color: #ffd700 !important; text-decoration: underline; text-shadow: 0 0 5px rgba(255, 215, 0, 0.5); }
        .epic-header { cursor: pointer; }
    </style>
    <script>
        function toggleEpicDetails(epicId) {
            const content = document.getElementById('epic-' + epicId);
            content.style.display = content.style.display === 'none' ? 'block' : 'none';
        }

        function filterByStatus(status) {
            const cards = document.querySelectorAll('.epic-card');
            cards.forEach(card => {
                const cardStatus = card.dataset.status;
                card.style.display = status === 'all' || cardStatus === status ? 'block' : 'none';
            });
        }

        function filterTestsByType(epicId, testType) {
            const testTable = document.querySelector(`#epic-${epicId} .test-filter-section + table tbody`);
            if (!testTable) return;

            const testRows = testTable.querySelectorAll('tr.test-row');
            const filterButtons = document.querySelectorAll(`#epic-${epicId} .test-filter-button`);

            // Update button states
            filterButtons.forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.testType === testType) {
                    btn.classList.add('active');
                }
            });

            // Filter test rows
            testRows.forEach(row => {
                const testTypeBadge = row.querySelector('.test-type-badge');
                if (!testTypeBadge) return;

                const rowTestType = testTypeBadge.textContent.toLowerCase();

                if (testType === 'all' || rowTestType === testType.toLowerCase()) {
                    row.classList.remove('hidden');
                } else {
                    row.classList.add('hidden');
                }
            });

            // Update test count display
            const allTestRows = testTable.querySelectorAll('tr.test-row'); // Only actual test rows
            const visibleTestRows = testTable.querySelectorAll('tr.test-row:not(.hidden)');
            const totalTests = allTestRows.length;
            const visibleTests = visibleTestRows.length;

            const countDisplay = document.querySelector(`#epic-${epicId} .test-count-display`);
            if (countDisplay) {
                if (totalTests === 0) {
                    countDisplay.textContent = 'No tests available for this epic';
                } else if (testType === 'all') {
                    countDisplay.textContent = `Showing all ${totalTests} tests`;
                } else {
                    countDisplay.textContent = `Showing ${visibleTests} ${testType.toUpperCase()} tests (${totalTests} total)`;
                }
            }
        }
        function filterUserStoriesByStatus(epicId, status) {
            const usTable = document.querySelector(`#epic-${epicId} table:first-of-type tbody`);
            if (!usTable) return;
            const usRows = usTable.querySelectorAll('.us-row');
            const filterButtons = document.querySelectorAll(`#epic-${epicId} .us-filter-button`);
            // Update button states
            filterButtons.forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.usStatus === status) {
                    btn.classList.add('active');
                }
            });
            // Filter user story rows
            usRows.forEach(row => {
                const rowStatus = row.dataset.usStatus;
                if (status === 'all' || rowStatus === status) {
                    row.classList.remove('hidden');
                } else {
                    row.classList.add('hidden');
                }
            });
            // Update user story count display
            const visibleUsRows = usTable.querySelectorAll('.us-row:not(.hidden)');
            const totalUs = usRows.length;
            const visibleUs = visibleUsRows.length;
            const countDisplay = document.querySelector(`#epic-${epicId} .us-count-display`);
            if (countDisplay) {
                if (status === 'all') {
                    countDisplay.textContent = `Showing all user stories (${totalUs} total)`;
                } else {
                    const statusDisplay = status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
                    countDisplay.textContent = `Showing ${visibleUs} ${statusDisplay} user stories (${totalUs} total)`;
                }
            }
        }
        function filterDefects(epicId, filterType, filterValue) {
            const defectTable = document.querySelector(`#epic-${epicId} .defect-filter-section + table tbody`);
            if (!defectTable) return;
            const defectRows = defectTable.querySelectorAll('.defect-row');
            const filterButtons = document.querySelectorAll(`#epic-${epicId} .defect-filter-button`);

            // Update button states
            filterButtons.forEach(btn => {
                btn.classList.remove('active');
                if ((filterType === 'all' && btn.dataset.defectFilter === 'all') ||
                    btn.dataset.defectFilter === `${filterType}:${filterValue}`) {
                    btn.classList.add('active');
                }
            });

            // Filter defect rows
            defectRows.forEach(row => {
                let shouldShow = false;
                if (filterType === 'all') {
                    shouldShow = true;
                } else if (filterType === 'priority') {
                    shouldShow = row.dataset.defectPriority === filterValue;
                } else if (filterType === 'status') {
                    shouldShow = row.dataset.defectStatus === filterValue;
                }

                if (shouldShow) {
                    row.classList.remove('hidden');
                } else {
                    row.classList.add('hidden');
                }
            });

            // Update defect count display
            const visibleDefectRows = defectTable.querySelectorAll('.defect-row:not(.hidden)');
            const totalDefects = defectRows.length;
            const visibleDefects = visibleDefectRows.length;
            const countDisplay = document.querySelector(`#epic-${epicId} .defect-count-display`);
            if (countDisplay) {
                if (filterType === 'all') {
                    countDisplay.textContent = `Showing all defects (${totalDefects} total)`;
                } else {
                    const filterDisplay = filterValue.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
                    countDisplay.textContent = `Showing ${visibleDefects} ${filterDisplay} defects (${totalDefects} total)`;
                }
            }
        }

        function initializeTestFiltering() {
            // Set E2E as default filter for all epics
            const epics = document.querySelectorAll('.epic-card');
            epics.forEach(epic => {
                const epicId = epic.dataset.status ? epic.querySelector('.epic-header h3 a')?.textContent?.split(':')[0] : null;
                if (epicId) {
                    // Default to E2E tests only
                    filterTestsByType(epicId, 'e2e');
                }
            });
        }

        // Add accessibility improvements
        document.addEventListener('DOMContentLoaded', function() {
            // Add keyboard accessibility for epic headers
            const epicHeaders = document.querySelectorAll('.epic-header');
            epicHeaders.forEach(header => {
                header.setAttribute('tabindex', '0');
                header.setAttribute('role', 'button');
                header.setAttribute('aria-expanded', 'false');

                header.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        const epicId = this.querySelector('.epic-title-link')?.textContent?.split(':')[0] ||
                                     this.textContent.trim().split(':')[0];
                        toggleEpicDetails(epicId);
                    }
                });
            });

            // Initialize test filtering with E2E default
            initializeTestFiltering();
        });
    </script>
</head>
<body>
    <div class="container">
        <h1>🎯 Dynamic Requirements Traceability Matrix</h1>

        <div class="metadata">
            <strong>Generated:</strong> """ + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC') + """<br>
            <strong>Total Epics:</strong> """ + str(len(epics)) + """<br>
            """ + self._get_filter_info_html(filters) + """
        </div>

        <div style="margin-bottom: 20px;">
            <strong>Filter by Status:</strong>
            <button onclick="filterByStatus('all')" style="margin-left: 10px; padding: 5px 10px;">All</button>
            <button onclick="filterByStatus('planned')" style="margin-left: 5px; padding: 5px 10px;">Planned</button>
            <button onclick="filterByStatus('in_progress')" style="margin-left: 5px; padding: 5px 10px;">In Progress</button>
            <button onclick="filterByStatus('completed')" style="margin-left: 5px; padding: 5px 10px;">Completed</button>
        </div>

        <h2>📊 Epic Progress Overview</h2>
"""

        for epic in epics:
            epic_data = self._build_epic_data(epic, filters)
            progress = epic_data["metrics"]["completion_percentage"]

            epic_title_link = self._render_epic_title_link(epic.epic_id, epic.title, epic.github_issue_number)
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
        <div class="epic-card" data-status="{epic.status}">
            <div class="epic-header" onclick="toggleEpicDetails('{epic.epic_id}')">
                <h3 style="margin: 0; display: inline-block;">{epic_title_link} <span class="status-badge status-{epic.status.replace('_', '-')}" style="margin-left: 10px;">{epic.status.replace('_', ' ').title()}</span></h3>
            </div>
            <div class="epic-content" id="epic-{epic.epic_id}">
                <p><strong>Description:</strong> {clean_description.replace(chr(10), '<br>')}</p>

                <div class="progress-bar">
                    <div class="progress-fill" style="width: {progress}%"></div>
                </div>
                <p style="text-align: center; margin-top: 5px;"><strong>{progress:.1f}% Complete</strong></p>

                <div class="test-summary">
                    <div class="metric">
                        <div class="metric-value">{user_stories_count}</div>
                        <div class="metric-label">User Stories</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{completed_points}/{total_points}</div>
                        <div class="metric-label">Story Points</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{tests_count}</div>
                        <div class="metric-label">Tests</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{test_pass_rate:.1f}%</div>
                        <div class="metric-label">Pass Rate ({tests_passed}/{tests_count})</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{defects_count}</div>
                        <div class="metric-label">Defects</div>
                    </div>
                </div>

                <h4>User Stories</h4>
                <div class="us-filter-section">
                    <strong>Filter User Stories:</strong>
                    <button class="us-filter-button active" data-us-status="all" onclick="filterUserStoriesByStatus('""" + epic.epic_id + """', 'all')">All</button>
                    <button class="us-filter-button" data-us-status="planned" onclick="filterUserStoriesByStatus('""" + epic.epic_id + """', 'planned')">Planned</button>
                    <button class="us-filter-button" data-us-status="in_progress" onclick="filterUserStoriesByStatus('""" + epic.epic_id + """', 'in_progress')">In Progress</button>
                    <button class="us-filter-button" data-us-status="completed" onclick="filterUserStoriesByStatus('""" + epic.epic_id + """', 'completed')">Completed</button>
                    <button class="us-filter-button" data-us-status="blocked" onclick="filterUserStoriesByStatus('""" + epic.epic_id + """', 'blocked')">Blocked</button>
                    <span class="us-count-display" style="margin-left: 15px; font-style: italic; color: #7f8c8d;">Showing all user stories</span>
                </div>
                <table>
                    <thead>
                        <tr><th>ID</th><th>Title</th><th>Story Points</th><th>Status</th></tr>
                    </thead>
                    <tbody>
"""
            for us in epic_data["user_stories"]:
                user_story_link = self._render_user_story_id_link(us["user_story_id"], us.get("github_issue_number"))
                status_normalized = us["implementation_status"].replace('_', '-')
                html += f"""
                        <tr class="us-row" data-us-status="{us['implementation_status']}">
                            <td>{user_story_link}</td>
                            <td>{us["title"]}</td>
                            <td>{us["story_points"]}</td>
                            <td><span class="status-badge status-{status_normalized}">{us["implementation_status"].replace('_', ' ').title()}</span></td>
                        </tr>
"""

            html += f"""
                    </tbody>
                </table>

                <h4>Test Metrics</h4>
                <div class="test-metrics-dashboard">
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-icon">🧪</div>
                            <div class="metric-content">
                                <div class="metric-number">{tests_count}</div>
                                <div class="metric-title">Total Tests</div>
                            </div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-icon">✅</div>
                            <div class="metric-content">
                                <div class="metric-number">{test_pass_rate:.1f}%</div>
                                <div class="metric-title">Pass Rate</div>
                            </div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-icon">⚡</div>
                            <div class="metric-content">
                                <div class="metric-number">{tests_passed}</div>
                                <div class="metric-title">Passed</div>
                            </div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-icon">❌</div>
                            <div class="metric-content">
                                <div class="metric-number">{tests_failed}</div>
                                <div class="metric-title">Failed</div>
                            </div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-icon">⏭️</div>
                            <div class="metric-content">
                                <div class="metric-number">{tests_not_run}</div>
                                <div class="metric-title">Not Run</div>
                            </div>
                        </div>
                    </div>
                    <div class="test-type-breakdown">
                        <h5>Test Distribution by Type</h5>
                        <div class="test-type-stats">"""

            # Add test type breakdown HTML
            html += self._generate_test_type_breakdown_html(epic_data.get("tests", []))

            html += """
                        </div>
                    </div>
                </div>

                <h4>Test Traceability</h4>
                <div class="test-filter-section">
                    <strong>Filter Tests:</strong>
                    <button class="test-filter-button active" data-test-type="e2e" onclick="filterTestsByType('""" + epic.epic_id + """', 'e2e')">E2E Only</button>
                    <button class="test-filter-button" data-test-type="unit" onclick="filterTestsByType('""" + epic.epic_id + """', 'unit')">Unit</button>
                    <button class="test-filter-button" data-test-type="integration" onclick="filterTestsByType('""" + epic.epic_id + """', 'integration')">Integration</button>
                    <button class="test-filter-button" data-test-type="security" onclick="filterTestsByType('""" + epic.epic_id + """', 'security')">Security</button>
                    <button class="test-filter-button" data-test-type="all" onclick="filterTestsByType('""" + epic.epic_id + """', 'all')">All Tests</button>
                    <span class="test-count-display" style="margin-left: 15px; font-style: italic; color: #7f8c8d;">Showing E2E tests only</span>
                </div>
                <table>
                    <thead>
                        <tr><th>Test Type</th><th>Test File</th><th>Function/Scenario</th><th>Last Execution</th><th>Status</th></tr>
                    </thead>
                    <tbody>
"""

            # Add test information
            for test in epic_data.get("tests", []):
                # Format last execution time
                last_execution = test.get("last_execution_time", "")
                if last_execution:
                    try:
                        if isinstance(last_execution, str):
                            exec_time = datetime.fromisoformat(last_execution.replace('Z', '+00:00'))
                        else:
                            exec_time = last_execution
                        formatted_time = exec_time.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_time = str(last_execution)
                else:
                    formatted_time = "Never"

                # Get test function or BDD scenario name
                test_name = test.get("test_function_name") or test.get("bdd_scenario_name", "")

                # Status styling
                status = test.get("last_execution_status", "unknown")
                status_class = "passed" if status == "passed" else "failed" if status == "failed" else "skipped"
                status_icon = "✅" if status == "passed" else "❌" if status == "failed" else "⏭️"

                test_type_lower = test.get("test_type", "").lower()
                html += f"""
                        <tr class="test-row" data-test-type="{test_type_lower}">
                            <td><span class="test-type-badge">{test.get("test_type", "").upper()}</span></td>
                            <td><code style="font-size: 12px;">{test.get("test_file_path", "")}</code></td>
                            <td>{test_name}</td>
                            <td>{formatted_time}</td>
                            <td><span class="status-badge status-{status_class}">{status_icon} {status.title()}</span></td>
                        </tr>
"""

            # If no tests, show message
            if not epic_data.get("tests", []):
                html += """
                        <tr>
                            <td colspan="5" style="text-align: center; color: #7f8c8d; font-style: italic;">No tests available for this epic</td>
                        </tr>
"""

            html += """
                    </tbody>
                </table>

                <h4>Defect Management</h4>
                <div class="defect-filter-section">
                    <strong>Filter Defects:</strong>
                    <button class="defect-filter-button active" data-defect-filter="all" onclick="filterDefects('""" + epic.epic_id + """', 'all', 'all')">All</button>
                    <button class="defect-filter-button" data-defect-filter="priority:critical" onclick="filterDefects('""" + epic.epic_id + """', 'priority', 'critical')">Critical</button>
                    <button class="defect-filter-button" data-defect-filter="priority:high" onclick="filterDefects('""" + epic.epic_id + """', 'priority', 'high')">High Priority</button>
                    <button class="defect-filter-button" data-defect-filter="status:open" onclick="filterDefects('""" + epic.epic_id + """', 'status', 'open')">Open</button>
                    <button class="defect-filter-button" data-defect-filter="status:in_progress" onclick="filterDefects('""" + epic.epic_id + """', 'status', 'in_progress')">In Progress</button>
                    <span class="defect-count-display" style="margin-left: 15px; font-style: italic; color: #7f8c8d;">Showing all defects</span>
                </div>
                <table>
                    <thead>
                        <tr><th>ID</th><th>Title</th><th>Priority</th><th>Status</th><th>Severity</th></tr>
                    </thead>
                    <tbody>
"""

            # Add defect information - sorted by priority and unsolved first
            defects = epic_data.get("defects", [])
            priority_order = {"critical": 1, "high": 2, "medium": 3, "low": 4}
            status_order = {"open": 1, "in_progress": 2, "resolved": 3, "closed": 4}

            # Sort: unsolved issues first, then by priority
            sorted_defects = sorted(defects, key=lambda d: (
                status_order.get(d.get("status", "open"), 5),
                priority_order.get(d.get("priority", "medium"), 5)
            ))

            for defect in sorted_defects:
                defect_id = defect.get("defect_id", "")
                title = defect.get("title", "")
                priority = defect.get("priority", "medium")
                status = defect.get("status", "open")
                severity = defect.get("severity", "medium")
                github_issue = defect.get("github_issue_number")

                # Priority badge styling
                priority_class = f"priority-{priority}"
                priority_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")

                # Status badge styling
                status_class = f"defect-status-{status.replace('_', '-')}"
                status_icon = {"open": "🆘", "in_progress": "⏳", "resolved": "✅", "closed": "✅"}.get(status, "❓")

                # Severity badge styling
                severity_class = f"severity-{severity}"

                # Defect ID with GitHub link
                defect_id_link = f'<a href="https://github.com/QHuuT/gonogo/issues/{github_issue}" target="_blank" title="Open {defect_id} in GitHub"><strong>{defect_id}</strong></a>' if github_issue else f"<strong>{defect_id}</strong>"

                html += f"""
                        <tr class="defect-row" data-defect-priority="{priority}" data-defect-status="{status}" data-defect-severity="{severity}">
                            <td>{defect_id_link}</td>
                            <td>{title}</td>
                            <td><span class="priority-badge {priority_class}">{priority_icon} {priority.title()}</span></td>
                            <td><span class="status-badge {status_class}">{status_icon} {status.replace('_', ' ').title()}</span></td>
                            <td><span class="severity-badge {severity_class}">{severity.title()}</span></td>
                        </tr>
"""

            # If no defects, show message
            if not defects:
                html += """
                        <tr>
                            <td colspan="5" style="text-align: center; color: #7f8c8d; font-style: italic;">No defects tracked for this epic</td>
                        </tr>
"""

            html += """
                    </tbody>
                </table>
            </div>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""
        return html

    def generate_epic_progress_json(self, include_charts: bool = True) -> Dict[str, Any]:
        """Generate epic progress report in JSON format."""
        epics = self._get_filtered_epics({"include_demo_data": False})

        report = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_epics": len(epics),
                "include_charts": include_charts
            },
            "epic_progress": []
        }

        for epic in epics:
            epic_data = self._build_epic_data(epic, {"include_tests": True, "include_defects": True})

            # Add time-series data for charts if requested
            if include_charts:
                epic_data["chart_data"] = self._get_epic_chart_data(epic)

            report["epic_progress"].append(epic_data)

        # Overall summary
        total_points = sum(self._get_epic_story_points(epic) for epic in epics)
        completed_points = sum(self._get_epic_completed_points(epic) for epic in epics)

        report["summary"] = {
            "overall_completion": (completed_points / total_points * 100) if total_points > 0 else 0,
            "total_story_points": total_points,
            "completed_story_points": completed_points,
            "epics_by_status": self._get_epic_status_distribution()
        }

        return report

    def generate_epic_progress_html(self, include_charts: bool = True) -> str:
        """Generate epic progress report in HTML format with charts."""
        json_data = self.generate_epic_progress_json(include_charts)

        html = """
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
            <strong>Generated:</strong> """ + json_data["metadata"]["generated_at"] + """<br>
            <strong>Overall Completion:</strong> """ + f"{json_data['summary']['overall_completion']:.1f}%" + """<br>
            <strong>Total Story Points:</strong> """ + str(json_data["summary"]["total_story_points"]) + """
        </div>

        <div class="chart-container">
            <canvas id="overallProgressChart"></canvas>
        </div>

        <div class="epic-grid">
"""

        for epic_data in json_data["epic_progress"]:
            progress = epic_data["metrics"]["completion_percentage"]
            progress_color = "#27ae60" if progress >= 80 else "#f39c12" if progress >= 50 else "#e74c3c"

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

        html += """
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
                    data: [""" + str(json_data["summary"]["completed_story_points"]) + """, """ + str(json_data["summary"]["total_story_points"] - json_data["summary"]["completed_story_points"]) + """],
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
        return html

    def export_full_matrix(self, format: str) -> Tuple[bytes, str, str]:
        """Export full RTM matrix in specified format."""
        if format == "csv":
            return self._export_csv(), "text/csv", f"rtm_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        elif format == "xlsx":
            return self._export_xlsx(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", f"rtm_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        elif format == "pdf":
            return self._export_pdf(), "application/pdf", f"rtm_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _get_filtered_epics(self, filters: Dict[str, Any]) -> List[Epic]:
        """Get epics based on applied filters."""
        query = self.db.query(Epic)

        # Filter out demo data unless explicitly requested
        if not filters.get("include_demo_data", False):
            query = query.filter(~Epic.epic_id.like('EP-DEMO-%'))

        if filters.get("epic_id"):
            query = query.filter(Epic.epic_id == filters["epic_id"])
        if filters.get("status"):
            query = query.filter(Epic.status == filters["status"])
        if filters.get("priority"):
            query = query.filter(Epic.priority == filters["priority"])

        return query.order_by(Epic.epic_id).all()

    def _build_epic_data(self, epic: Epic, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive epic data including metrics."""
        user_stories = self.db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
        tests = self.db.query(Test).filter(Test.epic_id == epic.id).all()
        defects = self.db.query(Defect).filter(Defect.epic_id == epic.id).all()

        # Calculate metrics
        total_story_points = sum(us.story_points for us in user_stories)
        completed_story_points = sum(
            us.story_points for us in user_stories
            if us.implementation_status in ["done", "completed"]
        )

        test_pass_rate = 0.0
        tests_passed = 0
        tests_failed = 0
        tests_skipped = 0
        tests_not_run = 0
        if tests:
            tests_passed = sum(1 for test in tests if test.last_execution_status == "passed")
            tests_failed = sum(1 for test in tests if test.last_execution_status == "failed")
            tests_skipped = sum(1 for test in tests if test.last_execution_status == "skipped")
            tests_not_run = sum(1 for test in tests if test.last_execution_status in ["not_run", "pending", None])
            # Only calculate pass rate for tests that have been executed
            executed_tests = tests_passed + tests_failed + tests_skipped
            test_pass_rate = (tests_passed / executed_tests * 100) if executed_tests > 0 else 0

        # Build base data
        epic_data = {
            "epic": epic.to_dict(),
            "user_stories": [us.to_dict() for us in user_stories],
            "tests": [test.to_dict() for test in tests] if filters.get("include_tests", True) else [],
            "defects": [defect.to_dict() for defect in defects] if filters.get("include_defects", True) else [],
            "metrics": {
                "total_story_points": total_story_points,
                "completed_story_points": completed_story_points,
                "completion_percentage": (completed_story_points / total_story_points * 100) if total_story_points > 0 else 0,
                "user_stories_count": len(user_stories),
                "tests_count": len(tests),
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "tests_skipped": tests_skipped,
                "tests_not_run": tests_not_run,
                "test_pass_rate": test_pass_rate,
                "defects_count": len(defects),
                "critical_defects": sum(1 for d in defects if d.severity == "critical"),
                "open_defects": sum(1 for d in defects if d.status in ["open", "in_progress"]),
            }
        }

        # Apply server-side filtering if filtering parameters are present
        filter_params = {
            'us_status_filter': filters.get('us_status_filter'),
            'test_type_filter': filters.get('test_type_filter'),
            'defect_priority_filter': filters.get('defect_priority_filter'),
            'defect_status_filter': filters.get('defect_status_filter')
        }

        # Only apply filtering if any filter parameters are set
        if any(v and v != 'all' for v in filter_params.values()):
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
            "bdd": "#1abc9c"
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

    def _get_us_filter_display_text(self, epic_data: Dict[str, Any], us_status_filter: str) -> str:
        """Generate display text for user story filter."""
        total_us = len(epic_data.get("user_stories", []))
        if us_status_filter == 'all':
            return f"Showing all user stories ({total_us} total)"
        else:
            filtered_us = [us for us in epic_data.get("user_stories", [])
                          if us.get("implementation_status") == us_status_filter]
            status_display = us_status_filter.replace('_', ' ').title()
            return f"Showing {len(filtered_us)} {status_display} user stories ({total_us} total)"

    def _apply_server_side_filters(self, epic_data: Dict[str, Any], filters: Dict[str, str]) -> Dict[str, Any]:
        """Apply server-side filtering to epic data."""
        filtered_data = epic_data.copy()

        # Filter user stories
        us_status_filter = filters.get('us_status_filter', 'all')
        if us_status_filter != 'all':
            filtered_data["user_stories"] = [
                us for us in epic_data.get("user_stories", [])
                if us.get("implementation_status") == us_status_filter
            ]

        # Filter tests
        test_type_filter = filters.get('test_type_filter', 'all')
        if test_type_filter != 'all':
            filtered_data["tests"] = [
                test for test in epic_data.get("tests", [])
                if test.get("test_type", "").lower() == test_type_filter.lower()
            ]

        # Filter defects
        defect_priority_filter = filters.get('defect_priority_filter', 'all')
        defect_status_filter = filters.get('defect_status_filter', 'all')

        filtered_defects = epic_data.get("defects", [])

        if defect_priority_filter and defect_priority_filter != 'all':
            filtered_defects = [
                defect for defect in filtered_defects
                if defect.get("priority", "").lower() == defect_priority_filter.lower()
            ]

        if defect_status_filter and defect_status_filter != 'all':
            filtered_defects = [
                defect for defect in filtered_defects
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

    def _get_filter_info_html(self, filters: Dict[str, Any]) -> str:
        """Generate HTML filter information."""
        active_filters = {k: v for k, v in filters.items() if v is not None and v != "" and k not in ["include_tests", "include_defects"]}
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

    def _render_user_story_id_link(self, user_story_id: str, github_issue_number: int) -> str:
        """Render user story ID as clickable GitHub link if available."""
        if github_issue_number and github_issue_number > 0:
            github_url = self._get_github_issue_link(github_issue_number)
            return f'<a href="{github_url}" target="_blank" style="color: #3498db; text-decoration: none;">{user_story_id}</a>'
        return user_story_id

    def _render_epic_title_link(self, epic_id: str, title: str, github_issue_number: int) -> str:
        """Render epic title as GitHub link if available."""
        if github_issue_number and github_issue_number > 0:
            github_url = self._get_github_issue_link(github_issue_number)
            return f'<a href="{github_url}" target="_blank" class="epic-title-link" title="Click to open {epic_id} in GitHub">{epic_id}: {title}</a>'
        return f"{epic_id}: {title}"

    def _extract_epic_description(self, github_body: str) -> str:
        """Extract just the Epic Description field from GitHub issue template."""
        if not github_body:
            return "No description provided"

        # Look for the Epic Description section
        import re

        # Pattern to match Epic Description section from GitHub issue template
        epic_desc_pattern = r'### Epic Description\s*\n(.*?)(?=\n### |$)'
        match = re.search(epic_desc_pattern, github_body, re.DOTALL)

        if match:
            description = match.group(1).strip()
            # Clean up markdown formatting
            description = self._clean_markdown(description)
            return description

        # Fallback: look for older format with ## Epic Description
        epic_desc_pattern = r'## Epic Description\s*\n(.*?)(?=\n## |$)'
        match = re.search(epic_desc_pattern, github_body, re.DOTALL)

        if match:
            description = match.group(1).strip()
            description = self._clean_markdown(description)
            return description

        # If no Epic Description section found, return first paragraph or truncated text
        lines = github_body.split('\n')
        clean_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        if clean_lines:
            description = '\n'.join(clean_lines[:5])  # First 5 non-empty, non-header lines
            description = self._clean_markdown(description)
            return description

        return "No description provided"

    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting from text."""
        if not text:
            return ""

        import re

        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

        # Remove bold/italic
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*

        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](url)

        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # Remove bullet points
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)

        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple blank lines to double
        text = text.strip()

        return text

    def _get_epic_chart_data(self, epic: Epic) -> Dict[str, Any]:
        """Get chart data for epic progress over time."""
        # This would typically query historical data
        # For now, return current state
        return {
            "completion_trend": [0, 25, 50, 75, 80],  # Mock data
            "test_execution_trend": [0, 20, 60, 85, 90],  # Mock data
            "defect_trend": [0, 2, 5, 3, 2]  # Mock data
        }

    def _get_epic_story_points(self, epic: Epic) -> int:
        """Get total story points for an epic."""
        return sum(us.story_points for us in self.db.query(UserStory).filter(UserStory.epic_id == epic.id).all())

    def _get_epic_completed_points(self, epic: Epic) -> int:
        """Get completed story points for an epic."""
        user_stories = self.db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
        return sum(us.story_points for us in user_stories if us.implementation_status in ["done", "completed"])

    def _get_epic_status_distribution(self) -> Dict[str, int]:
        """Get distribution of epics by status."""
        status_query = self.db.query(
            Epic.status, func.count(Epic.id).label('count')
        ).group_by(Epic.status).all()

        return {status: count for status, count in status_query}

    def _export_csv(self) -> bytes:
        """Export RTM data as CSV."""
        # Simplified CSV export - would implement full CSV generation
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Headers
        writer.writerow(['Epic ID', 'Epic Title', 'Status', 'User Stories', 'Story Points', 'Tests', 'Defects'])

        # Data
        epics = self._get_filtered_epics({"include_demo_data": False})
        for epic in epics:
            user_stories = self.db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
            tests = self.db.query(Test).filter(Test.epic_id == epic.id).all()
            defects = self.db.query(Defect).filter(Defect.epic_id == epic.id).all()

            writer.writerow([
                epic.epic_id,
                epic.title,
                epic.status,
                len(user_stories),
                sum(us.story_points for us in user_stories),
                len(tests),
                len(defects)
            ])

        return output.getvalue().encode('utf-8')

    def _export_xlsx(self) -> bytes:
        """Export RTM data as Excel file."""
        # Would implement Excel export using openpyxl
        return b"Excel export not yet implemented"

    def _export_pdf(self) -> bytes:
        """Export RTM data as PDF."""
        # Would implement PDF export using reportlab
        return b"PDF export not yet implemented"