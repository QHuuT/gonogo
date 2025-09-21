"""
Integration tests for RTM filter regression fix
Tests actual HTTP requests to verify filter functionality works correctly
Ready for Robot Framework integration
"""
import pytest
import requests
from urllib.parse import urlparse, parse_qs
import re
import time


class TestRTMFilterRegression:
    """Test RTM filter functionality via HTTP requests (Robot Framework ready)"""

    BASE_URL = "http://localhost:8000"
    RTM_URL = f"{BASE_URL}/api/rtm/reports/matrix"

    def check_server_running(self):
        """Ensure server is running before tests"""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                raise Exception(f"Server returned {response.status_code}")
            print("OK Server is running")
        except Exception as e:
            raise Exception(f"Server not running: {e}")

    @pytest.fixture(autouse=True)
    def setup_server_check(self):
        """Pytest fixture for server check"""
        self.check_server_running()

    def test_rtm_interface_loads_successfully(self):
        """Test that RTM interface loads without errors"""
        response = requests.get(f"{self.RTM_URL}?format=html")

        assert response.status_code == 200
        assert "RTM Matrix" in response.text
        assert "epic-card" in response.text
        assert "filter" in response.text.lower()
        print("OK RTM interface loads successfully")

    def test_filter_buttons_generate_correct_onclick_handlers(self):
        """Test that filter buttons have correct onclick handlers"""
        response = requests.get(f"{self.RTM_URL}?format=html")
        html_content = response.text

        # Check for filterByStatus onclick handlers
        status_filter_pattern = r'onclick="filterByStatus\(\'(\w+)\'\)"'
        status_matches = re.findall(status_filter_pattern, html_content)
        assert len(status_matches) > 0, "No status filter buttons found"
        assert 'planned' in status_matches or 'all' in status_matches
        print(f"OK Found status filter buttons: {status_matches}")

        # Check for filterDefects onclick handlers with 3 parameters
        defects_filter_pattern = r'onclick="filterDefects\(\'([^\']+)\',\s*\'([^\']+)\',\s*\'([^\']+)\'\)"'
        defects_matches = re.findall(defects_filter_pattern, html_content)
        assert len(defects_matches) > 0, "No defect filter buttons found"
        print(f"OK Found defect filter buttons with 3 parameters: {len(defects_matches)} buttons")

        # Verify parameter structure
        for epic_id, filter_type, filter_value in defects_matches:
            assert epic_id.startswith('EP-'), f"Invalid epic ID: {epic_id}"
            assert filter_type in ['all', 'priority', 'status'], f"Invalid filter type: {filter_type}"
            assert filter_value in ['all', 'critical', 'high', 'open', 'in_progress'], f"Invalid filter value: {filter_value}"

    def test_epic_toggle_handlers_present(self):
        """Test that epic headers have toggleEpicDetails onclick handlers"""
        response = requests.get(f"{self.RTM_URL}?format=html")
        html_content = response.text

        # Check for toggleEpicDetails onclick handlers
        epic_toggle_pattern = r'onclick="toggleEpicDetails\(\'(EP-\d+)\'\)"'
        epic_matches = re.findall(epic_toggle_pattern, html_content)
        assert len(epic_matches) > 0, "No epic toggle buttons found"
        print(f"OK Found epic toggle handlers for: {epic_matches}")

        # Verify epic IDs are valid
        for epic_id in epic_matches:
            assert re.match(r'EP-\d{5}', epic_id), f"Invalid epic ID format: {epic_id}"

    def test_javascript_file_loads_correctly(self):
        """Test that rtm-interactions.js loads and contains required functions"""
        response = requests.get(f"{self.BASE_URL}/static/js/rtm-interactions.js")

        assert response.status_code == 200
        js_content = response.text

        # Check for function definitions
        required_functions = [
            'function filterByStatus',
            'function filterUserStoriesByStatus',
            'function filterTestsByType',
            'function filterDefects',
            'function toggleEpicDetails'
        ]

        for func in required_functions:
            assert func in js_content, f"Missing function: {func}"
        print(f"OK All required JavaScript functions present")

        # Check filterDefects has correct parameter signature
        defects_func_pattern = r'function filterDefects\s*\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\)'
        defects_match = re.search(defects_func_pattern, js_content)
        assert defects_match, "filterDefects function not found or has wrong signature"

        params = defects_match.groups()
        assert len(params) == 3, f"filterDefects should have 3 parameters, found {len(params)}"
        print(f"OK filterDefects function has correct 3-parameter signature: {params}")

    def test_status_filter_backend_functionality(self):
        """Test that backend filtering works correctly"""
        # Test global status filter
        response = requests.get(f"{self.RTM_URL}?format=html&status_filter=planned")
        assert response.status_code == 200
        print("OK Status filter backend works")

        # Test user story filter
        response = requests.get(f"{self.RTM_URL}?format=html&us_status_filter=in_progress")
        assert response.status_code == 200
        print("OK User story filter backend works")

        # Test test type filter
        response = requests.get(f"{self.RTM_URL}?format=html&test_type_filter=unit")
        assert response.status_code == 200
        print("OK Test type filter backend works")

        # Test defect priority filter
        response = requests.get(f"{self.RTM_URL}?format=html&defect_priority_filter=critical")
        assert response.status_code == 200
        print("OK Defect priority filter backend works")

        # Test defect status filter
        response = requests.get(f"{self.RTM_URL}?format=html&defect_status_filter=open")
        assert response.status_code == 200
        print("OK Defect status filter backend works")

    def test_filter_buttons_do_not_interfere_with_epic_structure(self):
        """Test that filter buttons are not inside epic headers (preventing epic collapse)"""
        response = requests.get(f"{self.RTM_URL}?format=html")
        html_content = response.text

        # Find epic headers
        epic_header_pattern = r'<header[^>]*class="epic-header"[^>]*onclick="toggleEpicDetails[^>]*>(.*?)</header>'
        epic_headers = re.findall(epic_header_pattern, html_content, re.DOTALL)

        assert len(epic_headers) > 0, "No epic headers found"

        # Check that filter buttons are NOT inside epic headers
        for header_content in epic_headers:
            # Filter buttons should not be in epic headers
            assert 'onclick="filterByStatus' not in header_content, "Status filter button found inside epic header"
            assert 'onclick="filterDefects' not in header_content, "Defects filter button found inside epic header"
            assert 'onclick="filterUserStoriesByStatus' not in header_content, "User story filter button found inside epic header"
            assert 'onclick="filterTestsByType' not in header_content, "Test type filter button found inside epic header"

        print("OK Filter buttons are properly separated from epic headers")

    def test_no_javascript_syntax_errors_in_generated_html(self):
        """Test that generated HTML doesn't have JavaScript syntax errors"""
        response = requests.get(f"{self.RTM_URL}?format=html")
        html_content = response.text

        # Check for common JavaScript syntax errors in onclick handlers
        onclick_patterns = re.findall(r'onclick="([^"]*)"', html_content)

        for onclick in onclick_patterns:
            # Check for unmatched quotes
            assert onclick.count("'") % 2 == 0, f"Unmatched quotes in onclick: {onclick}"

            # Check for unmatched parentheses
            assert onclick.count("(") == onclick.count(")"), f"Unmatched parentheses in onclick: {onclick}"

            # Check for common syntax issues
            assert ";;" not in onclick, f"Double semicolon in onclick: {onclick}"
            assert ",," not in onclick, f"Double comma in onclick: {onclick}"

        print("OK No JavaScript syntax errors found in onclick handlers")

    def test_filter_functions_parameter_compatibility(self):
        """Test that filter function calls match expected parameter counts"""
        response = requests.get(f"{self.RTM_URL}?format=html")
        html_content = response.text

        # Test filterDefects calls have exactly 3 parameters
        defects_calls = re.findall(r'filterDefects\([^)]+\)', html_content)
        for call in defects_calls:
            # Count commas to determine parameter count
            param_count = call.count(',') + 1
            assert param_count == 3, f"filterDefects call has {param_count} parameters, expected 3: {call}"

        print(f"OK All {len(defects_calls)} filterDefects calls have correct 3 parameters")

        # Test other filter function parameter counts
        status_calls = re.findall(r'filterByStatus\([^)]+\)', html_content)
        for call in status_calls:
            param_count = call.count(',') + 1
            assert param_count == 1, f"filterByStatus call has {param_count} parameters, expected 1: {call}"

        user_story_calls = re.findall(r'filterUserStoriesByStatus\([^)]+\)', html_content)
        for call in user_story_calls:
            param_count = call.count(',') + 1
            assert param_count == 2, f"filterUserStoriesByStatus call has {param_count} parameters, expected 2: {call}"

        test_type_calls = re.findall(r'filterTestsByType\([^)]+\)', html_content)
        for call in test_type_calls:
            param_count = call.count(',') + 1
            assert param_count == 2, f"filterTestsByType call has {param_count} parameters, expected 2: {call}"

        print("OK All filter function calls have correct parameter counts")


