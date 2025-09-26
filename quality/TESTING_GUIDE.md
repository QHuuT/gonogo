# 🧪 Comprehensive Testing Guide

**Complete guide to testing workflows, commands, and RTM integration for the gonogo project.**

## 🎯 Quick Start - Essential Commands

### **Daily Development Testing**
```bash
# Quick unit tests (most frequent) - Automatic logging with failure tagging
pytest tests/unit/ -v
# Creates: quality/logs/pytest_unit_output_TIMESTAMP.log
# Creates: quality/logs/processed_pytest_unit_output_TIMESTAMP.log (with [FAILED TEST NO-X] tags)

# Unit tests with defect tracking
python tools/test-db-integration.py run tests --auto-defects --test-type unit

# Full integration test suite
python tools/test-db-integration.py run tests --sync-tests --link-scenarios --auto-defects
```

### **🛑 Kill Zombie Server Processes (Quick Fix)**
```bash
# Windows - Kill by port (most common)
netstat -ano | findstr :8000
taskkill /F /PID <PID_NUMBER>

# Windows - Nuclear option (kill all uvicorn)
wmic process where "name='python.exe' and commandline like '%uvicorn%'" delete

# Powershell 
Get-Process python* | Stop-Process -Force

# Verify port is free
netstat -ano | findstr :8000
```

### **First Time Setup**
```bash
# 1. Install dependencies
pip install -e ".[dev]" && pip install jinja2

# 2. Setup RTM database with test discovery
python tools/test-db-integration.py discover tests
python tools/test-db-integration.py discover scenarios

# 3. Run full test suite
python tools/test-db-integration.py run tests --sync-tests --auto-defects
```

### **🔌 Server Management**

#### **Start RTM Server**
```bash
# Start RTM server for reports and API
python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8000

# Access RTM reports at:
# http://localhost:8000/api/rtm/reports/matrix?format=html
```

#### **🛑 Kill Server (Prevent Zombie Processes)**
```bash
# Method 1: Find and kill by port (Windows)
netstat -ano | findstr :8000
taskkill /F /PID <PID_NUMBER>

# Method 2: Kill all Python uvicorn processes (Windows)
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*"

# Method 3: Kill by process name pattern (Windows)
wmic process where "name='python.exe' and commandline like '%uvicorn%'" delete

# Method 4: PowerShell approach (Windows)
Get-Process python | Where-Object {$_.CommandLine -like "*uvicorn*"} | Stop-Process -Force

# Linux/macOS alternative:
# pkill -f uvicorn
# lsof -ti:8000 | xargs kill -9
```

#### **🔍 Check for Running Servers**
```bash
# Check what's running on port 8000 (Windows)
netstat -ano | findstr :8000

# Check all Python processes (Windows)
tasklist | findstr python.exe

# Check uvicorn processes specifically (Windows)
wmic process where "name='python.exe' and commandline like '%uvicorn%'" get processid,commandline
```

#### **⚠️ Zombie Process Prevention**
- **Always use Ctrl+C** to stop uvicorn server gracefully
- **Check ports before starting** new servers to avoid conflicts
- **Kill properly** when processes get stuck to prevent resource conflicts

## 📋 **Testing Workflows by Activity**

### 🔄 **1. Daily Development Cycle**

#### **Quick Testing by Type (Automatic Logging)**

**Note:** All pytest commands now automatically:
- Save output to `quality/logs/pytest_TYPE_output_TIMESTAMP.log`
- Create processed log with failures first: `processed_pytest_TYPE_output_TIMESTAMP.log`
- Display clean output on screen

```bash
# Fast unit tests - development feedback (automatically logged)
python -m pytest tests/unit/ -v
pytest tests/unit/test_specific_file.py -v
pytest tests/unit/test_specific_file.py::test_specific_function -v

# Integration tests - service interactions (automatically logged)
python -m pytest tests/integration/ -v

# Security tests - GDPR, auth, validation (automatically logged)
python -m pytest tests/security/ -v

# E2E tests - full user workflows (automatically logged)
python -m pytest tests/e2e/ -v
```

**📊 Automatic Logging & Failure Tagging System:**
All pytest commands automatically create structured logs with failure tagging:
```bash
# Every pytest run automatically creates TWO log files:
# 1. Raw log: quality/logs/pytest_TYPE_output_TIMESTAMP.log
# 2. Processed log: quality/logs/processed_pytest_TYPE_output_TIMESTAMP.log

# Examples:
pytest tests/unit/ -v       # → pytest_unit_output_20250926_183348.log
pytest tests/integration/ -v # → pytest_integration_output_20250926_183348.log
pytest tests/security/ -v   # → pytest_security_output_20250926_183348.log

# Quick failure navigation:
grep "FAILED TEST NO-" quality/logs/processed_*.log  # Find all tagged failures
head -50 quality/logs/processed_*.log               # View failure summary
```

### **🏷️ Failure Tagging System**

When tests fail, the system automatically creates numbered tags for easy navigation:

