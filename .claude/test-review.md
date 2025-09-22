# 🧪 Code Review & Testing Agent

**Purpose**: Comprehensive testing workflows, code review standards, and quality analysis

## 🧪 Comprehensive Testing Commands

### **Test Execution Modes**
```bash
# Basic test execution
pytest tests/ -v                    # All tests with verbose output
pytest tests/unit/ -v               # Unit tests only
pytest tests/integration/ -v        # Integration tests only
pytest tests/security/ -v           # Security tests only
pytest tests/e2e/ -v               # End-to-end tests only

# Enhanced execution modes
pytest --mode=silent --type=all     # All tests, minimal output
pytest --mode=verbose --type=unit   # Unit tests with detailed output
pytest --mode=detailed --type=integration  # Integration with full debugging

# Test type filtering
pytest --type=unit                  # Unit tests only
pytest --type=integration           # Integration tests only
pytest --type=security              # Security tests only
pytest --type=e2e                   # End-to-end tests only
pytest --type=bdd                   # BDD scenarios only
```

### **Coverage Analysis**
```bash
# Coverage reports
pytest --cov=src tests/             # Basic coverage
pytest --cov=src tests/ --cov-report=html  # HTML coverage report
pytest --cov=src tests/ --cov-report=term-missing  # Terminal with missing lines
pytest --cov=src tests/ --cov-report=json  # JSON coverage data

# Coverage with specific thresholds
pytest --cov=src tests/ --cov-fail-under=85  # Fail if coverage < 85%

# Combined coverage and output
pytest --cov=src tests/ --cov-report=html --cov-report=term-missing -v
```

## 📊 Test Report Generation

### **Structured Test Reports**
```bash
# Generate comprehensive test reports
python tools/report_generator.py --demo                    # Demo report with coverage
python tools/report_generator.py --input quality/logs/test_execution.log  # From logs
python tools/report_generator.py --type unit --output quality/reports/    # Filtered reports
python tools/report_generator.py --input quality/logs/ --filename custom_report.html

# Test log generation
python tools/generate_test_logs.py                         # Generate sample test logs
```

### **Failure Analysis & Debugging**
```bash
# Test failure tracking and analysis
python tools/failure_tracking_demo.py                      # Generate failure analysis
# View: quality/reports/failure_analysis_report.html

# Log-failure correlation for debugging
python tools/log_correlation_demo.py                       # Generate correlation analysis
# View: quality/reports/log_correlation_report.json
# View: quality/reports/reproduction_script_*.py (auto-generated debug scripts)

# Database inspection for test data
python tools/db_inspector.py                               # Overview of all databases
python tools/db_inspector.py --db quality/logs/test_failures.db  # Examine specific database
python tools/db_inspector.py --db quality/logs/test_failures.db --interactive
```

## 🔄 RTM Test Integration

### **Test Discovery & Synchronization**
```bash
# Test discovery and database sync
python tools/test-db-integration.py discover tests         # Discover all tests and sync to database
python tools/test-db-integration.py discover tests --dry-run  # Preview discovery
python tools/test-db-integration.py discover scenarios     # Discover BDD scenarios
python tools/test-db-integration.py discover scenarios --dry-run  # Preview BDD linking

# Test execution with database integration (NO AUTO-DEFECTS)
python tools/test-db-integration.py run tests              # Basic database integration
python tools/test-db-integration.py run tests --sync-tests # Sync tests before running
python tools/test-db-integration.py run tests --test-type unit  # Run specific test type
```

### **Enhanced Pytest Integration (Safe Mode)**
```bash
# Database integration without auto-defect creation
pytest --sync-tests tests/                                 # Sync tests and run with database tracking
pytest --sync-tests tests/unit/                           # Sync unit tests only
pytest --link-scenarios tests/bdd/                        # Link BDD scenarios and run

# Note: --auto-defects flag excluded per user request
```

### **Integration Status & Analysis**
```bash
# Test-database integration status
python tools/test-db-integration.py status overview        # Show integration status
python tools/test-db-integration.py utils analyze         # Analyze integration patterns
python tools/test-db-integration.py utils analyze --show-epic-refs  # Show Epic references
python tools/test-db-integration.py utils analyze --show-orphaned   # Show unlinked tests
```

## 🗄️ SQLite Database Access Guide

