"""
REAL browser test - actually clicks filter buttons and checks what happens
This will catch the actual regression that HTTP tests missed
"""
import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class TestRTMBrowserClicks:
    """Test RTM by actually clicking buttons in a real browser"""

    BASE_URL = "http://localhost:8000"
    RTM_URL = f"{BASE_URL}/api/rtm/reports/matrix?format=html"

    @pytest.fixture
    def driver(self):
        """Setup Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Remove this to see the browser
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)

        yield driver
        driver.quit()

    def test_click_filter_button_and_check_behavior(self, driver):
        """Click an actual filter button and see what happens"""
        print("Opening RTM interface...")
        driver.get(self.RTM_URL)

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "epic-card"))
        )

        # Check for JavaScript errors first
        browser_logs = driver.get_log('browser')
        js_errors = [log for log in browser_logs if log['level'] == 'SEVERE']
        if js_errors:
            print(f"JavaScript errors found: {js_errors}")

        print("Looking for filter buttons...")

        # Find a defect filter button (the problematic one)
        defect_buttons = driver.find_elements(By.XPATH, "//button[contains(@onclick, 'filterDefects')]")
        if not defect_buttons:
            pytest.fail("No defect filter buttons found!")

        print(f"Found {len(defect_buttons)} defect filter buttons")

        # Get original URL
        original_url = driver.current_url
        print(f"Original URL: {original_url}")

        # Find an epic toggle button to test later
        epic_headers = driver.find_elements(By.XPATH, "//header[contains(@onclick, 'toggleEpicDetails')]")
        if not epic_headers:
            pytest.fail("No epic headers found!")

        print(f"Found {len(epic_headers)} epic headers")

        # Test clicking a defect filter button
        first_defect_button = defect_buttons[0]
        button_text = first_defect_button.text
        onclick_attr = first_defect_button.get_attribute('onclick')
        print(f"Clicking defect filter button: '{button_text}' with onclick='{onclick_attr}'")

        try:
            # Click the filter button
            first_defect_button.click()

            # Wait a moment for any navigation
            time.sleep(2)

            # Check what happened
            new_url = driver.current_url
            print(f"New URL after click: {new_url}")

            # Check for JavaScript errors after click
            browser_logs_after = driver.get_log('browser')
            new_js_errors = [log for log in browser_logs_after if log['level'] == 'SEVERE' and log not in browser_logs]
            if new_js_errors:
                print(f"NEW JavaScript errors after click: {new_js_errors}")
                pytest.fail(f"JavaScript errors occurred: {new_js_errors}")

            # The URL should have changed to include filter parameters
            if new_url == original_url:
                pytest.fail("URL did not change after clicking filter button - filtering not working!")

            # Check if filter parameters are in the URL
            if 'defect_' not in new_url:
                pytest.fail("No defect filter parameters in URL after clicking defect filter button!")

            print("OK Filter button click resulted in URL change with filter parameters")

        except Exception as e:
            # Check for JavaScript errors if click failed
            browser_logs_error = driver.get_log('browser')
            js_errors_click = [log for log in browser_logs_error if log['level'] == 'SEVERE']
            if js_errors_click:
                print(f"JavaScript errors during click: {js_errors_click}")

            pytest.fail(f"Failed to click filter button: {e}")

    def test_epic_toggle_still_works_after_filter(self, driver):
        """Test that epic toggle still works independently"""
        print("Testing epic toggle functionality...")

        # Go to RTM with a filter applied
        filter_url = f"{self.RTM_URL}&defect_priority_filter=critical"
        driver.get(filter_url)

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "epic-card"))
        )

        # Find epic headers
        epic_headers = driver.find_elements(By.XPATH, "//header[contains(@onclick, 'toggleEpicDetails')]")
        if not epic_headers:
            pytest.fail("No epic headers found with filter applied!")

        print(f"Found {len(epic_headers)} epic headers with filter applied")

        # Try clicking an epic header
        first_epic = epic_headers[0]
        epic_onclick = first_epic.get_attribute('onclick')
        print(f"Clicking epic header with onclick='{epic_onclick}'")

        try:
            first_epic.click()
            time.sleep(1)

            # Check for JavaScript errors
            browser_logs = driver.get_log('browser')
            js_errors = [log for log in browser_logs if log['level'] == 'SEVERE']
            if js_errors:
                print(f"JavaScript errors during epic toggle: {js_errors}")
                pytest.fail(f"Epic toggle caused JavaScript errors: {js_errors}")

            # URL should NOT change when clicking epic header
            current_url = driver.current_url
            if 'defect_priority_filter=critical' not in current_url:
                pytest.fail("Filter was lost when clicking epic header - epic toggle broke filtering!")

            print("OK Epic toggle works without affecting filters")

        except Exception as e:
            browser_logs = driver.get_log('browser')
            js_errors = [log for log in browser_logs if log['level'] == 'SEVERE']
            if js_errors:
                print(f"JavaScript errors: {js_errors}")
            pytest.fail(f"Epic toggle failed: {e}")

    def test_javascript_console_for_errors(self, driver):
        """Check browser console for JavaScript errors"""
        print("Checking for JavaScript errors...")

        driver.get(self.RTM_URL)

        # Wait for page to load completely
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "epic-card"))
        )

        # Get all browser logs
        browser_logs = driver.get_log('browser')

        # Filter for JavaScript errors
        js_errors = [log for log in browser_logs if log['level'] == 'SEVERE']
        js_warnings = [log for log in browser_logs if log['level'] == 'WARNING']

        if js_errors:
            print(f"CRITICAL JavaScript errors found:")
            for error in js_errors:
                print(f"  - {error['message']}")
            pytest.fail(f"JavaScript errors present: {[e['message'] for e in js_errors]}")

        if js_warnings:
            print(f"JavaScript warnings found:")
            for warning in js_warnings:
                print(f"  - {warning['message']}")

        print("OK No critical JavaScript errors found")

    def test_filter_functions_are_defined(self, driver):
        """Test that JavaScript filter functions are actually defined"""
        print("Checking if JavaScript functions are defined...")

        driver.get(self.RTM_URL)

        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "epic-card"))
        )

        # Test if functions are defined
        functions_to_test = [
            'filterByStatus',
            'filterUserStoriesByStatus',
            'filterTestsByType',
            'filterDefects',
            'toggleEpicDetails'
        ]

        for func_name in functions_to_test:
            try:
                result = driver.execute_script(f"return typeof window.{func_name}")
                if result != 'function':
                    pytest.fail(f"Function {func_name} is not defined or not a function (type: {result})")
                print(f"OK {func_name} is defined as a function")
            except Exception as e:
                pytest.fail(f"Error checking function {func_name}: {e}")

    def test_actual_function_execution(self, driver):
        """Test actually calling the JavaScript functions"""
        print("Testing actual JavaScript function execution...")

        driver.get(self.RTM_URL)

        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "epic-card"))
        )

        original_url = driver.current_url

        try:
            # Test filterDefects function with 3 parameters
            print("Testing filterDefects function call...")
            result = driver.execute_script("""
                // Mock window.location.href to capture the redirect
                let redirectUrl = null;
                const originalHref = window.location.href;
                Object.defineProperty(window.location, 'href', {
                    set: function(url) { redirectUrl = url; },
                    get: function() { return originalHref; }
                });

                // Call the function
                filterDefects('EP-00001', 'priority', 'critical');

                return redirectUrl;
            """)

            if not result:
                pytest.fail("filterDefects function did not attempt to redirect")

            if 'defect_priority_filter=critical' not in result:
                pytest.fail(f"filterDefects function generated wrong URL: {result}")

            print(f"OK filterDefects function works correctly: {result}")

        except Exception as e:
            # Get browser logs to see what went wrong
            browser_logs = driver.get_log('browser')
            js_errors = [log for log in browser_logs if log['level'] == 'SEVERE']
            if js_errors:
                print(f"JavaScript errors during function execution: {js_errors}")
            pytest.fail(f"Function execution failed: {e}")


def test_browser_behavior():
    """Standalone test function"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        test = TestRTMBrowserClicks()

        print("Running browser-based RTM tests...")

        test.test_javascript_console_for_errors(driver)
        test.test_filter_functions_are_defined(driver)
        test.test_actual_function_execution(driver)
        test.test_click_filter_button_and_check_behavior(driver)
        test.test_epic_toggle_still_works_after_filter(driver)

        print("OK All browser tests passed!")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_browser_behavior()