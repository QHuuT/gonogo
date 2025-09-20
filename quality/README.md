# Quality Reports Guide

This guide explains how to generate, interpret, and use all quality reports available in the gonogo project.

## 📁 Quality Folder Structure

```
quality/
├── archives/           # Test report archives and retention data
├── logs/              # Structured logging outputs
├── monitoring/        # System monitoring and metrics
├── reports/           # Generated quality reports
│   ├── coverage/      # HTML coverage reports
│   ├── assets/        # Report styling and resources
│   └── templates/     # Report templates
└── README.md          # This guide
```

## ⚙️ Report Generation Conditions & Triggers

### **Automatic Report Generation**
Reports are generated based on these conditions and triggers:

#### **1. Test Execution Triggers**
- **When**: Every time `pytest` is run with the structured logging plugin
- **Condition**: Tests must be executed in the project with pytest
- **Output**: Structured logs created in `quality/logs/`
- **Automatic**: Yes, via pytest integration plugin

#### **2. Coverage Report Triggers**
- **When**: `pytest --cov=src` command is executed
- **Condition**: pytest-cov plugin must be installed and configured
- **Output**: HTML and JSON coverage reports in `quality/reports/coverage/`
- **Automatic**: Yes, when coverage flags are used

#### **3. Manual Report Generation**
- **When**: Explicitly run via command line tools
- **Condition**: User or CI/CD pipeline executes report generation commands
- **Output**: Various report types based on available data
- **Automatic**: No, requires manual execution

#### **4. Failure-Based Report Generation**
- **When**: Test failures are detected and tracked
- **Condition**: FailureTracker system records failures during test execution
- **Output**: Failure analysis reports and reproduction scripts
- **Automatic**: Yes, when failures occur

#### **5. Archive Management Triggers**
- **When**: Scheduled via cron jobs or manual execution
- **Condition**: Reports and logs exist and meet retention policy criteria
- **Output**: Compressed archives and cleanup reports
- **Automatic**: Can be automated via scheduling

### **Data Requirements for Report Generation**
Each report type requires specific data sources to exist:

| Report Type | Required Data Source | Trigger Condition |
|-------------|---------------------|-------------------|
| **Test Execution** | Structured log files | Pytest runs with logging enabled |
| **Coverage** | Coverage data files | Tests run with `--cov` flag |
| **Failure Analysis** | Failure tracking DB | Test failures recorded in database |
| **Log Correlation** | Both logs + failures | Structured logging + failure tracking |
| **GitHub Issues** | Failure data + auth | Failures exist + GitHub credentials |
| **Archive Reports** | Historical reports | Previous reports exist in quality/ |

## 🎯 Quick Start Commands

```bash
# Generate all reports
python tools/report_generator.py

# Run specific demos (generate sample data + reports)
python tools/failure_tracking_demo.py
python tools/log_correlation_demo.py
python tools/github_issue_creation_demo.py
python tools/archive_management_demo.py

# Generate coverage reports
pytest --cov=src tests/ --cov-report=html --cov-report=json

# Check archive status
python tools/archive_cleanup.py --metrics
```

## 📊 Report Types Overview

### 1. Coverage Reports
**Purpose**: Track code coverage from test execution
**Location**: `quality/reports/coverage/`
**Generation**: Automatic with `pytest --cov`

#### How to Generate
```bash
# HTML coverage report
pytest --cov=src tests/ --cov-report=html

# JSON coverage data
pytest --cov=src tests/ --cov-report=json

# Both formats
pytest --cov=src tests/ --cov-report=html --cov-report=json
```

#### How to Interpret
- **Green lines**: Covered by tests
- **Red lines**: Not covered by tests
- **Yellow lines**: Partially covered (branches)
- **Coverage percentage**: % of lines executed during tests

#### Key Files
- `index.html` - Main coverage dashboard
- `coverage.json` - Raw coverage data for CI/CD
- Individual module reports (e.g., `z_*_py.html`)

#### Quality Thresholds
- **Excellent**: >90% coverage
- **Good**: 80-90% coverage
- **Needs attention**: <80% coverage

---

### 2. Test Execution Reports
**Purpose**: Detailed test run results with GDPR-compliant logging
**Location**: `quality/reports/`
**Generation**: Via `tools/report_generator.py`

#### How to Generate
```bash
# Generate comprehensive test report
python tools/report_generator.py

# Custom report with specific test type
python tools/report_generator.py --test-type unit
python tools/report_generator.py --test-type integration
```

