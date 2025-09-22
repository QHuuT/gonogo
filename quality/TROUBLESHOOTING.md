# 🚨 Quality & Testing Troubleshooting Guide

**Complete troubleshooting guide for common issues in testing, reports, databases, and RTM systems**

## 🔧 Server and Port Issues

### **🛑 Kill Zombie Server Processes (Most Common)**
```bash
# Windows - Kill by port (most common)
netstat -ano | findstr :8000
taskkill /F /PID <PID_NUMBER>

# Windows - Nuclear option (kill all uvicorn)
wmic process where "name='python.exe' and commandline like '%uvicorn%'" delete

# PowerShell alternative
Get-Process python* | Stop-Process -Force

# Verify port is free
netstat -ano | findstr :8000
```

### **macOS/Linux Server Issues**
```bash
# Kill process on specific port
lsof -ti:8000 | xargs kill -9

# Kill uvicorn processes
pkill -f uvicorn

# Verify port is free
lsof -i :8000
```

### **Server Won't Start**
```bash
# Check if port is already in use
netstat -ano | findstr :8000          # Windows
lsof -i :8000                         # macOS/Linux

# Check for permission issues
python -m uvicorn src.be.main:app --reload --host 127.0.0.1 --port 8001

# Verify dependencies
pip install uvicorn fastapi sqlalchemy jinja2
pip check
```

## 🧪 Test Execution Issues

### **Tests Not Running**
```bash
# Check test discovery
pytest --collect-only

# Verify dependencies
pip install -e ".[dev]"
pip install jinja2

# Check for import errors
python -c "import src.be.main; print('Imports OK')"

# Run with verbose output
pytest tests/ -v --tb=short
```

### **Test Failures - Debugging**
```bash
# Stop on first failure
pytest tests/ -x

# Run specific test with debug info
pytest tests/unit/test_specific.py -s -v --tb=long

# Show locals in traceback
pytest tests/unit/test_specific.py --tb=long --show-capture=all

# Run without output capture
pytest tests/unit/test_specific.py -s
```

### **Coverage Reports Not Generating**
```bash
# Ensure coverage package is installed
pip install coverage pytest-cov

# Check if source paths are correct
pytest --cov=src tests/ --cov-config=pyproject.toml

# Generate both HTML and terminal output
pytest --cov=src tests/ --cov-report=html --cov-report=term-missing

# Check coverage configuration
cat pyproject.toml | grep -A 10 "coverage"
```

### **RTM Integration Issues**
```bash
# Test database connection
python tools/rtm-db.py admin health-check

# Re-sync test discovery
python tools/test-db-integration.py discover tests

# Check for orphaned tests
python tools/test-db-integration.py utils analyze --show-orphaned

# Verify GitHub sync status
python tools/github_sync_manager.py --validate
```

## 📊 Report Generation Issues

### **Missing Report Data**
```bash
# Verify test execution produces data
pytest tests/ -v --tb=short

# Check if logs are being generated
ls -la quality/logs/

# Run report generator in debug mode
python tools/report_generator.py --debug

# Generate demo reports to test functionality
python tools/failure_tracking_demo.py
python tools/log_correlation_demo.py
```

### **Empty or Broken Reports**
```bash
# Check report templates exist
ls -la quality/reports/templates/

# Verify report assets
ls -la quality/reports/assets/

# Check for permission issues
ls -la quality/reports/

# Regenerate with verbose output
python tools/report_generator.py --verbose
```

### **HTML Reports Not Opening**
```bash
# Check file permissions
ls -la quality/reports/*.html

# Try different browser
firefox quality/reports/test_report.html

# Check for file corruption
file quality/reports/test_report.html

# Regenerate report
python tools/report_generator.py --demo
```

## 🗄️ Database Issues

### **Database Connection Problems**
```bash
# Check database exists
ls -la gonogo.db
ls -la quality/logs/test_failures.db

# Test database integrity
sqlite3 gonogo.db "PRAGMA integrity_check;"

# Check database permissions
ls -la gonogo.db

# Test with database inspector
python tools/db_inspector.py
```

