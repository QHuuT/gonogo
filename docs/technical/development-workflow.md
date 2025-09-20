# Development Workflow

**Last Updated**: 2025-09-20

## 🎯 Overview

This document defines the complete development workflow for GoNoGo, integrating BDD practices, requirements traceability, and GDPR compliance into a systematic approach to feature development.

## 📋 Core Development Workflow

### **Phase 1: Requirements Analysis & GitHub Issue Creation**
1. **Read CLAUDE.md** for current project state and commands
2. **Check GitHub Issues** for active epics and user stories
3. **CREATE GITHUB ISSUE** using templates when planning new tasks:
   ```bash
   # For new features/epics
   gh issue create --template epic --title "EP-XXXXX: Feature Name"

   # For specific requirements
   gh issue create --template user-story --title "US-XXXXX: Specific Requirement"

   # For bug fixes
   gh issue create --template defect --title "DEF-XXXXX: Bug Description"
   ```
4. **Review Context** in `docs/context/` for background decisions and compliance
5. **Review BDD Scenarios** in `tests/bdd/features/`
6. **Check RTM Status** in `docs/traceability/requirements-matrix.md`
7. **Verify GDPR Implications** in `docs/context/compliance/gdpr-requirements.md`

### **Phase 2: Test-Driven Implementation**
8. **Write/Update BDD Step Definitions** in `tests/bdd/step_definitions/`
9. **ADD BDD SCENARIOS TO GITHUB ISSUE** in the issue description:
   ```markdown
   ## BDD Scenarios
   - Feature: authentication.feature:user_login
   - Feature: authentication.feature:user_logout
   ```
10. **Run BDD Tests** (should fail - RED phase)
    ```bash
    pytest tests/bdd/ -v --tb=short
    ```
11. **Implement Minimum Code** to make tests pass (GREEN phase)
12. **Refactor** while keeping tests green (REFACTOR phase)
13. **Run Full Test Suite** to ensure no regressions

### **Phase 3: Documentation & Traceability**
14. **UPDATE RTM** in `docs/traceability/requirements-matrix.md` with:
    - Link to GitHub issue
    - Implementation status (⏳ In Progress → ✅ Done)
    - BDD scenario references
    - Test implementation links
15. **Update Technical Docs** if architecture changed (see [Documentation Workflow](documentation-workflow.md))
16. **Verify GDPR Compliance** if personal data involved
17. **Update CLAUDE.md** if workflow or structure changed

### **Phase 4: Quality Gates (MANDATORY) - Enhanced with Structured Logging**
18. **Run Tests with Structured Logging** (generates logs automatically):
    ```bash
    # All tests with structured logging (creates quality/logs/test_execution.log)
    pytest tests/ -v

    # Enhanced execution modes
    pytest --mode=silent --type=all     # All tests, minimal output
    pytest --mode=verbose --type=unit   # Unit tests with detailed output
    pytest --mode=detailed --type=integration  # Integration with full debugging
    ```
19. **Generate Interactive Test Report** (review for failures and trends):
    ```bash
    # Generate comprehensive HTML report from test logs
    python tools/report_generator.py --input quality/logs/

    # Generate filtered reports for specific test types
    python tools/report_generator.py --type unit --input quality/logs/
    python tools/report_generator.py --type integration --input quality/logs/

    # Generate demo report for testing (creates sample data)
    python tools/report_generator.py --demo

    # Review: quality/reports/test_report.html for interactive analysis
    ```
20. **Check Test Failure Patterns** (NEW - automatic failure tracking):
    ```bash
    # Run failure tracking analysis (creates sample failure data)
    python tools/failure_tracking_demo.py

    # View comprehensive failure analysis
    # - HTML: quality/reports/failure_analysis_report.html
    # - JSON: quality/reports/failure_summary_daily.json

    # Check for flaky tests and patterns in database
    ```
21. **Verify Log-Failure Correlation** (NEW - debugging assistance):
    ```bash
    # Run log correlation analysis (creates correlation scenarios)
    python tools/log_correlation_demo.py

    # Review correlation reports
    # - JSON: quality/reports/log_correlation_report.json
    # - Reproduction scripts: quality/reports/reproduction_script_*.py
    ```
22. **Test Archive Management** (NEW - retention and cleanup):
    ```bash
    # Check archive storage metrics and recommendations
    python tools/archive_cleanup.py --metrics

    # Dry run - see what would be archived/cleaned
    python tools/archive_cleanup.py --dry-run

    # Apply retention policies (compress old files, delete very old)
    python tools/archive_cleanup.py --apply

    # Search archived test reports
    python tools/archive_cleanup.py --search "test_report" --file-type .html
    ```