#### Report Contents
- **Test Summary**: Pass/fail counts, execution time
- **Test Details**: Individual test results with timing
- **Environment Info**: Python version, dependencies
- **GDPR Compliance**: Sanitized logs (no personal data)

#### Sample Reports
- `demo_test_report.html` - Complete test execution report
- `gdpr_test_report.html` - GDPR-specific test results
- `test_report.html` - Standard test summary

---

### 3. Failure Analysis Reports
**Purpose**: Track and analyze test failures with debugging context
**Location**: `quality/reports/`
**Generation**: Via `tools/failure_tracking_demo.py`

#### How to Generate
```bash
# Generate failure tracking demo data and reports
python tools/failure_tracking_demo.py

# View failure patterns and statistics
python -c "
from src.shared.testing.failure_tracker import FailureTracker
tracker = FailureTracker()
stats = tracker.get_failure_statistics()
print(f'Total failures: {stats.total_failures}')
print(f'Most common: {stats.most_common_category}')
"
```

#### Report Contents
- **Failure Patterns**: Common error types and frequencies
- **Failure Timeline**: When failures occurred
- **Error Categories**: Assertion, import, timeout, etc.
- **Debugging Context**: Stack traces and reproduction info

#### Key Files
- `failure_analysis.html` - Visual failure analysis dashboard
- `failure_summary_daily.json` - Daily failure statistics
- `reproduction_script_*.py` - Auto-generated failure reproduction scripts

#### Understanding Failure Categories
- **assertion_error**: Test assertions failed
- **import_error**: Module import problems
- **timeout_error**: Tests exceeded time limits
- **unicode_error**: Text encoding issues
- **unknown_error**: Unclassified failures

---

### 4. Log Correlation Reports
**Purpose**: Correlate structured logs with test failures for debugging
**Location**: `quality/reports/`
**Generation**: Via `tools/log_correlation_demo.py`

#### How to Generate
```bash
# Generate log correlation analysis
python tools/log_correlation_demo.py

# Export correlation report
python -c "
from src.shared.testing.log_failure_correlator import LogFailureCorrelator
correlator = LogFailureCorrelator()
report_path = correlator.export_correlation_report()
print(f'Report saved: {report_path}')
"
```

#### Report Contents
- **Correlation Summary**: Success rates, patterns found
- **Failure Contexts**: Complete debugging context for each failure
- **Log Analysis**: Setup, execution, and teardown logs
- **Reproduction Guides**: Step-by-step failure reproduction

#### Key Files
- `log_correlation_report.json` - Complete correlation analysis
- Individual correlation contexts with environment data

#### Correlation Success Rates
- **>80%**: Excellent log-failure correlation
- **60-80%**: Good correlation, minor gaps
- **<60%**: Poor correlation, logging improvements needed

---

### 5. GitHub Issue Creation Reports
**Purpose**: Track automated issue creation and project management
**Location**: `quality/reports/`
**Generation**: Via `tools/github_issue_creation_demo.py`

#### How to Generate
```bash
# Generate issue creation demo and reports
python tools/github_issue_creation_demo.py

# Create issues from failures (when configured)
python -c "
from src.shared.testing.github_issue_creator import GitHubIssueCreator
creator = GitHubIssueCreator()
# creator.create_issue_from_failure(failure_id)  # When auth configured
"
```

#### Report Contents
- **Issue Templates**: Generated issue content previews
- **Creation Summary**: Success/failure rates for issue creation
- **GitHub Integration**: Project board updates and labeling
- **Traceability**: Links between failures and GitHub issues

#### Key Files
- `github_issue_creation_report_*.md` - Issue creation summaries
- `issue_template_*.md` - Generated issue templates
- Individual issue content with proper formatting

---

### 6. Archive Management Reports
**Purpose**: Monitor test report retention and storage optimization
**Location**: `quality/archives/` and `quality/reports/`
**Generation**: Via `tools/archive_management_demo.py`

#### How to Generate
```bash
# Full archive management demo
python tools/archive_management_demo.py

# Check current archive status
python tools/archive_cleanup.py --metrics

# Apply retention policies (dry run)
python tools/archive_cleanup.py --dry-run

# Apply retention policies (live)
python tools/archive_cleanup.py --apply
```

#### Report Contents
- **Storage Metrics**: Total size, compression ratios, file counts
- **Retention Status**: Files by age and policy compliance
- **Optimization Recommendations**: Space-saving opportunities
- **Archive Search**: Historical report retrieval capabilities

#### Archive Policies (Default)
- **HTML reports**: 90 days retention, compress after 14 days
- **JSON data**: 180 days retention, compress after 30 days
- **Log files**: 60 days retention, compress after 7 days
- **Database files**: 365 days retention, compress after 90 days