**Processed Log Structure:**
```bash
# Summary section with numbered failures:
[FAILED TEST NO-1] tests/unit/backend/tools/test_rtm_db_cli.py::TestRTMDatabaseCLI::test_query_epics_json_format
[FAILED TEST NO-2] tests/unit/backend/tools/test_rtm_db_cli.py::TestRTMDatabaseCLI::test_epic_progress_not_found

# Detailed sections with matching tags:
================================================================================
[FAILED TEST NO-1] TestRTMDatabaseCLI.test_query_epics_json_format
================================================================================
# ... detailed stack trace ...

================================================================================
[FAILED TEST NO-2] TestRTMDatabaseCLI.test_epic_progress_not_found
================================================================================
# ... detailed stack trace ...
```

**Quick Navigation Commands:**
```bash
# Find specific failure
grep "FAILED TEST NO-1" quality/logs/processed_*.log

# List all failures
grep "FAILED TEST NO-" quality/logs/processed_*.log

# View failure summary (first 50 lines show overview)
head -50 quality/logs/processed_*.log

# Reference specific failures in discussions
# Example: "See [FAILED TEST NO-3] for the authentication issue"
```

#### **Testing by Codebase Components (No RTM Integration)**
```bash
# Backend API Layer
pytest tests/unit/api/ -v                          # API routes and endpoints
pytest tests/unit/api/test_blog_routes.py -v       # Blog API endpoints
pytest tests/unit/api/test_comment_routes.py -v    # Comment API endpoints
pytest tests/unit/api/test_rtm_routes.py -v        # RTM API endpoints

# Backend Models Layer
pytest tests/unit/models/ -v                       # All database models
pytest tests/unit/models/test_blog_model.py -v     # Blog post models
pytest tests/unit/models/test_comment_model.py -v  # Comment models
pytest tests/unit/models/test_user_model.py -v     # User models
pytest tests/unit/models/traceability/ -v          # RTM models (Epic, UserStory, Test, Defect)

# Backend Services Layer
pytest tests/unit/services/ -v                     # Business logic services
pytest tests/unit/services/test_blog_service.py -v # Blog post service
pytest tests/unit/services/test_comment_service.py -v # Comment service
pytest tests/unit/services/test_rtm_service.py -v  # RTM report service
pytest tests/unit/services/test_email_service.py -v # Email notifications

# Security & GDPR
pytest tests/unit/security/ -v                     # Security implementations
pytest tests/unit/security/test_gdpr_service.py -v # GDPR compliance
pytest tests/unit/security/test_auth_service.py -v # Authentication
pytest tests/unit/security/test_input_validation.py -v # Input sanitization

# Shared Utilities
pytest tests/unit/shared/ -v                       # Shared utilities
pytest tests/unit/shared/test_utils.py -v          # Common functions
pytest tests/unit/shared/test_types.py -v          # Type definitions
pytest tests/unit/shared/testing/ -v               # Testing utilities

# Frontend Templates
pytest tests/unit/templates/ -v                    # Jinja2 template tests
pytest tests/unit/templates/test_blog_templates.py -v # Blog templates
pytest tests/unit/templates/test_layout_templates.py -v # Layout templates

# Configuration & Database
pytest tests/unit/config/ -v                       # Configuration tests
pytest tests/unit/database/ -v                     # Database connection tests
pytest tests/unit/migrations/ -v                   # Database migration tests
```

#### **Unit Testing with Bug Tracking**
```bash
# Unit tests + auto-create defects for failures
python tools/test-db-integration.py run tests --auto-defects --test-type unit

# Focus on specific areas with defect tracking
python tools/test-db-integration.py run tests --sync-tests --auto-defects --test-type unit

# Note: Direct pytest --auto-defects flags require plugin setup
# Use the CLI tool above for reliable RTM integration with defect creation
```

#### **⚠️ Update Test Execution WITHOUT Creating Defects**
```bash
# Use when you have many expected failures and don't want spam defects
# Updates test execution status/timestamps but skips auto-defect creation

# Update unit test execution status only
python tools/test-db-integration.py run tests --sync-tests --test-type unit

# Update integration test execution status only
python tools/test-db-integration.py run tests --sync-tests --test-type integration

# Update security test execution status only
python tools/test-db-integration.py run tests --sync-tests --test-type security

# Update e2e test execution status only
python tools/test-db-integration.py run tests --sync-tests --test-type e2e

# Update full test suite execution status only
python tools/test-db-integration.py run tests --sync-tests --link-scenarios

# Note: Direct pytest flags (--sync-tests) require plugin setup and may not work
# Use the CLI tool above for reliable RTM integration

# When to use:
# - After major refactoring (many expected failures)
# - When testing experimental features
# - During initial test development
# - When you want execution tracking but not defect spam
```

### 🏗️ **2. Feature Development Workflow**

#### **Before Starting Feature Work**
```bash
# Sync any new tests to RTM database
pytest --sync-tests --link-scenarios --collect-only
```