23. **Run Quality Checks** (must pass before commit):
    ```bash
    black src/ tests/ && isort src/ tests/ && flake8 src/ tests/ && mypy src/
    ```
24. **Run Security Tests**: `pytest tests/security/ -v`
25. **Run GDPR Compliance Tests**: `pytest tests/security/test_gdpr_compliance.py -v`
26. **Verify Test Coverage**: `pytest --cov=src tests/ --cov-report=term-missing`
27. **Validate RTM Links** if RTM was modified:
    ```bash
    python tools/rtm-links-simple.py --validate
    ```

### **Phase 5: Integration & GitHub-First Commit**
28. **Integration Test**: `pytest tests/integration/ -v`
29. **E2E Test** (if applicable): `pytest tests/e2e/ -v`
30. **COMMIT WITH GITHUB ISSUE REFERENCE**:
    ```bash
    git commit -m "feat: implement user authentication system

    Implements US-00018: User login with GDPR consent

    - Add login/logout BDD scenarios
    - Implement authentication service
    - Add GDPR consent handling
    - Update RTM with completion status

    🤖 Generated with [Claude Code](https://claude.ai/code)

    Co-Authored-By: Claude <noreply@anthropic.com>"
    ```
31. **COMMENT ON GITHUB ISSUE** with implementation details:
    ```bash
    gh issue comment [ISSUE-NUMBER] --body "
    ## Implementation Completed ✅

    **Files Changed:**
    - \`src/be/services/auth_service.py\` - Authentication logic
    - \`tests/bdd/features/authentication.feature\` - BDD scenarios
    - \`tests/bdd/step_definitions/auth_steps.py\` - Test implementations

    **BDD Scenarios Implemented:**
    - User login with valid credentials
    - User logout functionality
    - GDPR consent validation

    **Quality Gates Passed:**
    - All tests passing ✅
    - Code quality checks passed ✅
    - GDPR compliance validated ✅
    - RTM updated ✅

    **Commit:** [commit-hash]
    "
    ```

## 🔄 BDD Scenario Development Process

### **Writing New BDD Scenarios**
1. **Use Template**: Copy from `tests/bdd/features/scenario-template.feature`
2. **Follow Gherkin Best Practices**:
   - **Given**: Set up initial context
   - **When**: Perform the action
   - **Then**: Verify expected outcome
3. **Tag Appropriately**: `@functional @gdpr @security @performance`
4. **Include GDPR Scenarios**: Always consider privacy implications
5. **Link to User Story**: Reference US-XXX in comments

### **Implementing Step Definitions**
1. **Create Step File**: `tests/bdd/step_definitions/test_[feature]_steps.py`
2. **Import Scenarios**: `scenarios("../features/[feature].feature")`
3. **Implement Steps**: Use `@given`, `@when`, `@then` decorators
4. **Use Fixtures**: Leverage `bdd_context`, `bdd_test_client`, etc.
5. **Mock External Dependencies**: Keep tests isolated

## 📊 Requirements Traceability Matrix (RTM) Updates

### **When to Update RTM**
- New user story implemented
- BDD scenario added or modified
- Code implementation completed
- Test status changed
- Defect discovered or resolved

### **RTM Update Process**
1. **Open**: `docs/traceability/requirements-matrix.md`
2. **Update Status**: Change from 📝 Planned → ⏳ In Progress → ✅ Done
3. **Link Artifacts**: Ensure all columns are filled
4. **Update Metrics**: Recalculate coverage percentages
5. **Note Dependencies**: Update any blocking items
6. **Link Defects**: Update defects column with DEF-XXX references

## 🛡️ GDPR Compliance Integration

### **For Every Feature Involving Personal Data**
1. **Check GDPR Map**: Review `docs/traceability/gdpr-compliance-map.md`
2. **Identify Legal Basis**: Consent, Legitimate Interest, etc.
3. **Implement Privacy by Design**: Minimize data collection
4. **Add GDPR BDD Scenarios**: Test consent, access, erasure
5. **Update Data Processing Records**: Document in RTM

### **GDPR Testing Checklist**
- [ ] Consent collection tested
- [ ] Data minimization verified
- [ ] Retention policies implemented
- [ ] Right to access working
- [ ] Right to erasure working
- [ ] Data export functional

## 🐛 Defect Management Workflow

### **When a Defect is Discovered**
1. **Create GitHub Issue**: Use defect template
2. **Link to Epic/User Story**: Identify related requirements
3. **Assess Business Impact**: Priority, severity, GDPR implications
4. **Update RTM**: Add defect reference to affected requirements
5. **Create Fix BDD Scenario**: Test for the fix (if needed)

