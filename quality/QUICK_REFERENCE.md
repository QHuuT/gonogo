# 📋 Quality & Testing Quick Reference

**Essential commands and thresholds for daily development and quality assurance**

## 🚀 Essential Daily Commands

### **Testing & Coverage**
```bash
# Core testing workflows
pytest tests/unit/ -v                          # Unit tests (fastest)
pytest tests/integration/ -v                   # Integration tests
pytest tests/security/ -v                      # Security & GDPR tests
pytest --cov=src tests/ --cov-report=html      # Coverage with HTML report
pytest --cov=src tests/ --cov-fail-under=85    # Enforce coverage threshold

# Enhanced test execution modes
pytest --mode=silent --type=all                # All tests, minimal output
pytest --mode=verbose --type=unit              # Unit tests with details
pytest --mode=detailed --type=integration      # Full debugging mode
```

### **Report Generation**
```bash
# Generate comprehensive test reports
python tools/report_generator.py                # Standard test report
python tools/report_generator.py --demo         # Demo report with coverage
python tools/failure_tracking_demo.py           # Failure analysis
python tools/log_correlation_demo.py            # Log correlation analysis
```

### **Database & RTM Operations**
```bash
# Database health and exploration
python tools/rtm-db.py admin health-check       # RTM database status
python tools/db_inspector.py                    # Overview all databases
sqlite3 gonogo.db "SELECT * FROM epics;"        # Quick RTM query

# RTM management
python tools/github_sync_manager.py             # Sync with GitHub
python tools/rtm_report_generator.py --html     # Generate RTM dashboard
```

### **Archive & Maintenance**
```bash
# Storage management
python tools/archive_cleanup.py --metrics       # Check storage usage
python tools/archive_cleanup.py --dry-run       # Preview cleanup
python tools/archive_cleanup.py --apply         # Apply retention policies
```

## 🗄️ Database Quick Access

### **Database Locations**
```bash
# Main databases in repository
gonogo.db                                # RTM database (Epics, User Stories, Tests)
quality/logs/test_failures.db           # Test failure tracking
quality/archives/archive_metadata.db    # Archive management
```

### **SQLite Command Line**
```bash
# Access RTM database
sqlite3 gonogo.db
.tables                                  # List all tables
.schema epics                           # Show table structure
.headers on && .mode column             # Format output

# Quick queries
SELECT epic_id, status FROM epics;      # Epic overview
SELECT * FROM user_stories WHERE epic_id = 'EP-00005';  # Stories for epic
SELECT test_file, last_execution_status FROM tests WHERE epic_id = 'EP-00005';
```

### **DB Browser for SQLite (GUI)**
```bash
# Recommended: Install DB Browser for SQLite
# Windows: winget install DBBrowserForSQLite.DBBrowserForSQLite
# macOS: brew install --cask db-browser-for-sqlite
# Ubuntu: sudo apt install sqlitebrowser

# Open gonogo.db in DB Browser:
# 1. File → Open Database → gonogo.db
# 2. Browse Data tab: View table contents
# 3. Execute SQL tab: Run custom queries
```

## 🚨 Troubleshooting Commands

### **Server Issues**
```bash
# Kill zombie processes (Windows)
netstat -ano | findstr :8000
taskkill /F /PID <PID_NUMBER>

# Kill zombie processes (Unix/macOS)
lsof -ti:8000 | xargs kill -9
```

### **Test Issues**
```bash
# Debug test failures
pytest --mode=detailed tests/unit/test_specific.py  # Maximum debugging
pytest -x tests/                        # Stop on first failure
pytest --pdb tests/unit/test_specific.py # Drop to debugger

# Check test discovery
pytest --collect-only                   # Show discovered tests
```

### **Database Issues**
```bash
# Database health checks
sqlite3 gonogo.db "PRAGMA integrity_check;"  # Check corruption
python tools/rtm-db.py admin validate   # RTM validation
python tools/rtm-db.py admin health-check  # Connection test
```

## 📊 Report Locations & Files

| Report Type | Location | Key Files |
|-------------|----------|-----------|
| **Coverage** | `quality/reports/coverage/` | `index.html`, `coverage.json` |
| **Test Results** | `quality/reports/` | `*test_report.html` |
| **Failure Analysis** | `quality/reports/` | `failure_analysis.html` |
| **RTM Dashboard** | `quality/reports/dynamic_rtm/` | `rtm_matrix_complete.html` |
| **Log Correlation** | `quality/reports/` | `log_correlation_report.json` |
| **Archives** | `quality/archives/` | Compressed historical reports |

## 🎯 Quality Thresholds & Targets

| Metric | Target | Warning | Action Required |
|--------|---------|---------|-----------------|
| **Test Coverage** | >90% | 80-90% | Add unit tests |
| **Test Pass Rate** | >95% | 90-95% | Fix failing tests |
| **Failure Correlation** | >80% | 60-80% | Improve logging |
| **Archive Compression** | >50% | 30-50% | Review retention |

## 🔧 Common Problem Solutions

### **Coverage Issues**
```bash
pytest --cov=src tests/ --cov-report=term-missing  # Show missing lines
pytest --cov=src tests/ --cov-fail-under=85        # Enforce threshold
```

### **Test Failures**
```bash
pytest tests/ -v --tb=short --maxfail=5    # Show first 5 failures
python tools/failure_tracking_demo.py      # Analyze failure patterns
```

### **Report Problems**
```bash
python tools/report_generator.py --debug   # Debug report generation
pip install jinja2                         # Fix missing dependencies
```

### **Storage Issues**
```bash
python tools/archive_cleanup.py --metrics  # Check usage
python tools/archive_cleanup.py --apply    # Clean old reports
```

## 📱 One-Liner Health Checks

```bash
# Complete system health check
pytest --cov=src tests/ -v && python tools/rtm-db.py admin health-check && python tools/archive_cleanup.py --metrics

# Quick test status
pytest tests/unit/ -v --maxfail=3

# RTM status check
python tools/rtm-db.py query epics --format table
```

## 🔗 Related Documentation

- **[Testing Guide](TESTING_GUIDE.md)** - Complete testing workflows
- **[Database Guide](DATABASE_GUIDE.md)** - Database exploration and queries
- **[RTM Guide](RTM_GUIDE.md)** - Requirements traceability matrix
- **[Troubleshooting](TROUBLESHOOTING.md)** - Detailed problem solving
- **[Quality Hub](README.md)** - Main navigation and persona guides