#### **During Feature Development**
```bash
# Test your feature area frequently
pytest --auto-defects tests/unit/models/test_your_feature.py -v

# Test related integration points
pytest --auto-defects tests/integration/test_feature_integration.py -v
```

#### **Before Committing Feature**
```bash
# Full test suite with complete RTM integration
pytest --sync-tests --link-scenarios --auto-defects tests/ -v

# Check for any auto-created defects
python tools/rtm-db.py query defects --format table
```

### 🚀 **3. Pre-Commit Quality Gates**

#### **Complete Quality Check**
```bash
# 1. Full test suite with RTM integration
pytest --sync-tests --link-scenarios --auto-defects tests/ -v

# 2. Code quality checks
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/

# 3. Generate test report
python tools/report_generator.py --input quality/logs/test_execution.log

# 4. Check RTM status
python tools/rtm_report_generator.py --html
```

### 🐛 **4. Bug Investigation Workflow**

#### **Reproduce and Track Bug**
```bash
# Run specific failing test with defect creation
pytest --auto-defects tests/unit/test_failing_area.py::test_specific_bug -v

# Run broader test suite to find related issues
pytest --auto-defects tests/integration/test_related_area.py -v
```

#### **After Bug Fix**
```bash
# Verify fix with full integration
pytest --sync-tests --auto-defects tests/unit/test_fixed_area.py -v

# Run regression tests
pytest --auto-defects tests/ -k "test_related_functionality" -v
```

### 🔄 **5. CI/CD and Release Testing**

#### **Pre-Release Test Suite**
```bash
# Complete test suite with full RTM integration
pytest --sync-tests --link-scenarios --auto-defects tests/ -v

# Generate comprehensive reports
python tools/report_generator.py --input quality/logs/test_execution.log
python tools/rtm_report_generator.py --html

# Create GitHub issues from any test failure defects
python tools/github_issue_creation_demo.py --dry-run
python tools/github_issue_creation_demo.py
```

## 🎛️ **Test Types and Commands**

### **By Test Type**

| Test Type | Command | Use Case |
|-----------|---------|----------|
| **Unit** | `pytest --auto-defects tests/unit/ -v` | Fast feedback, development |
| **Integration** | `pytest --auto-defects tests/integration/ -v` | Service integration testing |
| **E2E** | `pytest --auto-defects tests/e2e/ -v` | End-to-end user flows |
| **Security** | `pytest --auto-defects tests/security/ -v` | Security and GDPR compliance |
| **BDD** | `pytest --link-scenarios --auto-defects tests/bdd/ -v` | Behavior-driven scenarios |


### **By Test Scope**

| Scope | Command | When to Use |
|-------|---------|-------------|
| **Single Test** | `pytest tests/unit/test_file.py::test_function -v` | Debugging specific issue |
| **Test File** | `pytest --auto-defects tests/unit/test_file.py -v` | Testing specific module |
| **Test Directory** | `pytest --auto-defects tests/unit/models/ -v` | Testing component area |
| **Full Suite** | `pytest --sync-tests --link-scenarios --auto-defects tests/ -v` | Complete validation |

## 🏷️ **Test Tagging with Pytest Markers**

### **Class-Level vs Method-Level Markers**

**Understanding Marker Inheritance:**
- **Class-level markers** apply to ALL test methods in the class (like defaults)
- **Method-level markers** apply to specific test methods (and can override class markers)

#### **Best Practice: Which Markers Go Where?**

| Marker | Recommended Level | Reason |
|--------|------------------|--------|
| `@pytest.mark.epic()` | **Class-level** | All tests in a class usually belong to same epic |
| `@pytest.mark.user_story()` | **Class-level** | All tests in a class usually test same user story |
| `@pytest.mark.test_type()` | **Class-level** | All tests in a class are same type (unit/integration/etc) |
| `@pytest.mark.component()` | **Class-level** | All tests in a class usually test same component |
| `@pytest.mark.priority()` | **Method-level** | Each test has different priority |
| `@pytest.mark.test_category()` | **Method-level** | Each test has different category (smoke/edge/etc) |

### **All Markers for RTM Database Linkage**

#### **Python Tests - Class-Level Markers (Apply to ALL methods)**
```python
import pytest

@pytest.mark.epic("EP-XXXXX")              # Epic linkage (required) - CLASS LEVEL
@pytest.mark.user_story("US-XXXXX")        # User Story linkage (required) - CLASS LEVEL
@pytest.mark.test_type("unit")             # Test type - CLASS LEVEL
@pytest.mark.component("backend")          # Component - CLASS LEVEL
class TestFeature:
    """All methods inherit epic, user_story, test_type, and component"""

    @pytest.mark.priority("critical")           # METHOD LEVEL - specific to this test
    @pytest.mark.test_category("smoke")         # METHOD LEVEL - specific to this test
    def test_critical_functionality(self):
        assert True

    @pytest.mark.priority("low")                # METHOD LEVEL - different priority
    @pytest.mark.test_category("edge")          # METHOD LEVEL - different category
    def test_edge_case(self):
        assert True
```