### **Defect Resolution Process**
1. **Analyze Root Cause**: Document in GitHub Issue
2. **Fix Implementation**: Follow standard BDD workflow
3. **Update BDD Scenarios**: Prevent regression
4. **Verify Fix**: All acceptance criteria now pass
5. **Update RTM**: Mark defect as resolved
6. **Close GitHub Issue**: Update status and verify date

### **Defect Prevention**
- Review defect patterns monthly
- Update BDD scenarios to catch similar issues
- Improve quality gates based on defect analysis
- Update development guidelines to prevent recurrence

## 📈 Success Metrics

### **Development Quality**
- 100% User Story → BDD Scenario coverage
- 90%+ test coverage maintained
- All GDPR scenarios passing
- Zero high-severity security issues

### **Process Quality**
- RTM updated within 24h of changes
- Documentation current with code
- All commits linked to user stories
- Quality gates passing before merge

## 📊 Test Logging and Reporting System - Comprehensive User Guide

### **🎯 Overview**
The GoNoGo project features a comprehensive test logging and reporting system with structured logging, interactive HTML reports, failure tracking, log correlation, GitHub integration, and automated archiving.

### **🏗️ System Architecture**
```
quality/
├── logs/                    # Structured test execution logs
│   ├── test_execution.log   # Main test log (JSON format)
│   ├── test_failures.db    # SQLite database for failure tracking
│   └── structured_*.log    # Individual test session logs
├── reports/                 # Generated reports and analysis
│   ├── test_report.html    # Interactive test dashboard
│   ├── failure_analysis_report.html  # Failure pattern analysis
│   ├── log_correlation_report.json   # Log-failure correlations
│   ├── templates/          # Jinja2 templates for reports
│   └── issue_template_*.md # GitHub issue templates
└── archives/               # Archived test data with retention
    ├── compressed/         # Gzip-compressed old files
    ├── archive_metadata.db # Archive tracking database
    └── bundles/           # ZIP bundles for batch exports
```

### **📋 1. Enhanced Test Execution Modes**

#### **Standard Test Execution with Logging**
```bash
# Run all tests with structured logging (creates quality/logs/test_execution.log)
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v               # Unit tests only
pytest tests/integration/ -v        # Integration tests
pytest tests/security/ -v           # Security tests
pytest tests/e2e/ -v               # End-to-end tests
```

#### **Enhanced Execution Modes (NEW)**
```bash
# Silent mode - minimal output, full logging
pytest --mode=silent --type=all

# Verbose mode - detailed output for specific test types
pytest --mode=verbose --type=unit
pytest --mode=verbose --type=integration

# Detailed mode - maximum debugging information
pytest --mode=detailed --type=integration
pytest --mode=detailed tests/unit/specific_test.py -v
```

#### **Coverage Integration**
```bash
# Generate coverage report with structured logging
pytest --cov=src tests/ --cov-report=term-missing

# Coverage with HTML report
pytest --cov=src tests/ --cov-report=html:quality/reports/coverage/
```

### **📈 2. Interactive HTML Test Reports**

#### **Generate Reports from Test Logs**
```bash
# Generate comprehensive HTML report from recent logs
python tools/report_generator.py --input quality/logs/

# Generate filtered reports for specific test types
python tools/report_generator.py --type unit --input quality/logs/
python tools/report_generator.py --type integration --input quality/logs/
python tools/report_generator.py --type security --input quality/logs/

# Generate demo report with sample data (for testing)
python tools/report_generator.py --demo
```

#### **Report Features**
- **Interactive Filtering**: Filter by test status, type, and search terms
- **Timeline Visualization**: See test execution patterns over time
- **Failure Analysis**: Categorized error patterns and debugging information
- **Export Capabilities**: CSV export for external analysis
- **GDPR Compliance**: Personal data sanitization in logs and reports

#### **Viewing Reports**
```bash
# Open the generated report in your browser
open quality/reports/test_report.html  # macOS
start quality/reports/test_report.html # Windows
xdg-open quality/reports/test_report.html # Linux
```

### **🔍 3. Test Failure Tracking and Pattern Analysis**

#### **Automatic Failure Tracking**
Test failures are automatically tracked in SQLite database with:
- **11 Failure Categories**: assertion_error, import_error, unicode_error, timeout_error, etc.
- **Pattern Detection**: Identifies recurring failure patterns across test suites
- **Statistical Analysis**: Daily/weekly/monthly trends with failure rate calculations
- **Flaky Test Detection**: Automatically identifies unstable tests

