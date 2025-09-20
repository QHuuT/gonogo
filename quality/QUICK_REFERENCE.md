# Quality Reports Quick Reference

## 🚀 Most Common Commands

```bash
# Generate all reports
python tools/report_generator.py

# Coverage with HTML report
pytest --cov=src tests/ --cov-report=html

# Check archive status
python tools/archive_cleanup.py --metrics

# Run all demos (generates sample data)
python tools/failure_tracking_demo.py
python tools/log_correlation_demo.py
python tools/github_issue_creation_demo.py
python tools/archive_management_demo.py
```

## 📊 Report Locations

| Report Type | Location | Key Files |
|-------------|----------|-----------|
| **Coverage** | `quality/reports/coverage/` | `index.html`, `coverage.json` |
| **Test Results** | `quality/reports/` | `*test_report.html` |
| **Failure Analysis** | `quality/reports/` | `failure_analysis.html` |
| **Log Correlation** | `quality/reports/` | `log_correlation_report.json` |
| **GitHub Issues** | `quality/reports/` | `github_issue_creation_report_*.md` |
| **Archives** | `quality/archives/` | Compressed historical reports |

## 🎯 Quality Thresholds

| Metric | Target | Action if Below |
|--------|---------|-----------------|
| **Test Coverage** | >90% | Add tests for uncovered code |
| **Test Pass Rate** | >95% | Fix failing tests immediately |
| **Failure Correlation** | >80% | Improve logging and context |
| **Archive Compression** | >50% | Review retention policies |

## 🔧 Quick Fixes

```bash
# Coverage too low?
pytest --cov=src tests/ --cov-report=term-missing  # See what's missing

# Tests failing?
pytest tests/ -v --tb=short --maxfail=5  # Show first 5 failures

# Reports not generating?
python tools/report_generator.py --debug  # Debug mode

# Archive storage full?
python tools/archive_cleanup.py --apply  # Clean old reports
```

## 📱 One-Liner Health Check

```bash
# Complete quality health check
pytest --cov=src tests/ --cov-report=term && python tools/archive_cleanup.py --metrics && echo "✅ Quality check complete"
```

For detailed information, see [Quality Reports Guide](README.md).