#### **Python Tests - When to Override at Method Level**
```python
@pytest.mark.component("backend")          # Default: backend
class TestAPI:

    def test_backend_logic(self):
        # Uses class marker: component="backend"
        assert True

    @pytest.mark.component("frontend")     # Override: this test is frontend
    def test_frontend_integration(self):
        # Overrides class marker for this specific test
        assert True
```

#### **BDD Tests - Complete Tag Set**
```gherkin
# Feature-level tags (apply to ALL scenarios in the feature)
@epic:EP-XXXXX @user_story:US-XXXXX @component:backend @test_type:bdd
Feature: Feature Name

  # Scenario-level tags (apply to THIS scenario only)
  @priority:high @test_category:smoke
  Scenario: Critical smoke test scenario
    Given a precondition
    When an action occurs
    Then a result is expected

  # Edge case scenario
  @priority:low @test_category:edge
  Scenario: Edge case scenario
    Given an edge case condition
    When an unusual action occurs
    Then the system handles it gracefully

  # RGAA compliance scenario
  @priority:high @test_category:compliance-rgaa
  Scenario: Keyboard navigation works
    Given a user with keyboard-only access
    When they navigate the interface
    Then all features are keyboard accessible

  # GDPR compliance scenario
  @priority:critical @test_category:compliance-gdpr
  Scenario: User can delete personal data
    Given a user with personal data stored
    When they request data deletion
    Then all personal data is removed

  # Project management compliance scenario
  @priority:high @test_category:compliance-project-management
  Scenario: Epic template enforces required fields
    Given a user creating a new epic
    When they use the epic template
    Then all required fields are enforced

  # Error handling scenario
  @priority:medium @test_category:error-handling
  Scenario: System handles invalid input gracefully
    Given a user submits invalid data
    When the system processes the request
    Then an appropriate error message is displayed
    And the system remains stable
```

**Feature-level vs Scenario-level Tags:**
- **Feature-level** (before `Feature:`): epic, user_story, component, test_type → applies to ALL scenarios
- **Scenario-level** (before `Scenario:`): priority, test_category → applies to SPECIFIC scenario only

### **Practical Examples**

#### **Example 1: Integration Test Class**
```python
# Class-level: Shared by all 5 methods
@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00005")
@pytest.mark.test_type("integration")
@pytest.mark.component("backend")
class TestComponentAPI:
    """All 5 test methods inherit the 4 class markers"""

    @pytest.mark.priority("high")
    @pytest.mark.test_category("smoke")
    def test_list_components(self):
        # Has: EP-00005, US-00005, integration, backend, high, smoke
        pass

    @pytest.mark.priority("medium")
    @pytest.mark.test_category("regression")
    def test_component_statistics(self):
        # Has: EP-00005, US-00005, integration, backend, medium, regression
        pass

    @pytest.mark.priority("low")
    @pytest.mark.test_category("edge")
    def test_nonexistent_component(self):
        # Has: EP-00005, US-00005, integration, backend, low, edge
        pass
```

#### **Example 2: Unit Test Class**
```python
# Class-level: Shared markers
@pytest.mark.epic("EP-00001")
@pytest.mark.user_story("US-00010")
@pytest.mark.test_type("unit")
@pytest.mark.component("backend")
class TestUserAuthentication:

    @pytest.mark.priority("critical")
    @pytest.mark.test_category("smoke")
    def test_valid_login(self):
        pass

    @pytest.mark.priority("high")
    @pytest.mark.test_category("error-handling")
    def test_invalid_password(self):
        pass

    @pytest.mark.priority("critical")
    @pytest.mark.test_category("compliance-gdpr")
    def test_consent_required(self):
        pass
```

#### **Example 3: GDPR Compliance Tests**
```python
@pytest.mark.epic("EP-00003")
@pytest.mark.user_story("US-00020")
@pytest.mark.test_type("integration")
@pytest.mark.component("security")
class TestGDPRCompliance:
    """All GDPR tests in one class"""

    @pytest.mark.priority("critical")
    @pytest.mark.test_category("compliance-gdpr")
    def test_user_data_deletion(self):
        pass

    @pytest.mark.priority("critical")
    @pytest.mark.test_category("compliance-gdpr")
    def test_consent_workflow(self):
        pass

    @pytest.mark.priority("high")
    @pytest.mark.test_category("compliance-gdpr")
    def test_data_export(self):
        pass
```

### **Complete Marker Reference**

| Marker | Python Syntax | BDD Syntax | Values |
|--------|---------------|------------|--------|
| **Epic** | `@pytest.mark.epic("EP-XXXXX")` | `@epic:EP-XXXXX` | EP-00001, EP-00002, etc. |
| **User Story** | `@pytest.mark.user_story("US-XXXXX")` | `@user_story:US-XXXXX` | US-00001, US-00002, etc. |
| **Component** | `@pytest.mark.component("value")` | `@component:value` | backend, frontend, security, database |
| **Priority** | `@pytest.mark.priority("value")` | `@priority:value` | critical, high, medium, low |
| **Test Type** | `@pytest.mark.test_type("value")` | `@test_type:value` | unit, integration, functional, e2e, security, bdd |
| **Test Category** | `@pytest.mark.test_category("value")` | `@test_category:value` | smoke, edge, regression, performance, error-handling, compliance-gdpr, compliance-rgaa, compliance-doc, compliance-project-management |