#### **Generate Failure Analysis**
```bash
# Run failure tracking demo (creates sample data for demonstration)
python tools/failure_tracking_demo.py

# View comprehensive failure analysis reports
# - HTML Dashboard: quality/reports/failure_analysis_report.html
# - JSON Summary: quality/reports/failure_summary_daily.json
```

#### **Failure Database Queries**
```bash
# View failure database location
ls -la quality/logs/test_failures.db

# Example SQLite queries (if needed for analysis)
sqlite3 quality/logs/test_failures.db "SELECT category, COUNT(*) FROM failures GROUP BY category;"
```

### **🔗 4. Log-Failure Correlation and Context Preservation**

#### **Advanced Correlation System**
Links structured logs with test failures using:
- **Test ID Matching**: Direct correlation via test identifiers
- **Temporal Correlation**: Time-based association of logs and failures
- **Session Correlation**: Group related test executions
- **Context Preservation**: Environment state, test data, execution timeline

#### **Generate Correlation Analysis**
```bash
# Run log correlation demo (creates sample correlation scenarios)
python tools/log_correlation_demo.py

# View correlation reports and reproduction guides
# - JSON Report: quality/reports/log_correlation_report.json
# - Reproduction Scripts: quality/reports/reproduction_script_*.py
```

#### **Debugging Assistance Features**
- **Category-Specific Hints**: Debugging suggestions based on failure type
- **Related Failure Detection**: Find similar failures across test sessions
- **Automated Script Generation**: Reproduction guides for failure scenarios

### **🔄 5. GitHub Issue Creation Integration**

#### **Automated Issue Creation from Test Failures**
```bash
# Run GitHub issue creation demo (dry-run mode - no actual issues created)
python tools/github_issue_creation_demo.py --dry-run

# View generated templates and reports
# - Issue Templates: quality/reports/issue_template_*.md
# - Creation Reports: quality/reports/github_issue_creation_report_*.md
```

#### **Issue Creation Features**
- **Automated Template Generation**: Pre-filled titles, bodies, and context
- **Intelligent Labeling**: Auto-assignment based on failure category and test location
- **Batch Processing**: Handle multiple failures with comprehensive reporting
- **Rich Context**: Environment info, stack traces, reproduction guides

#### **Manual Issue Creation**
```bash
# Create actual GitHub issues (requires GitHub CLI authentication)
python tools/github_issue_creation_demo.py  # Remove --dry-run for real creation
```

### **📦 6. Test Report Archiving and Retention Management**

#### **Archive Storage Metrics**
```bash
# Check current archive storage and get optimization recommendations
python tools/archive_cleanup.py --metrics

# Example output:
# Current Storage:
#   Total files: 150
#   Total size: 45.2 MB
#   Compressed files: 75
#   Compression savings: 25.8 MB
# Recommendations:
#   - Consider archiving 25 files older than 30 days
#   - 12 files can be compressed to save ~8MB space
```

#### **Retention Policy Management**
```bash
# Dry run - see what would be done without making changes
python tools/archive_cleanup.py --dry-run

# Apply retention policies (compress old files, archive very old, delete ancient)
python tools/archive_cleanup.py --apply

# Apply with custom schedule for automation
python tools/archive_cleanup.py --apply --schedule "0 3 * * *"  # Daily 3 AM
```

#### **Archive Search and Retrieval**
```bash
# Search archived test reports
python tools/archive_cleanup.py --search "test_report"
python tools/archive_cleanup.py --search "failure" --file-type .html
python tools/archive_cleanup.py --search "integration" --file-type .log

# Create archive bundles for specific patterns
python tools/archive_cleanup.py --bundle backup_reports --patterns "reports/*.html" "reports/*.json"

# Restore files from archive
python tools/archive_cleanup.py --restore path/to/archived/file.gz --destination /tmp/restored/
```

#### **Automated Cleanup Configuration**
```bash
# Generate automated cleanup script and cron configuration
python tools/archive_cleanup.py --configure --schedule "0 2 * * *"

# This creates:
# - Executable script: quality/archive_cleanup.sh
# - Cron job configuration with proper paths
# - Documentation for setup
```

### **🔧 7. Debugging & Troubleshooting Guide**

#### **Test Failure Investigation Process**
1. **Check Interactive Test Report**:
   ```bash
   python tools/report_generator.py --input quality/logs/
   # Open quality/reports/test_report.html in browser for filtering and analysis
   ```

2. **Analyze Failure Patterns**:
   ```bash
   python tools/failure_tracking_demo.py
   # Review quality/reports/failure_analysis_report.html for trends
   ```