### **Database Corruption**
```bash
# Check database integrity
sqlite3 gonogo.db "PRAGMA integrity_check;"
sqlite3 gonogo.db "PRAGMA foreign_key_check;"

# Backup database before repair
cp gonogo.db gonogo_backup.db

# Vacuum database (rebuild and optimize)
sqlite3 gonogo.db "VACUUM;"

# Export and reimport if severely corrupted
sqlite3 gonogo.db .dump > backup.sql
sqlite3 new_gonogo.db < backup.sql
```

### **RTM Database Issues**
```bash
# Reset RTM database (DANGEROUS - backup first)
cp gonogo.db gonogo_backup_$(date +%Y%m%d).db
python tools/rtm-db.py admin reset --confirm

# Re-sync from GitHub
python tools/github_sync_manager.py

# Validate data integrity
python tools/rtm-db.py admin validate
```

## 📁 Archive and Storage Issues

### **Archive Cleanup Failures**
```bash
# Check disk space
df -h quality/                         # Unix
dir quality                            # Windows

# Check permissions
ls -la quality/archives/

# Run cleanup in dry-run mode first
python tools/archive_cleanup.py --dry-run --verbose

# Check for file locks
lsof quality/archives/*                # Unix
```

### **Storage Full / Performance Issues**
```bash
# Check storage usage
python tools/archive_cleanup.py --metrics

# Apply retention policies
python tools/archive_cleanup.py --apply

# Manual cleanup of old reports
find quality/reports/ -name "*.html" -mtime +30 -delete    # Unix
forfiles /p quality\reports /s /d -30 /c "cmd /c del @path"  # Windows

# Compress large files
gzip quality/logs/*.log                # Unix
```

## 🔧 Dependency and Environment Issues

### **Missing Dependencies**
```bash
# Reinstall all dependencies
pip install -e ".[dev]"
pip install jinja2

# Check for conflicts
pip check

# List installed packages
pip list | grep -E "(pytest|coverage|fastapi|uvicorn|sqlalchemy)"

# Upgrade outdated packages
pip list --outdated
pip install --upgrade pytest coverage
```

### **Python Environment Issues**
```bash
# Check Python version
python --version

# Check virtual environment
which python                          # Unix
where python                          # Windows

# Recreate virtual environment if needed
deactivate
rm -rf venv/
python -m venv venv
source venv/bin/activate               # Unix
venv\Scripts\activate                  # Windows
pip install -e ".[dev]"
```

### **Import Errors**
```bash
# Check PYTHONPATH
echo $PYTHONPATH                       # Unix
echo %PYTHONPATH%                      # Windows

# Test imports manually
python -c "import src.be.main"
python -c "import src.shared.testing.failure_tracker"

# Add current directory to path
export PYTHONPATH=.:$PYTHONPATH        # Unix
set PYTHONPATH=.;%PYTHONPATH%          # Windows
```

## 🌐 RTM Web Dashboard Issues

### **Dashboard Not Loading**
```bash
# Check server is running
curl http://localhost:8000/health

# Check for port conflicts
netstat -ano | findstr :8000

# Start server with debug logging
python -m uvicorn src.be.main:app --reload --log-level debug

# Check for template errors
python -c "from src.be.main import app; print('App loads OK')"
```

### **RTM Data Not Showing**
```bash
# Check database has data
python tools/rtm-db.py query epics --format table

# Check GitHub sync status
python tools/github_sync_manager.py --progress-report

# Force RTM report regeneration
python tools/rtm_report_generator.py --html

# Check web dashboard URL
curl http://localhost:8000/api/rtm/reports/matrix?format=html
```

### **Filtering Not Working**
```bash
# Check JavaScript console for errors
# Open browser dev tools (F12) and check Console tab

# Verify static assets are loading
curl http://localhost:8000/static/js/rtm-interactions.js

# Check CSS is loading
curl http://localhost:8000/static/css/rtm-components.css

# Regenerate RTM report
python tools/rtm_report_generator.py --html
```

## 📈 Performance Issues