**Note**: Epic and User Story markers are required for RTM database traceability. Component, priority, test_type, and test_category are optional but recommended.

### **Quick Reference: Marker Placement**

```python
# RECOMMENDED: Class-level for shared properties
@pytest.mark.epic("EP-XXXXX")           # CLASS: Same epic for all tests
@pytest.mark.user_story("US-XXXXX")     # CLASS: Same user story
@pytest.mark.test_type("integration")   # CLASS: All are integration tests
@pytest.mark.component("backend")       # CLASS: All test backend
class TestSuite:

    # Method-level for specific properties
    @pytest.mark.priority("critical")        # METHOD: This test is critical
    @pytest.mark.test_category("smoke")      # METHOD: This is a smoke test
    def test_critical_feature(self):
        pass

    @pytest.mark.priority("low")             # METHOD: This test is low priority
    @pytest.mark.test_category("edge")       # METHOD: This is an edge case
    def test_edge_case(self):
        pass

# AVOID: Repeating same markers on every method
class TestSuite:
    @pytest.mark.epic("EP-XXXXX")           # Repetitive
    @pytest.mark.user_story("US-XXXXX")     # Repetitive
    @pytest.mark.test_type("integration")   # Repetitive
    @pytest.mark.component("backend")       # Repetitive
    @pytest.mark.priority("high")
    @pytest.mark.test_category("smoke")
    def test_one(self):
        pass

    @pytest.mark.epic("EP-XXXXX")           # Repetitive
    @pytest.mark.user_story("US-XXXXX")     # Repetitive
    @pytest.mark.test_type("integration")   # Repetitive
    @pytest.mark.component("backend")       # Repetitive
    @pytest.mark.priority("low")
    @pytest.mark.test_category("edge")
    def test_two(self):
        pass
```

### **Examples from Codebase**

```python
# From tests/unit/test_rtm.py
@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00060")
def test_rtm_filter_by_epic():
    assert filter_tests_by_epic("EP-00005") is not None

# Multiple tests for same epic
@pytest.mark.epic("EP-00001")
@pytest.mark.user_story("US-00010")
def test_blog_post_creation():
    assert create_blog_post("title", "content") is not None

@pytest.mark.epic("EP-00001")
@pytest.mark.user_story("US-00011")
def test_blog_post_editing():
    assert edit_blog_post(1, "new content") == True
```

### **Marker Discovery**

After tagging tests, sync them to the RTM database:

```bash
# Discover and sync test markers to database
pytest --sync-tests --collect-only

# Or use the test-db integration tool
python tools/test-db-integration.py discover tests
```

The markers will appear in the RTM dashboard and link tests to requirements automatically.

## 🏷️ **Flag Reference Guide**

### **RTM Integration Flags**

| Flag | Purpose | When to Use |
|------|---------|-------------|
| `--sync-tests` | Discover and sync test definitions to RTM database | First run, after adding new tests |
| `--link-scenarios` | Link BDD scenarios to User Stories | When using BDD tests with US references |
| `--auto-defects` | Auto-create defect records for test failures | Always (recommended for tracking) |

### **Standard Pytest Flags**

| Flag | Purpose | Example |
|------|---------|---------|
| `-v` | Verbose output | `pytest -v tests/` |
| `-s` | Show print statements | `pytest -s tests/unit/test_debug.py` |
| `-k` | Run tests matching pattern | `pytest -k "test_login" tests/` |
| `--tb=short` | Short traceback format | `pytest --tb=short tests/` |
| `--maxfail=1` | Stop after first failure | `pytest --maxfail=1 tests/` |

## 📁 **Test Output Storage & Location Guide**

### **📊 Where Test Outputs Are Stored**

#### **Test Execution Logs**
```bash
# Structured test logs (JSON format)
quality/logs/test_execution.log         # Main test execution log
quality/logs/test_failures.db          # Failure tracking database
quality/logs/test_*.log                # Additional test logs

# Check if logs are being generated
ls -la quality/logs/
cat quality/logs/test_execution.log | tail -10
```

#### **Generated Reports**
```bash
# HTML test reports
quality/reports/test_report.html             # Main test report
quality/reports/test_report_*.html           # Timestamped reports

# RTM reports
quality/reports/dynamic_rtm/rtm_matrix_complete.html  # Live RTM report
quality/reports/dynamic_rtm/rtm_matrix_demo.html      # Demo RTM report

# GitHub issue templates (from auto-defects)
quality/reports/issue_template_*.md          # Defect issue templates

# Check generated reports
ls -la quality/reports/
ls -la quality/reports/dynamic_rtm/
ls -la quality/reports/issue_template_*.md
```

