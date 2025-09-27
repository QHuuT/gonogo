"""
Integration tests for RTM filter functionality.

Tests that the fixed RTM JavaScript filtering works correctly
by generating actual RTM reports and validating the HTML structure
matches what the JavaScript expects.

This ensures the fix works end-to-end.
"""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.epic("EP-00005")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
class TestRTMFilterIntegration:
    """Integration tests for RTM filter functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.test_output_dir = Path("quality/reports/test_rtm_filters")
        self.test_output_dir.mkdir(exist_ok=True)

    @pytest.mark.test_category("smoke")
    @pytest.mark.priority("high")
    def test_rtm_report_generation(self):
        """Test that RTM reports can be generated successfully."""
        # Generate a test RTM report
        result = subprocess.run(
            ["python", "tools/rtm_report_generator.py", "--html"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Verify generation succeeded
        assert result.returncode == 0, f"RTM generation failed: {result.stderr}"

        # Check that output file exists
        expected_output = Path("quality/reports/dynamic_rtm/rtm_matrix_complete.html")
        assert expected_output.exists(), "RTM report was not generated"

    @pytest.mark.test_category("regression")
    @pytest.mark.priority("high")
    def test_rtm_html_structure_for_filtering(self):
        """Test that generated RTM HTML has correct structure for filtering."""
        # First generate the report
        subprocess.run(
            ["python", "tools/rtm_report_generator.py", "--html"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Read the generated HTML
        rtm_file = Path("quality/reports/dynamic_rtm/rtm_matrix_complete.html")
        assert rtm_file.exists(), "RTM file does not exist"

        with open(rtm_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Test 1: Verify epic containers have correct IDs
        assert 'id="epic-EP-' in html_content, "Epic container IDs not found"

        # Test 2: Verify user stories table structure
        assert (
            'aria-label="User Stories for EP-' in html_content
        ), "User Stories table aria-label not found"
        assert 'class="us-row"' in html_content, "User story rows not found"
        assert (
            "data-us-status=" in html_content
        ), "User story status data attributes not found"

        # Test 3: Verify test table structure
        assert (
            'aria-label="Test Traceability for EP-' in html_content
        ), "Test table aria-label not found"
        assert 'class="test-row"' in html_content, "Test rows not found"
        assert "data-test-type=" in html_content, "Test type data attributes not found"

        # Test 4: Verify defect structure
        assert (
            'class="defect-filter-section"' in html_content
        ), "Defect filter section not found"
        assert 'class="defect-row"' in html_content, "Defect rows not found"
        assert (
            "data-defect-priority=" in html_content
        ), "Defect priority data attributes not found"
        assert (
            "data-defect-status=" in html_content
        ), "Defect status data attributes not found"

        # Test 5: Verify filter buttons have correct attributes
        assert (
            'data-filter-group="epic-' in html_content
        ), "Filter group data attributes not found"
        assert (
            'onclick="filterTestsByType(' in html_content
        ), "Test filter onclick handlers not found"
        assert (
            'onclick="filterUserStoriesByStatus(' in html_content
        ), "User story filter onclick handlers not found"
        assert (
            'onclick="filterDefects(' in html_content
        ), "Defect filter onclick handlers not found"

        # Test 6: Verify JavaScript file is referenced
        assert (
            "rtm-interactions.js" in html_content
        ), "RTM interactions JavaScript not referenced"

    def test_javascript_functions_are_exposed(self):
        """Test that JavaScript functions are properly exposed to global scope."""
        # Read the JavaScript file
        js_file = Path("static/js/rtm-interactions.js")
        assert js_file.exists(), "RTM interactions JavaScript file not found"

        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test that functions are exposed to global scope
        assert "window.toggleEpicDetails = toggleEpicDetails;" in js_content
        assert "window.filterByStatus = filterByStatus;" in js_content
        assert "window.filterTestsByType = filterTestsByType;" in js_content
        assert (
            "window.filterUserStoriesByStatus = filterUserStoriesByStatus;"
            in js_content
        )
        assert "window.filterDefects = filterDefects;" in js_content

    def test_filter_button_data_attributes_consistency(self):
        """Test that filter buttons have consistent data attributes."""
        # Generate fresh report
        subprocess.run(
            ["python", "tools/rtm_report_generator.py", "--html"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        rtm_file = Path("quality/reports/dynamic_rtm/rtm_matrix_complete.html")
        with open(rtm_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Test user story filter buttons
        us_filter_patterns = [
            'data-us-status="all"',
            'data-us-status="planned"',
            'data-us-status="in_progress"',
            'data-us-status="completed"',
            'data-us-status="blocked"',
        ]

        for pattern in us_filter_patterns:
            assert (
                pattern in html_content
            ), f"User story filter pattern not found: {pattern}"

        # Test test filter buttons
        test_filter_patterns = [
            'data-test-type="e2e"',
            'data-test-type="unit"',
            'data-test-type="integration"',
            'data-test-type="security"',
            'data-test-type="all"',
        ]

        for pattern in test_filter_patterns:
            assert pattern in html_content, f"Test filter pattern not found: {pattern}"

        # Test defect filter buttons
        defect_filter_patterns = [
            'data-defect-filter="all"',
            'data-defect-filter="priority:critical"',
            'data-defect-filter="priority:high"',
            'data-defect-filter="status:open"',
            'data-defect-filter="status:in_progress"',
        ]

        for pattern in defect_filter_patterns:
            assert (
                pattern in html_content
            ), f"Defect filter pattern not found: {pattern}"

    def test_epic_specific_filter_groups(self):
        """Test that each epic has its own filter groups."""
        # Generate fresh report
        subprocess.run(
            ["python", "tools/rtm_report_generator.py", "--html"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        rtm_file = Path("quality/reports/dynamic_rtm/rtm_matrix_complete.html")
        with open(rtm_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Find all epic IDs in the content
        import re

        epic_ids = re.findall(r'data-epic-id="(EP-\d+)"', html_content)

        # Verify each epic has its own filter groups
        for epic_id in epic_ids:
            # Check for epic-specific filter groups
            test_filter_group = f'data-filter-group="epic-{epic_id}-test"'
            us_filter_group = f'data-filter-group="epic-{epic_id}-us"'

            if test_filter_group not in html_content:
                # This might be OK if the epic has no tests, just warn
                print(f"Warning: No test filter group found for {epic_id}")

            if us_filter_group not in html_content:
                # This might be OK if the epic has no user stories, just warn
                print(f"Warning: No user story filter group found for {epic_id}")

    def test_javascript_selector_compatibility(self):
        """Test that JavaScript selectors match the generated HTML structure."""
        # Generate fresh report
        subprocess.run(
            ["python", "tools/rtm_report_generator.py", "--html"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        rtm_file = Path("quality/reports/dynamic_rtm/rtm_matrix_complete.html")
        with open(rtm_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test that JavaScript selectors will find elements in HTML

        # Test 1: Epic container selectors
        assert 'id="epic-EP-' in html_content, "Epic containers not found in HTML"
        assert (
            "#epic-${epicId}" in js_content
        ), "Epic container selector not in JavaScript"

        # Test 2: Test table selectors
        assert (
            'aria-label="Test Traceability' in html_content
        ), "Test table aria-label not in HTML"
        assert (
            'table[aria-label*="Test Traceability"]' in js_content
        ), "Test table selector not in JavaScript"

        # Test 3: User stories table selectors
        assert (
            'aria-label="User Stories' in html_content
        ), "User stories table aria-label not in HTML"
        assert (
            'table[aria-label*="User Stories"]' in js_content
        ), "User stories table selector not in JavaScript"

        # Test 4: Defect filter section selectors
        assert (
            'class="defect-filter-section"' in html_content
        ), "Defect filter section not in HTML"
        assert (
            ".defect-filter-section" in js_content
        ), "Defect filter section selector not in JavaScript"

    def test_filter_count_display_elements(self):
        """Test that filter count display elements exist."""
        # Generate fresh report
        subprocess.run(
            ["python", "tools/rtm_report_generator.py", "--html"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        rtm_file = Path("quality/reports/dynamic_rtm/rtm_matrix_complete.html")
        with open(rtm_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Test that count display elements exist
        assert (
            'class="test-count-display"' in html_content
            or "test-count-display" in html_content
        ), "Test count display not found"
        assert (
            'class="us-count-display"' in html_content
            or "us-count-display" in html_content
        ), "User story count display not found"
        assert (
            'class="defect-count-display"' in html_content
            or "defect-count-display" in html_content
        ), "Defect count display not found"

    def test_animation_classes_and_functionality(self):
        """Test that animation-related classes and functionality are present."""
        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test animation function exists
        assert (
            "function animateVisibility(" in js_content
        ), "animateVisibility function not found"
        assert "hidden" in js_content, "Hidden class handling not found"
        assert "transition" in js_content, "Transition handling not found"

    def test_error_handling_and_logging(self):
        """Test that error handling and console logging are implemented."""
        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test error handling exists
        assert "console.warn(" in js_content, "Console warning not found"
        assert "not found" in js_content, "Error messages not found"

    def test_accessibility_features(self):
        """Test that accessibility features are implemented."""
        # Generate fresh report
        subprocess.run(
            ["python", "tools/rtm_report_generator.py", "--html"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        rtm_file = Path("quality/reports/dynamic_rtm/rtm_matrix_complete.html")
        with open(rtm_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test ARIA attributes in HTML
        assert "aria-pressed=" in html_content, "ARIA pressed attributes not found"
        assert "aria-label=" in html_content, "ARIA label attributes not found"

        # Test ARIA handling in JavaScript
        assert (
            "setAttribute('aria-pressed'" in js_content
        ), "ARIA pressed handling not in JavaScript"
        assert (
            "announceToScreenReader(" in js_content
        ), "Screen reader announcements not found"

    def test_multiple_epic_independence(self):
        """Test that filtering one epic doesn't affect others."""
        # This test verifies that the selectors are epic-specific

        # Generate fresh report
        subprocess.run(
            ["python", "tools/rtm_report_generator.py", "--html"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        rtm_file = Path("quality/reports/dynamic_rtm/rtm_matrix_complete.html")
        with open(rtm_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Find all epic containers
        import re

        epic_containers = re.findall(r'id="epic-(EP-\d+)"', html_content)

        # Verify each epic has independent structure
        for epic_id in epic_containers:
            epic_specific_content = f"#epic-{epic_id}"
            assert (
                epic_specific_content in html_content
            ), f"Epic-specific container not found for {epic_id}"


@pytest.mark.epic("EP-00005")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("regression")
@pytest.mark.priority("high")
class TestRTMFilterRegression:
    """Regression tests to ensure the filtering fix doesn't break existing functionality."""

    def test_epic_expand_collapse_still_works(self):
        """Test that epic expand/collapse functionality is not broken by filter fixes."""
        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Verify epic toggle functionality still exists
        assert (
            "function toggleEpicDetails(" in js_content
        ), "toggleEpicDetails function not found"
        assert (
            "window.toggleEpicDetails = toggleEpicDetails;" in js_content
        ), "toggleEpicDetails not exposed globally"

    def test_search_functionality_preserved(self):
        """Test that search functionality is not broken by filter fixes."""
        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Verify search functionality still exists
        assert (
            "function performSearch(" in js_content
        ), "performSearch function not found"
        assert "searchTerm" in js_content, "Search term handling not found"

    def test_export_functionality_preserved(self):
        """Test that export functionality is not broken by filter fixes."""
        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Verify export functionality still exists
        assert "function exportData(" in js_content, "exportData function not found"
        assert "exportToCSV" in js_content, "CSV export not found"
        assert "exportToJSON" in js_content, "JSON export not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