3. **Check Log Correlation**:
   ```bash
   python tools/log_correlation_demo.py
   # Review quality/reports/log_correlation_report.json for context
   ```

4. **Debug with Detailed Mode**:
   ```bash
   # Run failing tests with maximum detail and structured logging
   pytest --mode=detailed tests/unit/test_failing.py -v
   ```

5. **Verify GDPR Sanitization**:
   ```bash
   # Ensure no personal data in logs (should show [REDACTED])
   grep -i "email\|ip.*address" quality/logs/test_*.log
   ```

#### **Common Issues and Solutions**

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **No logs generated** | Empty quality/logs/ directory | Run `pytest tests/ -v` first to create logs |
| **Empty reports** | Blank HTML reports | Check for test_*.log files; verify tests actually ran |
| **Template errors** | Jinja2 template not found | Verify templates exist in `quality/reports/templates/` |
| **Missing dependencies** | Import errors in tools | Run `pip install -e ".[dev]" && pip install jinja2` |
| **Archive permission errors** | SQLite database locked (Windows) | Known Windows issue; doesn't affect functionality |
| **Report generation fails** | Tool crashes during report creation | Check log files exist and contain valid JSON |

### **⚙️ 8. Configuration Reference**

#### **Test Runner Plugin Configuration (pyproject.toml)**
```toml
[tool.pytest.ini_options]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--strict-config",
]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "security: marks tests as security tests",
    "gdpr: marks tests as GDPR compliance tests",
]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

#### **Structured Logging Configuration**
- **Log Format**: JSON with timestamp, test_id, level, message, context
- **Log Location**: `quality/logs/test_execution.log`
- **GDPR Compliance**: Automatic PII sanitization using `[REDACTED]`
- **Session Tracking**: Unique session IDs for correlation

#### **Archive Retention Policies**
Default policies by file type:
1. **HTML Reports**: Keep 30 days, compress after 7 days
2. **JSON Data**: Keep 90 days, compress after 14 days
3. **Log Files**: Keep 60 days, compress after 7 days
4. **Coverage Reports**: Keep 45 days, compress after 14 days
5. **Screenshots**: Keep 30 days, compress after 7 days
6. **Database Files**: Keep 120 days, compress after 30 days

### **📋 9. GDPR Compliance for Test Logging**

#### **Data Classification and Sanitization**
- **Personal Data Detection**: Automatic identification of emails, IPs, names
- **Sanitization Strategy**: Replace with `[REDACTED]` markers
- **Log Retention**: Respect EU data retention requirements
- **Data Subject Rights**: Provide access/export capabilities

#### **GDPR-Safe Test Data Creation**
```bash
# Ensure test data doesn't contain real personal information
# Use faker library for generating compliant test data
pytest tests/security/test_gdpr_compliance.py -v
```

### **🎯 10. Quality Gates Integration**

#### **Enhanced Pre-Commit Checklist**
```bash
# 1. Run tests with structured logging
pytest tests/ -v

# 2. Generate and review test report
python tools/report_generator.py --input quality/logs/
# Review quality/reports/test_report.html

# 3. Check failure patterns
python tools/failure_tracking_demo.py
# Review quality/reports/failure_analysis_report.html

# 4. Verify archive status
python tools/archive_cleanup.py --metrics

# 5. Standard quality checks
black src/ tests/ && isort src/ tests/ && flake8 src/ tests/ && mypy src/

# 6. Security and GDPR compliance
pytest tests/security/ -v
pytest tests/security/test_gdpr_compliance.py -v
```

### **📞 Support and Troubleshooting**

#### **For Technical Issues**
1. Check common issues table above
2. Verify all dependencies installed: `pip install -e ".[dev]"`
3. Ensure quality/ directory structure exists
4. Check file permissions on Windows (SQLite locking)

#### **For GDPR Compliance Questions**
1. Review `docs/context/compliance/gdpr-requirements.md`
2. Run GDPR compliance tests: `pytest tests/security/test_gdpr_compliance.py -v`
3. Verify log sanitization working properly

#### **For Feature Requests**
1. Create GitHub issue using feature template
2. Reference relevant Epic (EP-00006 for test logging features)
3. Include use case and acceptance criteria

---

**Related Documentation**:
- [Documentation Workflow](documentation-workflow.md) - How to maintain documentation
- [BDD Scenarios](../../tests/bdd/features/) - Executable test specifications
- [Requirements Matrix](../traceability/requirements-matrix.md) - Current traceability status
- [Quality Assurance Guidelines](quality-assurance.md) - Code standards and testing