### **Database Locations in Repository**
```bash
# RTM (Requirements Traceability Matrix) Database
gonogo.db                               # Main RTM database (Epics, User Stories, Tests, Defects)
src/be/gonogo.db                        # Backup/secondary RTM database

# Test Execution Databases
quality/logs/test_failures.db           # Test failure tracking and analysis
quality/logs/demo_test_failures.db      # Demo test failure data

# Archive and Metadata Databases
quality/archives/archive_metadata.db    # Archive management metadata
test_rtm.db                             # Test RTM database (development)
```

### **Quick SQLite CLI Access**
```bash
# Access RTM database directly
sqlite3 gonogo.db

# Common SQLite commands once connected:
.tables                                 # List all tables
.schema table_name                      # Show table structure
.headers on                            # Show column headers
.mode column                           # Format output as columns

# Example queries:
SELECT * FROM epics;                    # View all epics
SELECT * FROM user_stories WHERE epic_id = 'EP-00005';  # Stories for specific epic
SELECT * FROM tests WHERE epic_id = 'EP-00005';         # Tests for specific epic
SELECT * FROM defects ORDER BY priority DESC;           # Defects by priority

.quit                                   # Exit SQLite
```

### **Database Inspection Tools**
```bash
# Use project's database inspector (recommended)
python tools/db_inspector.py                               # Overview of all databases
python tools/db_inspector.py --db gonogo.db                # Inspect RTM database
python tools/db_inspector.py --db quality/logs/test_failures.db  # Inspect test failures
python tools/db_inspector.py --interactive                 # Interactive browser mode

# RTM-specific database queries
python tools/rtm-db.py query epics --format table         # List all epics
python tools/rtm-db.py query user-stories --epic-id EP-00005  # Stories for epic
python tools/rtm-db.py admin health-check                 # Database health status
```

### **Database Schema Overview**
```sql
-- RTM Database Tables (gonogo.db)
epics                 -- Epic definitions and status
user_stories          -- User stories linked to epics
tests                 -- Test files linked to epics/stories
defects               -- Defect tracking and management
github_sync_records   -- GitHub synchronization logs

-- Test Database Tables (quality/logs/test_*.db)
test_executions       -- Test run results and timing
test_failures         -- Failed test analysis and patterns
log_entries           -- Structured test execution logs
```

### **Database Backup & Recovery**
```bash
# Backup RTM database
python tools/rtm-db.py data export --output rtm_backup_$(date +%Y%m%d).json

# Restore from backup
python tools/rtm-db.py data import rtm_backup_20250922.json

# Manual SQLite backup
sqlite3 gonogo.db ".backup gonogo_backup.db"

# Database integrity check
python tools/rtm-db.py admin validate                     # RTM database validation
sqlite3 gonogo.db "PRAGMA integrity_check;"               # SQLite integrity check
```

### **Common Debugging Queries**
```bash
# SQLite command line examples
sqlite3 gonogo.db << EOF
-- Check epic progress
SELECT e.epic_id, e.title, e.status,
       COUNT(us.id) as user_stories_count,
       SUM(CASE WHEN us.implementation_status = 'completed' THEN us.story_points ELSE 0 END) as completed_points,
       SUM(us.story_points) as total_points
FROM epics e
LEFT JOIN user_stories us ON e.id = us.epic_id
GROUP BY e.id;

-- Find tests without epic links
SELECT test_file, test_type, title FROM tests WHERE epic_id IS NULL;

-- Show recent GitHub sync activity
SELECT * FROM github_sync_records ORDER BY sync_timestamp DESC LIMIT 10;
EOF
```

## 📋 Code Review Standards

### **Pre-Review Checklist**
- [ ] **All tests pass**: Run full test suite
- [ ] **Coverage maintained**: Check coverage hasn't decreased
- [ ] **Code quality**: Black, isort, flake8, mypy all pass
- [ ] **Security tests**: Security test suite passes
- [ ] **BDD scenarios**: Relevant scenarios created/updated
- [ ] **Documentation**: Code is well-documented

### **Review Quality Gates**
```bash
# Full quality validation pipeline
pytest tests/ -v                    # All tests pass
pytest --cov=src tests/ --cov-fail-under=85  # Coverage threshold
black --check src/ tests/           # Code formatting check
isort --check-only src/ tests/      # Import sorting check
flake8 src/ tests/                  # Linting
mypy src/                          # Type checking

# Combined quality check
black --check src/ tests/ && isort --check-only src/ tests/ && flake8 src/ tests/ && mypy src/ && pytest tests/ -v
```

