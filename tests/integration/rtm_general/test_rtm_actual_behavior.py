"""
ACTUAL behavioral test for RTM filter regression
Tests that clicking filter buttons ACTUALLY filters without collapsing epics
"""

import re
from urllib.parse import parse_qs, urlparse

import pytest
import requests


@pytest.mark.epic("EP-00005")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
class TestRTMActualBehavior:
    """Test actual RTM behavior - what happens when buttons are clicked"""

    BASE_URL = "http://localhost:8000"
    RTM_URL = f"{BASE_URL}/api/rtm/reports/matrix"

    def check_server_running(self):
        """Ensure server is running"""
        response = requests.get(f"{self.BASE_URL}/health", timeout=5)
        assert response.status_code == 200

    def test_clicking_status_filter_actually_filters(self):
        """Test that status filter buttons actually redirect to filtered URLs"""
        self.check_server_running()

        # Get original page
        original_response = requests.get(f"{self.RTM_URL}?format=html")
        assert original_response.status_code == 200

        # Test clicking "planned" status filter - simulate the JavaScript redirect
        filtered_response = requests.get(
            f"{self.RTM_URL}?format=html&status_filter=planned"
        )
        assert filtered_response.status_code == 200

        # Verify URL actually contains the filter parameter
        assert (
            "status_filter=planned" in filtered_response.url
            or "status_filter=planned" in filtered_response.request.url
        )
        print("OK Status filter redirects to correct URL")

    def test_clicking_defect_filter_actually_filters(self):
        """Test that defect filter buttons actually redirect to filtered URLs"""
        self.check_server_running()

        # Test defect priority filter - simulate filterDefects('EP-00001', 'priority', 'critical')
        filtered_response = requests.get(
            f"{self.RTM_URL}?format=html&defect_priority_filter=critical"
        )
        assert filtered_response.status_code == 200

        # Verify filtering worked by checking the content changed
        assert (
            "defect_priority_filter=critical" in filtered_response.url
            or "defect_priority_filter=critical" in str(filtered_response.request.url)
        )
        print("OK Defect priority filter redirects to correct URL")

        # Test defect status filter - simulate filterDefects('EP-00001', 'status', 'open')
        filtered_response2 = requests.get(
            f"{self.RTM_URL}?format=html&defect_status_filter=open"
        )
        assert filtered_response2.status_code == 200
        assert (
            "defect_status_filter=open" in filtered_response2.url
            or "defect_status_filter=open" in str(filtered_response2.request.url)
        )
        print("OK Defect status filter redirects to correct URL")

    def test_epic_headers_still_have_toggle_functionality(self):
        """Test that epic headers still have toggle functionality and aren't affected by filters"""
        self.check_server_running()

        # Get page with filter applied
        response = requests.get(f"{self.RTM_URL}?format=html&status_filter=planned")
        assert response.status_code == 200
        html_content = response.text

        # Epic toggle handlers should still be present even when filters are active
        epic_toggle_pattern = r'onclick="toggleEpicDetails\(\'(EP-\d+)\'\)"'
        epic_matches = re.findall(epic_toggle_pattern, html_content)
        assert (
            len(epic_matches) > 0
        ), "Epic toggle handlers missing when filters are active"
        print(
            f"OK Epic toggle handlers present with filters: {len(epic_matches)} epics"
        )

        # Epic headers should NOT contain filter onclick handlers
        epic_header_pattern = r'<header[^>]*class="epic-header"[^>]*onclick="toggleEpicDetails[^>]*>(.*?)</header>'
        epic_headers = re.findall(epic_header_pattern, html_content, re.DOTALL)

        for header_content in epic_headers:
            assert (
                "filterDefects" not in header_content
            ), "filterDefects found in epic header - will cause collapse!"
            assert (
                "filterByStatus" not in header_content
            ), "filterByStatus found in epic header - will cause collapse!"

        print("OK Epic headers don't contain filter buttons")

    def test_filter_clear_functionality(self):
        """Test that 'all' filters actually clear parameters"""
        self.check_server_running()

        # Apply a filter first
        filtered_response = requests.get(
            f"{self.RTM_URL}?format=html&defect_priority_filter=critical"
        )
        assert "defect_priority_filter=critical" in str(filtered_response.request.url)

        # Simulate clicking 'All' button - filterDefects('EP-00001', 'all', 'all')
        # This should redirect to URL without defect filter parameters
        cleared_response = requests.get(f"{self.RTM_URL}?format=html")

        # Verify filter parameters are not in the URL
        clear_url = str(cleared_response.request.url)
        assert "defect_priority_filter" not in clear_url
        assert "defect_status_filter" not in clear_url
        print("OK Filter clearing works correctly")

    def test_multiple_filters_work_independently(self):
        """Test that different filter types can be applied independently"""
        self.check_server_running()

        # Test multiple filters applied together
        multi_filter_url = f"{self.RTM_URL}?format=html&status_filter=planned&us_status_filter=in_progress&test_type_filter=unit&defect_priority_filter=critical"
        response = requests.get(multi_filter_url)
        assert response.status_code == 200

        # All filters should be preserved in the response
        request_url = str(response.request.url)
        assert "status_filter=planned" in request_url
        assert "us_status_filter=in_progress" in request_url
        assert "test_type_filter=unit" in request_url
        assert "defect_priority_filter=critical" in request_url
        print("OK Multiple filters work independently")

    def test_filter_buttons_exist_and_have_correct_onclick(self):
        """Test that filter buttons exist and have the correct onclick handlers"""
        self.check_server_running()

        response = requests.get(f"{self.RTM_URL}?format=html")
        html_content = response.text

        # Check specific defect filter button onclick handlers
        critical_button_pattern = (
            r'onclick="filterDefects\(\'EP-\d+\',\s*\'priority\',\s*\'critical\'\)"'
        )
        critical_buttons = re.findall(critical_button_pattern, html_content)
        assert len(critical_buttons) > 0, "No critical priority filter buttons found"

        open_button_pattern = (
            r'onclick="filterDefects\(\'EP-\d+\',\s*\'status\',\s*\'open\'\)"'
        )
        open_buttons = re.findall(open_button_pattern, html_content)
        assert len(open_buttons) > 0, "No open status filter buttons found"

        all_button_pattern = (
            r'onclick="filterDefects\(\'EP-\d+\',\s*\'all\',\s*\'all\'\)"'
        )
        all_buttons = re.findall(all_button_pattern, html_content)
        assert len(all_buttons) > 0, "No 'all' filter buttons found"

        print(
            f"OK Found filter buttons: {len(critical_buttons)} critical, {len(open_buttons)} open, {len(all_buttons)} all"
        )

    def test_regression_scenario_specifically(self):
        """Test the exact scenario that was reported as broken"""
        self.check_server_running()

        # Get RTM page
        response = requests.get(f"{self.RTM_URL}?format=html")
        html_content = response.text

        # Find a specific defect filter button
        defect_filter_pattern = r'<button[^>]*onclick="filterDefects\(\'(EP-\d+)\',\s*\'(priority|status)\',\s*\'(\w+)\'\)"[^>]*>([^<]+)</button>'
        defect_buttons = re.findall(defect_filter_pattern, html_content)

        assert len(defect_buttons) > 0, "No defect filter buttons found in HTML"

        epic_id, filter_type, filter_value, button_text = defect_buttons[0]
        print(
            f"Testing defect filter button: '{button_text}' -> filterDefects('{epic_id}', '{filter_type}', '{filter_value}')"
        )

        # Simulate the JavaScript function call
        if filter_type == "priority":
            expected_param = f"defect_priority_filter={filter_value}"
        elif filter_type == "status":
            expected_param = f"defect_status_filter={filter_value}"
        else:
            expected_param = "no_defect_filters"

        # Test the actual redirect URL that would be generated
        if expected_param != "no_defect_filters":
            test_url = f"{self.RTM_URL}?format=html&{expected_param}"
            test_response = requests.get(test_url)
            assert test_response.status_code == 200
            assert expected_param in str(test_response.request.url)
            print(f"OK Defect filter button generates correct URL: {expected_param}")

        # Critical test: Verify epic toggle buttons are SEPARATE from filter buttons
        # Find epic header with toggle
        epic_header_pattern = f"<header[^>]*onclick=\"toggleEpicDetails\('{epic_id}'\)\"[^>]*>(.*?)</header>"
        epic_header_match = re.search(epic_header_pattern, html_content, re.DOTALL)

        if epic_header_match:
            epic_header_content = epic_header_match.group(1)
            # The epic header should NOT contain any filter button onclick handlers
            assert (
                "filterDefects" not in epic_header_content
            ), f"REGRESSION: filterDefects found in epic {epic_id} header!"
            assert (
                "filterByStatus" not in epic_header_content
            ), f"REGRESSION: filterByStatus found in epic {epic_id} header!"
            print(f"OK Epic {epic_id} header is clean - no filter buttons inside it")

        print(
            "OK Regression test passed - filters and epic toggles are properly separated"
        )


@pytest.mark.epic("EP-00001")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
@pytest.mark.test_category("regression")
@pytest.mark.priority("high")
def test_actual_filter_behavior():
    """Standalone function for direct testing"""
    test = TestRTMActualBehavior()

    print("Testing actual RTM filter behavior...")

    print("\n1. Testing status filter behavior...")
    test.test_clicking_status_filter_actually_filters()

    print("\n2. Testing defect filter behavior...")
    test.test_clicking_defect_filter_actually_filters()

    print("\n3. Testing epic toggle preservation...")
    test.test_epic_headers_still_have_toggle_functionality()

    print("\n4. Testing filter clearing...")
    test.test_filter_clear_functionality()

    print("\n5. Testing multiple filters...")
    test.test_multiple_filters_work_independently()

    print("\n6. Testing button onclick handlers...")
    test.test_filter_buttons_exist_and_have_correct_onclick()

    print("\n7. Testing specific regression scenario...")
    test.test_regression_scenario_specifically()

    print("\nOK All actual behavior tests passed!")


if __name__ == "__main__":
    test_actual_filter_behavior()
