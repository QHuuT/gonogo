# 🧪 Comprehensive Testing Guide

**Complete guide to testing workflows, commands, and RTM integration for the gonogo project.**

## 🎯 Quick Start - Essential Commands

### **Daily Development Testing**
```bash
# Quick unit tests (most frequent)
pytest tests/unit/ -v

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

#### **Quick Testing by Type (No RTM Integration)**
```bash
# Fast unit tests - development feedback
pytest tests/unit/ -v
pytest tests/unit/test_specific_file.py -v
pytest tests/unit/test_specific_file.py::test_specific_function -v

# Integration tests - service interactions
pytest tests/integration/ -v

# Security tests - GDPR, auth, validation
pytest tests/security/ -v

# E2E tests - full user workflows
pytest tests/e2e/ -v
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

### **Database Queries**
```bash
# View test execution status
python tools/rtm-db.py query tests --format table

# View auto-created defects
python tools/rtm-db.py query defects --format table

# View epic progress
python tools/rtm-db.py query epics --format table
```

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
```bash
# 1. Start of day - quick health check
pytest tests/unit/ -v

# 2. During development - frequent unit testing
pytest --auto-defects tests/unit/your_module/ -v

# 3. Before committing - integration check
pytest --auto-defects tests/integration/ -v

# 4. Before push - full suite
pytest --sync-tests --link-scenarios --auto-defects tests/ -v
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
- **[CLAUDE.md](../CLAUDE.md)** - Complete project configuration and commands

---

## 🎯 **TL;DR - Most Important Commands**

```bash
# Daily development
pytest --auto-defects tests/unit/ -v

# Before committing
pytest --sync-tests --link-scenarios --auto-defects tests/ -v

# Quality reports
python tools/report_generator.py --input quality/logs/test_execution.log
python tools/rtm_report_generator.py --html

# Defect management
python tools/github_issue_creation_demo.py --dry-run
python tools/github_issue_creation_demo.py
```

**🎉 Use this guide as your single source of truth for all testing activities!**