---

## 🔧 Advanced Usage

### Custom Report Generation
```bash
# Generate reports with specific filters
python tools/report_generator.py \
  --test-type unit \
  --format html \
  --output-dir custom_reports/

# Generate coverage with custom thresholds
pytest --cov=src tests/ \
  --cov-fail-under=85 \
  --cov-report=term-missing
```

### Automated Report Scheduling

#### **Production Scheduling** (Recommended)
```bash
# Daily comprehensive reports (runs after nightly tests)
0 2 * * * cd /path/to/gonogo && python tools/report_generator.py 2>&1 | logger -t test_reports

# Weekly archive cleanup (Sunday 3 AM)
0 3 * * 0 cd /path/to/gonogo && python tools/archive_cleanup.py --apply 2>&1 | logger -t archive_cleanup

# Daily failure analysis (if failures exist)
30 2 * * * cd /path/to/gonogo && python tools/failure_tracking_demo.py 2>&1 | logger -t failure_tracking

# Weekly storage metrics report (Monday 8 AM)
0 8 * * 1 cd /path/to/gonogo && python tools/archive_cleanup.py --metrics 2>&1 | logger -t storage_metrics
```

#### **Development Scheduling** (Optional)
```bash
# After each test run, generate reports (via Git hooks)
# .git/hooks/post-commit:
#!/bin/bash
pytest --cov=src tests/ --cov-report=html
python tools/report_generator.py

# On pull request merge (GitHub Actions)
# Automatically generate and archive reports
```

#### **Trigger Conditions for Automation**
- **Daily Reports**: Generate if new test logs exist from previous 24 hours
- **Archive Cleanup**: Execute if storage usage > threshold OR weekly schedule
- **Failure Analysis**: Trigger when failure count > baseline OR daily schedule
- **Coverage Reports**: Generate after any test execution with coverage enabled

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Generate Quality Reports
  run: |
    pytest --cov=src tests/ --cov-report=json --cov-report=html
    python tools/report_generator.py
    python tools/archive_cleanup.py --metrics

- name: Upload Coverage Reports
  uses: actions/upload-artifact@v3
  with:
    name: coverage-reports
    path: quality/reports/coverage/
```

## 📈 Quality Metrics Dashboard

### Key Performance Indicators (KPIs)
- **Test Coverage**: >90% target
- **Test Pass Rate**: >95% target
- **Failure Correlation**: >80% target
- **Archive Efficiency**: >50% compression target

### Monitoring Thresholds
- **Coverage drops >5%**: Investigate immediately
- **Pass rate <90%**: Block releases
- **Correlation <60%**: Improve logging
- **Archive size >1GB**: Apply cleanup policies

## 🔍 Troubleshooting

### Common Issues

#### Coverage Reports Not Generating
```bash
# Ensure coverage package is installed
pip install coverage pytest-cov

# Check if source paths are correct
pytest --cov=src tests/ --cov-config=pyproject.toml
```

#### Missing Report Data
```bash
# Verify test execution produces data
pytest tests/ -v --tb=short

# Check report generator permissions
python tools/report_generator.py --debug
```

#### Archive Cleanup Failures
```bash
# Check disk space and permissions
df -h quality/
ls -la quality/archives/

# Run cleanup in dry-run mode first
python tools/archive_cleanup.py --dry-run --verbose
```

## 📚 Related Documentation

- **[Development Workflow](../docs/technical/development-workflow.md)** - Complete development process
- **[Quality Assurance](../docs/technical/quality-assurance.md)** - Code standards and quality gates
- **[Testing Strategy](../docs/technical/quality-assurance.md#testing-strategy)** - Test pyramid and coverage goals
- **[RTM Documentation](../docs/traceability/requirements-matrix.md)** - Requirements traceability

## 🎯 Best Practices

### Report Generation
1. **Generate reports after each significant change**
2. **Review coverage trends, not just absolute numbers**
3. **Focus on uncovered critical paths first**
4. **Use failure analysis to identify flaky tests**

### Archive Management
1. **Monitor storage usage weekly**
2. **Adjust retention policies based on team needs**
3. **Compress old reports to save space**
4. **Maintain searchable archive for historical analysis**

### Quality Monitoring
1. **Set up automated quality gates**
2. **Track quality metrics over time**
3. **Investigate quality regressions quickly**
4. **Share quality reports with the team regularly**

---

**Last Updated**: 2025-09-20
**Version**: EP-00006 Stabilization Release