### **Security Review**
```bash
# Security-focused testing
pytest tests/security/ -v           # Run security test suite
pytest tests/unit/ -k "security" -v # Unit tests with security focus
pytest tests/integration/ -k "gdpr" -v  # GDPR compliance tests

# GDPR compliance validation
# Check for personal data handling in new code
# Verify consent mechanisms are working
# Validate data retention policies
```

## 📈 Performance Testing

### **Performance Analysis**
```bash
# Test execution performance
pytest tests/unit/ --durations=10   # Show 10 slowest tests
pytest tests/ --benchmark-only      # Run only benchmark tests (if configured)

# Database performance
python tools/rtm-db.py admin validate  # Database integrity check
python tools/test-db-integration.py status overview  # Integration performance
```

### **Archive Management**
```bash
# Test archive management and retention
python tools/archive_cleanup.py --metrics              # Storage analysis
python tools/archive_cleanup.py --dry-run              # Preview cleanup
python tools/archive_cleanup.py --search "test_report" # Search archived files
```

## 🔍 Debugging Workflows

### **Test Debugging**
```bash
# Detailed debugging mode
pytest --mode=detailed tests/unit/test_specific.py     # Maximum debugging info
pytest -s tests/unit/test_specific.py                  # No output capture
pytest --pdb tests/unit/test_specific.py               # Drop into debugger on failure
pytest -x tests/unit/                                  # Stop on first failure

# Logging and debug output
pytest --log-cli-level=DEBUG tests/unit/test_specific.py  # Show debug logs
pytest --capture=no tests/unit/test_specific.py        # Show all output
```

### **Integration Debugging**
```bash
# Database debugging
python tools/db_inspector.py --db quality/logs/test_failures.db --table test_failures
python tools/rtm-db.py admin health-check              # Database health
python tools/rtm-db.py admin validate                  # Data integrity

# RTM integration debugging
python tools/github_sync_manager.py --dry-run --validate  # Sync validation
python tools/test-db-integration.py utils analyze --show-orphaned  # Find unlinked tests
```

## 📊 Quality Metrics & Thresholds

### **Quality Standards**
- **Test Coverage**: >85% (fail build if below)
- **Unit Test Ratio**: >70% of total tests
- **Integration Coverage**: Critical paths covered
- **Security Tests**: All GDPR and security features tested
- **Performance**: No tests >10s execution time

### **Quality Monitoring**
```bash
# Generate quality dashboard
python tools/report_generator.py                       # Comprehensive quality report
python tools/failure_tracking_demo.py                  # Failure pattern analysis

# Coverage trending
pytest --cov=src tests/ --cov-report=json             # JSON for CI/CD integration
```

## 🔄 GitHub Integration for Reviews

### **GitHub Issue Integration**
```bash
# Create issues for test failures (manual process)
gh issue create --title "Test Failure: Description" --label "defect,priority/high"

# GitHub issue creation for systematic failures
python tools/github_issue_creation_demo.py --dry-run   # Generate issue templates
# Note: Manual review required - no automatic defect creation
```

### **RTM Updates for Reviews**
```bash
# RTM synchronization for review context
python tools/github_sync_manager.py                    # Full GitHub sync
python tools/rtm-db.py query epic-progress EP-XXXXX    # Epic progress review
python tools/rtm_report_generator.py --html            # Generate RTM report for review
```

## 🔗 Cross-Agent References

- **🔧 Daily Development**: See `.claude/daily-dev.md` for daily testing needs
- **📚 Documentation**: See `.claude/documentation.md` for test documentation
- **🎨 UX/UI Design**: See `.claude/ux-ui-design.md` for UI testing standards
- **🚨 Emergency**: See `.claude/emergency.md` for test failure recovery
- **📖 Main Guide**: See `CLAUDE.md` for project overview

## 💡 Testing Best Practices

### **Test Design Principles**
- **Unit Tests**: Fast, isolated, mock external dependencies
- **Integration Tests**: Test component interactions, use real databases
- **Security Tests**: Validate GDPR compliance, input sanitization
- **E2E Tests**: Critical user journeys only
- **Performance**: Set reasonable timeouts, monitor execution time

### **Review Guidelines**
- **Test First**: Review test changes before implementation
- **Coverage Context**: Understand what new coverage means
- **Edge Cases**: Ensure edge cases and error conditions are tested
- **Regression**: Verify tests would catch the bug being fixed
- **Maintainability**: Tests should be clear and maintainable

---

**🎯 Focus**: This file provides comprehensive testing and code review workflows. Use for thorough quality validation and review processes.**