#### **Database Updates**
```bash
# Test execution results stored in RTM database
src/be/database.db

# Check database content
python tools/rtm-db.py query tests --format table
python tools/rtm-db.py query defects --format table
```

### **🔍 Verify Test Outputs Are Being Generated**
```bash
# Run test with full logging
pytest --sync-tests --auto-defects tests/unit/ -v

# Check what was created
echo "=== Test Logs ==="
ls -la quality/logs/

echo "=== Generated Reports ==="
ls -la quality/reports/

echo "=== Database Updates ==="
python tools/rtm-db.py query tests --format table | head -5
```

### **📂 Complete Output Directory Structure**
```
quality/
├── logs/                          # Test execution logs
│   ├── test_execution.log         # Main structured test log (JSON)
│   ├── test_failures.db          # Failure tracking database
│   └── test_*.log                # Additional test logs
├── reports/                       # Generated HTML reports
│   ├── test_report.html          # Main test report
│   ├── test_report_*.html        # Timestamped test reports
│   ├── dynamic_rtm/              # RTM reports
│   │   ├── rtm_matrix_complete.html  # Live RTM report
│   │   └── rtm_matrix_demo.html      # Demo RTM report
│   ├── issue_template_*.md       # GitHub issue templates
│   └── templates/                # Report templates
│       └── assets/              # CSS/JS for reports
└── archives/                     # Archived test results
```

### **⚠️ Troubleshooting Missing Outputs**
```bash
# 1. Check if quality directories exist
mkdir -p quality/logs quality/reports quality/reports/dynamic_rtm

# 2. Run simple test to generate logs
pytest tests/unit/ -v

# 3. Check if logs were created
ls -la quality/logs/test_execution.log

# 4. If no logs, generate manually
python tools/generate_test_logs.py

# 5. Generate report from logs
python tools/report_generator.py --input quality/logs/test_execution.log
```

## 📊 **Reporting and Analysis Commands**

### **Test Execution Reports**
```bash
# Generate HTML test report
python tools/report_generator.py --input quality/logs/test_execution.log

# View test report
start quality/reports/test_report.html  # Windows
open quality/reports/test_report.html   # macOS
```

### **RTM Reports**
```bash
# Generate live RTM report
python tools/rtm_report_generator.py --html

# View RTM report
start quality/reports/dynamic_rtm/rtm_matrix_complete.html  # Windows
open quality/reports/dynamic_rtm/rtm_matrix_complete.html   # macOS
```

### **📝 Test Output Logging**

Save detailed test output to `quality/logs/` for later review and debugging.

#### **Automatic Logging (Recommended) - NEW SYSTEM**
```bash
# Simple commands with automatic logging and failure tagging
pytest tests/unit/shared/models/test_epic_model.py -v  # Auto-creates logs with timestamps
pytest tests/unit/ -v                                  # Auto-creates logs with timestamps
pytest -k "cache" -v                                  # Auto-creates logs with timestamps

# All commands automatically create:
# 1. quality/logs/pytest_TYPE_output_TIMESTAMP.log (raw log)
# 2. quality/logs/processed_pytest_TYPE_output_TIMESTAMP.log (with [FAILED TEST NO-X] tags)
```

#### **Manual Logging (Legacy - Only if Needed)**
```bash
# Only use if you need custom file names
python -m pytest tests/unit/shared/models/test_epic_model.py -v 2>&1 | tee quality/logs/test_output_$(date +%Y%m%d_%H%M%S).log
python -m pytest tests/unit/ -v 2>&1 | tee quality/logs/all_unit_tests_$(date +%Y%m%d_%H%M%S).log
python -m pytest -k "cache" -v 2>&1 | tee quality/logs/cache_tests_$(date +%Y%m%d_%H%M%S).log
```

#### **Only Save to File (Silent)**
```bash
# Save to file without screen output
python -m pytest tests/unit/shared/models/test_epic_model.py -v > quality/logs/test_output_$(date +%Y%m%d_%H%M%S).log 2>&1
```

#### **Windows-Compatible (if date command doesn't work)**
```bash
# Fixed filename approach
python -m pytest tests/unit/shared/models/test_epic_model.py -v 2>&1 | tee quality/logs/test_output_20250926.log
```

#### **View Saved Test Logs**
```bash
# View complete log file
cat quality/logs/test_output_20250926.log

# View only test results (PASSED/FAILED)
grep -A 10 -B 5 "PASSED\|FAILED" quality/logs/test_output_20250926.log

# List all test log files
ls -la quality/logs/test_*.log

# View latest test log
ls -t quality/logs/test_*.log | head -1 | xargs cat
```

#### **📋 Post-Process Logs (Put Failures First)**

**Process any test log to show failures and stack traces at the top:**
```bash
# Process a specific log file
python tools/process_test_logs.py quality/logs/unit_tests_20250926.log

# Process with custom output name
python tools/process_test_logs.py quality/logs/unit_tests_20250926.log --output quality/logs/failures_first.log

# Process the latest test log automatically
python tools/process_test_logs.py $(ls -t quality/logs/test_*.log | head -1)
```

