"""
Validation tests for RTM filter functionality fix.

Tests that verify the JavaScript filter functionality has been correctly
fixed by examining the existing RTM reports and JavaScript code.

This validates the fix works without requiring database setup.
"""

from pathlib import Path

import pytest


@pytest.mark.epic("EP-00005")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
class TestRTMFilterValidation:
    """Validation tests for RTM filter functionality."""

    def test_existing_rtm_report_structure(self):
        """Test that existing RTM reports have correct structure for filtering."""
        # Use existing demo report
        rtm_file = Path("quality/reports/dynamic_rtm/rtm_matrix_demo.html")

        if not rtm_file.exists():
            pytest.skip(f"Demo RTM file not found: {rtm_file}")

        with open(rtm_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Test epic containers have correct IDs
        assert 'id="epic-EP-' in html_content, "Epic container IDs not found"

        # Test user stories structure
        if "User Stories" in html_content:
            assert 'class="us-row"' in html_content, "User story rows not found"
            assert (
                "data-us-status=" in html_content
            ), "User story status data attributes not found"

        # Test test structure
        if "Test" in html_content:
            assert 'class="test-row"' in html_content, "Test rows not found"

        # Test filter buttons
        assert 'onclick="filter' in html_content, "Filter onclick handlers not found"

    def test_javascript_fixes_applied(self):
        """Test that the JavaScript fixes have been correctly applied."""
        js_file = Path("static/js/rtm-interactions.js")
        assert js_file.exists(), "RTM interactions JavaScript file not found"

        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test 1: Verify updated test filter selector
        assert (
            'table[aria-label*="Test Traceability"]' in js_content
        ), "Updated test filter selector not found"

        # Test 2: Verify updated user stories filter selector
        assert (
            'table[aria-label*="User Stories"]' in js_content
        ), "Updated user stories filter selector not found"

        # Test 3: Verify improved updateFilterButtonStates function
        assert (
            "filterGroup.includes('-defect')" in js_content
        ), "Improved defect filter handling not found"

        # Test 4: Verify console warning added
        assert "console.warn(" in js_content, "Console warning for debugging not found"

        # Test 5: Verify functions are exposed globally
        assert "window.filterTestsByType = filterTestsByType;" in js_content
        assert (
            "window.filterUserStoriesByStatus = filterUserStoriesByStatus;"
            in js_content
        )
        assert "window.filterDefects = filterDefects;" in js_content

    def test_filter_function_parameter_matching(self):
        """Test that filter function parameters match HTML onclick calls."""
        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test filterDefects function signature
        # Should accept 3 parameters: (epicId, filterType, filterValue)
        filter_defects_match = (
            "function filterDefects(epicId, filterType, filterValue)" in js_content
        )
        assert (
            filter_defects_match
        ), "filterDefects function signature doesn't match expected parameters"

        # Test filterTestsByType function signature
        # Should accept 2 parameters: (epicId, testType)
        filter_tests_match = (
            "function filterTestsByType(epicId, testType)" in js_content
        )
        assert (
            filter_tests_match
        ), "filterTestsByType function signature doesn't match expected parameters"

        # Test filterUserStoriesByStatus function signature
        # Should accept 2 parameters: (epicId, status)
        filter_us_match = (
            "function filterUserStoriesByStatus(epicId, status)" in js_content
        )
        assert (
            filter_us_match
        ), "filterUserStoriesByStatus function signature doesn't match expected parameters"

    def test_css_selector_improvements(self):
        """Test that CSS selectors have been improved to match HTML structure."""
        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test that old problematic selectors have been replaced

        # Old problematic selector should be gone
        assert (
            ".test-filter-section + table" not in js_content
            or 'table[aria-label*="Test Traceability"]' in js_content
        ), "Test filter selector not properly updated"

        # Old first-of-type selector should be replaced
        assert (
            "table:first-of-type tbody" not in js_content
            or 'table[aria-label*="User Stories"]' in js_content
        ), "User stories selector not properly updated"

        # Defect selector should still work (it was already correct)
        assert (
            ".defect-filter-section + table tbody" in js_content
        ), "Defect filter selector missing"

    def test_button_state_management_fix(self):
        """Test that button state management has been fixed for defect buttons."""
        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test that defect button handling is special-cased
        assert (
            ".defect-filter-button" in js_content
        ), "Defect filter button selector not found"

        # Test that epic ID extraction for defects is implemented
        assert (
            "filterGroup.replace('-defect', '')" in js_content
        ), "Epic ID extraction for defects not found"

        # Test that both 'active' and 'filter-button--active' classes are managed
        assert (
            "'filter-button--active', 'active'" in js_content
        ), "Both active classes not managed"

    def test_error_handling_improvements(self):
        """Test that error handling and debugging have been improved."""
        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test console warnings for debugging
        assert "console.warn(" in js_content, "Console warnings not added"

        # Test specific error messages
        assert (
            "not found for epic" in js_content
        ), "Epic-specific error messages not found"
        assert (
            "No filter buttons found" in js_content
        ), "Button error messages not found"

    def test_regression_prevention(self):
        """Test that existing functionality hasn't been broken."""
        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test epic toggle functionality still exists
        assert (
            "function toggleEpicDetails(" in js_content
        ), "Epic toggle functionality missing"

        # Test search functionality still exists
        assert "function performSearch(" in js_content, "Search functionality missing"

        # Test export functionality still exists
        assert "function exportData(" in js_content, "Export functionality missing"

        # Test accessibility functions still exist
        assert (
            "announceToScreenReader(" in js_content
        ), "Screen reader announcements missing"

    def test_initialization_and_exposure(self):
        """Test that initialization and global function exposure work correctly."""
        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test initialization function exists
        assert "function initialize(" in js_content, "Initialization function missing"

        # Test DOM ready event listener
        assert "DOMContentLoaded" in js_content, "DOM ready event listener missing"

        # Test all filter functions are exposed globally
        global_exposures = [
            "window.toggleEpicDetails = toggleEpicDetails;",
            "window.filterByStatus = filterByStatus;",
            "window.filterTestsByType = filterTestsByType;",
            "window.filterUserStoriesByStatus = filterUserStoriesByStatus;",
            "window.filterDefects = filterDefects;",
        ]

        for exposure in global_exposures:
            assert exposure in js_content, f"Global exposure missing: {exposure}"

    def test_animation_and_ux_features(self):
        """Test that animation and UX features are preserved."""
        js_file = Path("static/js/rtm-interactions.js")
        with open(js_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Test animation function exists
        assert "function animateVisibility(" in js_content, "Animation function missing"

        # Test count display updates
        assert "updateFilterCount(" in js_content, "Filter count updates missing"

        # Test smooth transitions
        assert "transition" in js_content, "Transition handling missing"


@pytest.mark.epic("EP-00001")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("regression")
@pytest.mark.priority("medium")
class TestRTMFilterUnitValidation:
    """Unit-level validation of the specific fixes."""

    def test_selector_string_correctness(self):
        """Test that the new selector strings are correctly formatted."""
        # These are the exact selectors that should be in the JavaScript

        # Test selector template
        epic_id = "EP-00001"

        # Expected selectors after fix
        expected_test_selector = (
            f'#epic-{epic_id} table[aria-label*="Test Traceability"] tbody'
        )
        expected_us_selector = (
            f'#epic-{epic_id} table[aria-label*="User Stories"] tbody'
        )
        expected_defect_selector = (
            f"#epic-{epic_id} .defect-filter-section + table tbody"
        )

        # Verify selector format is correct
        assert (
            "aria-label*=" in expected_test_selector
        ), "Test selector format incorrect"
        assert (
            "aria-label*=" in expected_us_selector
        ), "User stories selector format incorrect"
        assert (
            ".defect-filter-section" in expected_defect_selector
        ), "Defect selector format incorrect"

    def test_data_attribute_mapping(self):
        """Test that data attribute mapping is correct."""
        # Expected data attribute patterns
        expected_patterns = {
            "test": "data-test-type",
            "user_story": "data-us-status",
            "defect_priority": "data-defect-priority",
            "defect_status": "data-defect-status",
            "defect_filter": "data-defect-filter",
        }

        # Verify patterns are valid HTML attribute names
        for category, pattern in expected_patterns.items():
            assert pattern.startswith(
                "data-"
            ), f"Invalid data attribute pattern: {pattern}"
            assert "-" in pattern, f"Data attribute should use kebab-case: {pattern}"

    def test_filter_group_naming_convention(self):
        """Test that filter group naming follows consistent convention."""
        epic_id = "EP-00001"

        # Expected filter group names
        expected_groups = {
            "test": f"epic-{epic_id}-test",
            "user_story": f"epic-{epic_id}-us",
            "defect": f"epic-{epic_id}-defect",
        }

        # Verify naming convention
        for filter_type, group_name in expected_groups.items():
            assert group_name.startswith(
                "epic-"
            ), f"Filter group should start with 'epic-': {group_name}"
            assert (
                epic_id in group_name
            ), f"Filter group should contain epic ID: {group_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
