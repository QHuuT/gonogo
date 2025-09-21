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
        """Generate RTM matrix in HTML format with interactive features."""
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
            const testTable = document.querySelector(`#epic-${epicId} table:last-of-type tbody`);
            if (!testTable) return;

            const testRows = testTable.querySelectorAll('tr');
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
                if (row.children.length === 1) return; // Skip "no tests" row

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
                        <div class="metric-value">{epic_data["metrics"]["user_stories_count"]}</div>
                        <div class="metric-label">User Stories</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{epic_data["metrics"]["completed_story_points"]}/{epic_data["metrics"]["total_story_points"]}</div>
                        <div class="metric-label">Story Points</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{epic_data["metrics"]["tests_count"]}</div>
                        <div class="metric-label">Tests</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{epic_data["metrics"]["test_pass_rate"]:.1f}%</div>
                        <div class="metric-label">Pass Rate ({epic_data["metrics"]["tests_passed"]}/{epic_data["metrics"]["tests_count"]})</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{epic_data["metrics"]["defects_count"]}</div>
                        <div class="metric-label">Defects</div>
                    </div>
                </div>

                <h4>User Stories</h4>
                <table>
                    <thead>
                        <tr><th>ID</th><th>Title</th><th>Story Points</th><th>Status</th></tr>
                    </thead>
                    <tbody>
"""
            for us in epic_data["user_stories"]:
                user_story_link = self._render_user_story_id_link(us["user_story_id"], us.get("github_issue_number"))
                html += f"""
                        <tr>
                            <td>{user_story_link}</td>
                            <td>{us["title"]}</td>
                            <td>{us["story_points"]}</td>
                            <td><span class="status-badge status-{us["implementation_status"].replace('_', '-')}">{us["implementation_status"].replace('_', ' ').title()}</span></td>
                        </tr>
"""

            html += """
                    </tbody>
                </table>

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
                        <tr><th>Test Type</th><th>Test File</th><th>Function/Scenario</th><th>Last Execution</th><th>Status</th><th>Duration</th></tr>
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

                # Format duration
                duration = test.get("execution_duration_ms", 0)
                duration_str = f"{duration}ms" if duration else "-"

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
                            <td>{duration_str}</td>
                        </tr>
"""

            # If no tests, show message
            if not epic_data.get("tests", []):
                html += """
                        <tr>
                            <td colspan="6" style="text-align: center; color: #7f8c8d; font-style: italic;">No tests available for this epic</td>
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
        epics = self.db.query(Epic).order_by(Epic.epic_id).all()

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

            html += f"""
            <div class="epic-card">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div class="progress-circle" style="background: {progress_color};">
                        {progress:.0f}%
                    </div>
                    <div style="margin-left: 15px;">
                        <h3 style="margin: 0;">{epic_data["epic"]["epic_id"]}</h3>
                        <p style="margin: 5px 0; color: #666;">{epic_data["epic"]["title"]}</p>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px;">
                    <div><strong>Story Points:</strong> {epic_data["metrics"]["completed_story_points"]}/{epic_data["metrics"]["total_story_points"]}</div>
                    <div><strong>User Stories:</strong> {epic_data["metrics"]["user_stories_count"]}</div>
                    <div><strong>Tests:</strong> {epic_data["metrics"]["tests_count"]}</div>
                    <div><strong>Test Pass Rate:</strong> {epic_data["metrics"]["test_pass_rate"]:.1f}%</div>
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
        if tests:
            tests_passed = sum(1 for test in tests if test.last_execution_status == "passed")
            tests_failed = sum(1 for test in tests if test.last_execution_status == "failed")
            tests_skipped = sum(1 for test in tests if test.last_execution_status == "skipped")
            test_pass_rate = (tests_passed / len(tests)) * 100

        return {
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
                "test_pass_rate": test_pass_rate,
                "defects_count": len(defects),
                "critical_defects": sum(1 for d in defects if d.severity == "critical"),
                "open_defects": sum(1 for d in defects if d.status in ["open", "in_progress"]),
            }
        }

    def _get_test_counts(self, tests: List[Test]) -> Dict[str, int]:
        """Get test counts by type."""
        return {
            "unit": sum(1 for t in tests if t.test_type == "unit"),
            "integration": sum(1 for t in tests if t.test_type == "integration"),
            "bdd": sum(1 for t in tests if t.test_type == "bdd"),
        }

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
        epics = self.db.query(Epic).order_by(Epic.epic_id).all()
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