**What the post-processor does:**
- **Extracts all failed tests** and lists them at the top
- **Includes complete stack traces** for each failure
- **Provides failure summary** with count and test names
- **Preserves original log** at the bottom for complete reference
- **Creates timestamped processed file** (e.g., `processed_unit_tests_20250926.log`)

**Quick failure review:**
```bash
# View just the failure summary (first 50 lines)
head -50 quality/logs/processed_unit_tests_20250926.log

# View all failures and their stack traces
head -200 quality/logs/processed_unit_tests_20250926.log
```

**View automatically processed logs:**
```bash
# View latest processed unit test log (failures first)
head -50 $(ls -t quality/logs/processed_pytest_unit_output_*.log | head -1)

# View latest processed security test log
head -50 $(ls -t quality/logs/processed_pytest_security_output_*.log | head -1)

# List all processed logs (these are created automatically)
ls -la quality/logs/processed_pytest_*_output_*.log

# List raw logs (these are also created automatically)
ls -la quality/logs/pytest_*_output_*.log

# Manual processing (usually not needed since it's automatic)
python tools/process_test_logs.py quality/logs/pytest_unit_output_TIMESTAMP.log
```

#### **What's Included in Test Logs**
- Test discovery and collection details
- Individual test results (PASSED/FAILED/SKIPPED)
- Complete coverage reports
- All warnings and deprecation notices
- Full stack traces for failures
- Performance and timing information
- Database migration outputs
- Plugin and configuration details

### **Database Queries**
```bash
# View test execution status
python tools/rtm-db.py query tests --format table

# View auto-created defects
python tools/rtm-db.py query defects --format table

# View epic progress
python tools/rtm-db.py query epics --format table
```

## 🗄️ **Database Exploration**

For comprehensive database exploration including SQLite access, schema analysis, and advanced queries, see:

**📖 [Database Exploration Guide](DATABASE_GUIDE.md)**

### **Quick Database Access**
```bash
# GUI exploration (recommended)
# 1. Install DB Browser for SQLite: https://sqlitebrowser.org/
# 2. Open: gonogo.db (main RTM database)

# Command line access
sqlite3 gonogo.db                       # Main RTM database
sqlite3 quality/logs/test_failures.db   # Test failure tracking

# Project tools
python tools/db_inspector.py            # Overview of all databases
python tools/rtm-db.py admin health-check  # RTM database status
```

### **Key Database Locations**
- **gonogo.db** - Main RTM database (epics, user stories, tests, defects)
- **quality/logs/test_failures.db** - Test failure tracking and analysis
- **quality/logs/demo_test_failures.db** - Demo test failure data
- **quality/archives/archive_metadata.db** - Archive management metadata

## 🐛 **Defect Management Workflow**

### **1. Auto-Defect Creation**
```bash
# Run tests with auto-defect creation
pytest --auto-defects tests/ -v
# Output: 🐛 Created defect DEF-00023 for failed test: tests/unit/test_login.py::test_invalid_password
```

### **2. Review Created Defects**
```bash
# View all defects
python tools/rtm-db.py query defects --format table

# Check defects needing GitHub issues (placeholder numbers 900001+)
python -c "
from be.database import get_db_session
from be.models.traceability import Defect
db = get_db_session()
placeholders = db.query(Defect).filter(Defect.github_issue_number >= 900000).all()
print(f'Defects needing GitHub issues: {len(placeholders)}')
for d in placeholders:
    print(f'  {d.defect_id}: {d.title}')
"
```

### **3. Create GitHub Issues**
```bash
# Preview GitHub issues to be created
python tools/github_issue_creation_demo.py --dry-run

# Create actual GitHub issues
python tools/github_issue_creation_demo.py
```

## 🔧 **Troubleshooting Commands**

### **Common Issues and Solutions**

#### **Missing Dependencies**
```bash
# Install all required dependencies
pip install -e ".[dev]" && pip install jinja2

# Verify installation
python -c "import pytest, uvicorn, fastapi, sqlalchemy, jinja2; print('All dependencies installed')"
```

#### **Server Port Conflicts / Zombie Processes**
```bash
# Problem: "Address already in use" error when starting server
# Solution: Kill existing processes on port 8000

# Quick fix - kill by port (Windows)
netstat -ano | findstr :8000
taskkill /F /PID <PID_FROM_OUTPUT>

# Nuclear option - kill all uvicorn processes (Windows)
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*"
wmic process where "name='python.exe' and commandline like '%uvicorn%'" delete

# Verify port is free
netstat -ano | findstr :8000
# Should return empty if port is free

# Then restart server
python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8000
```

#### **Database Issues**
```bash
# Check database health
python tools/rtm-db.py admin health-check

# Reset database if corrupted
python tools/rtm-db.py admin reset --confirm

# Re-populate with sample data
python tools/populate_rtm_sample_data.py
```