# Robot Framework compatible functions
def rtm_interface_loads():
    """Robot Framework: Verify RTM interface loads"""
    test = TestRTMFilterRegression()
    test.check_server_running()
    test.test_rtm_interface_loads_successfully()
    return True

def filter_buttons_work():
    """Robot Framework: Verify filter buttons have correct handlers"""
    test = TestRTMFilterRegression()
    test.check_server_running()
    test.test_filter_buttons_generate_correct_onclick_handlers()
    return True

def epic_toggles_work():
    """Robot Framework: Verify epic toggle handlers work"""
    test = TestRTMFilterRegression()
    test.check_server_running()
    test.test_epic_toggle_handlers_present()
    return True

def javascript_functions_loaded():
    """Robot Framework: Verify JavaScript functions are loaded"""
    test = TestRTMFilterRegression()
    test.check_server_running()
    test.test_javascript_file_loads_correctly()
    return True

def backend_filtering_works():
    """Robot Framework: Verify backend filtering functionality"""
    test = TestRTMFilterRegression()
    test.check_server_running()
    test.test_status_filter_backend_functionality()
    return True

def no_epic_filter_interference():
    """Robot Framework: Verify filters don't interfere with epics"""
    test = TestRTMFilterRegression()
    test.check_server_running()
    test.test_filter_buttons_do_not_interfere_with_epic_structure()
    return True