### **Slow Test Execution**
```bash
# Show slowest tests
pytest tests/ --durations=10

# Run only fast tests
pytest tests/unit/ -v

# Profile test execution
pytest tests/ --profile

# Parallel test execution (if pytest-xdist installed)
pytest tests/ -n auto
```

### **Large Database Size**
```bash
# Check database size
ls -lh gonogo.db
ls -lh quality/logs/test_failures.db

# Vacuum databases
sqlite3 gonogo.db "VACUUM;"
sqlite3 quality/logs/test_failures.db "VACUUM;"

# Archive old data
python tools/archive_cleanup.py --apply

# Check for orphaned records
python tools/rtm-db.py admin validate
```

### **Memory Issues**
```bash
# Monitor memory usage during tests
# Unix: top -p $(pgrep python)
# Windows: tasklist | findstr python

# Run tests in smaller batches
pytest tests/unit/ -v
pytest tests/integration/ -v

# Clear pytest cache
rm -rf .pytest_cache/
```

## 🚨 Emergency Recovery

### **Complete Environment Reset**
```bash
# WARNING: This will reset your development environment

# 1. Stop all processes
pkill -f python                       # Unix
taskkill /F /IM python.exe            # Windows

# 2. Clean Python environment
pip uninstall -r requirements.txt -y
pip install -e ".[dev]"
pip install jinja2

# 3. Reset databases (backup first!)
cp gonogo.db gonogo_backup.db
python tools/rtm-db.py admin reset --confirm

# 4. Reinitialize system
python tools/test-db-integration.py discover tests
python tools/github_sync_manager.py
python tools/rtm-db.py admin health-check
```

### **Git Repository Recovery**
```bash
# Check repository state
git status
git fsck

# Reset to known good state
git log --oneline -10
git reset --hard <commit-hash>
git clean -fd

# Restore from backup if needed
cp gonogo_backup.db gonogo.db
```

## 🔍 Diagnostic Commands

### **System Health Check**
```bash
# Complete health check
python --version
git status
python tools/rtm-db.py admin health-check
python tools/archive_cleanup.py --metrics
pytest tests/unit/ -v --maxfail=1
```

### **Environment Diagnostics**
```bash
# Python environment
python --version
pip list | grep -E "(pytest|coverage|fastapi)"
pip check

# System resources
# Unix: ps aux | grep python
# Windows: tasklist | findstr python

# Network connectivity
curl http://localhost:8000/health
ping localhost
```

### **Log Analysis**
```bash
# Check for errors in logs
grep -i error quality/logs/*.log
grep -i fail quality/logs/*.log

# Check recent activity
tail -f quality/logs/test_execution.log

# Analyze failure patterns
python tools/failure_tracking_demo.py
python tools/log_correlation_demo.py
```

## 📞 Escalation Procedures

### **When to Escalate**
- **Data Loss**: Any indication of database corruption or data loss
- **Security Issues**: Potential security vulnerabilities discovered
- **System Corruption**: Git repository corruption or unrecoverable state
- **Performance Degradation**: System becoming unusable
- **Dependency Conflicts**: Unable to resolve package conflicts

### **Information to Collect**
```bash
# System information
python --version
pip list > environment_packages.txt
git status
git log --oneline -5

# Error information
pytest tests/ -v --tb=long > error_log.txt 2>&1
python tools/rtm-db.py admin health-check > health_log.txt

# Database state
python tools/db_inspector.py > db_status.txt
```

## 🔗 Related Documentation

- **[Testing Guide](TESTING_GUIDE.md)** - Complete testing workflows
- **[Database Guide](DATABASE_GUIDE.md)** - Database exploration and maintenance
- **[RTM Guide](RTM_GUIDE.md)** - RTM dashboard and web interface
- **[Quality Reports Guide](README.md)** - Report generation and analysis
- **[Quick Reference](QUICK_REFERENCE.md)** - Common commands and thresholds

---

**Last Updated**: 2024-09-22
**Purpose**: Centralized troubleshooting guide extracting issues from README.md, TESTING_GUIDE.md, and other quality documentation