#### **No Test Logs Generated**
```bash
# Ensure pytest runs generate logs
pytest tests/unit/test_simple.py -v

# Check log directory
ls -la quality/logs/

# Generate report manually
python tools/report_generator.py --demo
```

#### **RTM Reports Empty**
```bash
# Sync tests to database first
pytest --sync-tests --collect-only

# Check database content
python tools/rtm-db.py query tests --format table
python tools/rtm-db.py query epics --format table

# Generate RTM report
python tools/rtm_report_generator.py --html
```

## 🎯 **Recommended Daily Workflows**

### **👨‍💻 Developer Workflow**

**📋 Screen Output Only (Quick Feedback):**
```bash
# 1. Start of day - quick health check (screen only)
pytest tests/unit/ -v

# 2. During development - frequent unit testing (screen only)
pytest --auto-defects tests/unit/your_module/ -v

# 3. Before committing - integration check (screen only)
pytest --auto-defects tests/integration/ -v

# 4. Before push - full suite (screen only)
pytest --sync-tests --link-scenarios --auto-defects tests/ -v
```

**💾 With Saved Output (Documentation & Debugging):**
```bash
# 1. Start of day - health check with log
python -m pytest tests/unit/ -v 2>&1 | tee quality/logs/daily_health_check_$(date +%Y%m%d_%H%M%S).log

# 2. Before committing - save integration results
python -m pytest --auto-defects tests/integration/ -v 2>&1 | tee quality/logs/pre_commit_$(date +%Y%m%d_%H%M%S).log

# 3. Before push - full suite with complete log
python -m pytest --sync-tests --link-scenarios --auto-defects tests/ -v 2>&1 | tee quality/logs/full_suite_$(date +%Y%m%d_%H%M%S).log
```

### **🔍 QA Testing Workflow**
```bash
# 1. Full test suite with defect tracking
pytest --sync-tests --link-scenarios --auto-defects tests/ -v

# 2. Generate test report
python tools/report_generator.py --input quality/logs/test_execution.log

# 3. Generate RTM report
python tools/rtm_report_generator.py --html

# 4. Create GitHub issues for failures
python tools/github_issue_creation_demo.py

# 5. Review reports
start quality/reports/test_report.html
start quality/reports/dynamic_rtm/rtm_matrix_complete.html
```

### **🚀 Release Testing Workflow**
```bash
# 1. Complete test suite with full integration
pytest --sync-tests --link-scenarios --auto-defects tests/ -v

# 2. Code quality gates
black src/ tests/ && isort src/ tests/ && flake8 src/ tests/ && mypy src/

# 3. Generate all reports
python tools/report_generator.py --input quality/logs/test_execution.log
python tools/rtm_report_generator.py --html

# 4. Archive test results
python tools/archive_cleanup.py --bundle release-$(date +%Y%m%d) --patterns "reports/*.html,logs/*.log"

# 5. Create GitHub issues for any failures
python tools/github_issue_creation_demo.py
```

## 📚 **Additional Resources**

- **[Quality Reports Guide](README.md)** - Complete reporting system overview
- **[RTM Guide](RTM_GUIDE.md)** - Requirements traceability matrix details
- **[Quick Reference](QUICK_REFERENCE.md)** - Common commands and thresholds
- **[Development Workflow](../docs/technical/development-workflow.md)** - Complete project configuration and commands

---

## 🎯 **TL;DR - Most Important Commands**

### **Quick Testing (Screen Output Only)**
```bash
# Daily development - quick feedback
pytest --auto-defects tests/unit/ -v

# Before committing - verify functionality
pytest --sync-tests --link-scenarios --auto-defects tests/ -v
```

### **Testing with Saved Logs (Recommended for Documentation)**
```bash
# Daily development with logs
python -m pytest --auto-defects tests/unit/ -v 2>&1 | tee quality/logs/daily_$(date +%Y%m%d_%H%M%S).log

# Before committing with full logs
python -m pytest --sync-tests --link-scenarios --auto-defects tests/ -v 2>&1 | tee quality/logs/commit_$(date +%Y%m%d_%H%M%S).log

# For Windows (if date doesn't work)
python -m pytest tests/unit/ -v 2>&1 | tee quality/logs/test_output_$(date +%Y%m%d).log
```

### **Quality Reports & Analysis**
```bash
# Generate reports from logs
python tools/report_generator.py --input quality/logs/test_execution.log
python tools/rtm_report_generator.py --html

# View saved test logs
ls -la quality/logs/test_*.log
cat quality/logs/daily_20250926_*.log

# Defect management
python tools/github_issue_creation_demo.py --dry-run
python tools/github_issue_creation_demo.py

# Debug analysis and regression prevention
# See quality/debug_reports/ for detailed debugging documentation
# Format: quality/debug_reports/YYYYMMDD-issue-description.md
```

**🎉 Use this guide as your single source of truth for all testing activities!**

For detailed debugging analysis and regression prevention, see [Debug Reports](debug_reports/) documentation.