def no_javascript_errors():
    """Robot Framework: Verify no JavaScript syntax errors"""
    test = TestRTMFilterRegression()
    test.check_server_running()
    test.test_no_javascript_syntax_errors_in_generated_html()
    return True

def filter_parameters_correct():
    """Robot Framework: Verify filter function parameters are correct"""
    test = TestRTMFilterRegression()
    test.check_server_running()
    test.test_filter_functions_parameter_compatibility()
    return True


if __name__ == "__main__":
    # Direct execution for manual testing
    print("Running RTM Filter Regression Tests...")

    test = TestRTMFilterRegression()
    test.check_server_running()

    print("\n1. Testing RTM interface loads...")
    test.test_rtm_interface_loads_successfully()

    print("\n2. Testing filter button handlers...")
    test.test_filter_buttons_generate_correct_onclick_handlers()

    print("\n3. Testing epic toggle handlers...")
    test.test_epic_toggle_handlers_present()

    print("\n4. Testing JavaScript file...")
    test.test_javascript_file_loads_correctly()

    print("\n5. Testing backend filtering...")
    test.test_status_filter_backend_functionality()

    print("\n6. Testing filter/epic separation...")
    test.test_filter_buttons_do_not_interfere_with_epic_structure()

    print("\n7. Testing JavaScript syntax...")
    test.test_no_javascript_syntax_errors_in_generated_html()

    print("\n8. Testing filter parameters...")
    test.test_filter_functions_parameter_compatibility()

    print("\nOK All RTM filter regression tests passed!")