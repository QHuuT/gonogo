# 🚨 Emergency & Troubleshooting Agent

**System recovery, debugging, and emergency procedures**

## 🎯 Agent Purpose
This agent specializes in **system issues, debugging, and recovery procedures** - server recovery, test failure debugging, database recovery, and system diagnostics.

**🔄 For other tasks**: [Agent Navigation](../CLAUDE.md#🤖-agent-navigation)

## 🆘 Immediate Emergency Actions

### **Server Down / Not Responding**
```bash
# 1. Check if server process is running
ps aux | grep uvicorn  # Linux/macOS
tasklist | findstr python  # Windows

# 2. Check port usage
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 3. Kill zombie processes
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000 && taskkill /F /PID <PID>  # Windows

# 4. Restart server
python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8000

# 5. Verify server health
curl -f http://localhost:8000/health && echo "✅ Server OK" || echo "❌ Server Down"
```

### **Database Connection Failure**
```bash
# 1. Check database file exists
ls -la *.db quality/logs/*.db  # Check for database files

# 2. Database health check
python tools/rtm-db.py admin health-check

# 3. Emergency database backup (if accessible)
python tools/rtm-db.py data export --output emergency_backup_$(date +%Y%m%d_%H%M%S).json

# 4. Database recovery
python tools/rtm-db.py admin reset --confirm  # LAST RESORT
python tools/rtm-db.py data import --input emergency_backup.json
```

### **Test Suite Complete Failure**
```bash
# 1. Check Python environment
python --version && pip list | grep -E "(pytest|coverage)"

# 2. Check imports and path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"  # Linux/macOS
set PYTHONPATH=%PYTHONPATH%;%cd%\src  # Windows

# 3. Run minimal test
python -c "from src.be.models import Epic; print('✅ Imports OK')"

# 4. Test discovery check
pytest --collect-only tests/unit/ | head -20

# 5. Run single simple test
pytest tests/unit/ -k "test_" --maxfail=1 -v
```

## 🔧 System Diagnostics

### **Complete Environment Check**
```bash
# Python environment
python --version
pip --version
which python
which pip

# Project dependencies
pip list | grep -E "(fastapi|sqlalchemy|pytest|coverage)"
pip check  # Check for dependency conflicts

# Git status
git status
git log --oneline -5
git branch -a

# File system check
ls -la src/ tests/ tools/
du -sh . logs/ quality/ 2>/dev/null || echo "Some directories missing"

# Network connectivity
ping -c 3 github.com
curl -I https://api.github.com
```

### **RTM System Diagnostics**
```bash
# RTM health check
python tools/rtm-db.py admin health-check

# RTM database integrity
python tools/rtm-db.py admin validate

# RTM configuration check
python tools/rtm-links.py config-info
python tools/rtm-links.py doctor

# GitHub integration status
gh auth status
gh api user | jq '.login' 2>/dev/null || echo "GitHub CLI issue"

# RTM data counts
python tools/rtm-db.py query epics --format table | tail -1
python tools/rtm-db.py query user-stories --format table | tail -1
```

## 💥 Critical Failure Recovery

### **Project Corruption Recovery**
```bash
# 1. Backup current state
tar -czf emergency_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  src/ tests/ tools/ quality/ docs/ *.md *.py *.json *.db 2>/dev/null

# 2. Clean reinstall
rm -rf __pycache__ .pytest_cache src/__pycache__ tests/__pycache__
find . -name "*.pyc" -delete
pip uninstall -y $(pip freeze | cut -d'=' -f1)
pip install -e ".[dev]" && pip install jinja2

# 3. Verify clean state
pytest tests/unit/ --maxfail=3 -q
python tools/rtm-db.py admin health-check

# 4. Restore data if needed
# python tools/rtm-db.py data import --input emergency_backup.json
```

### **Git Repository Recovery**
```bash
# 1. Check repository integrity
git fsck --full

# 2. Reset to last known good state
git log --oneline -10  # Find last good commit
git reset --hard <GOOD_COMMIT_HASH>

# 3. Force clean workspace
git clean -fd
git checkout -- .

# 4. Restore from remote
git fetch origin
git reset --hard origin/main

# 5. Verify repository state
git status
git log --oneline -5
```

### **Database Corruption Recovery**
```bash
# 1. Backup corrupted database
cp rtm_database.db rtm_database_corrupted_$(date +%Y%m%d_%H%M%S).db

# 2. Attempt repair
sqlite3 rtm_database.db ".recover" > recovered_data.sql
sqlite3 rtm_database_new.db < recovered_data.sql

# 3. Recreate from GitHub (if repair fails)
mv rtm_database.db rtm_database_broken.db
python tools/rtm-db.py admin reset --confirm
python tools/import_real_github_data.py --import

# 4. Verify recovery
python tools/rtm-db.py admin health-check
python tools/rtm-db.py query epics --format table
```

## 🔍 Debugging Workflows

### **Server Startup Issues**
```bash
# 1. Check detailed error output
python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# 2. Check import issues
python -c "
import sys
sys.path.insert(0, 'src')
try:
    from be.main import app
    print('✅ App imports successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
"

# 3. Check FastAPI app creation
python -c "
import sys
sys.path.insert(0, 'src')
from be.main import app
print(f'✅ App type: {type(app)}')
print(f'✅ Routes: {len(app.routes)}')
"

# 4. Test alternative port
python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8001
```

### **Test Failure Debugging**
```bash
# 1. Isolate failing test
pytest tests/unit/test_failing.py::test_specific_function -v -s --tb=long

# 2. Run with debugger
pytest tests/unit/test_failing.py::test_specific_function --pdb

# 3. Check test environment
pytest tests/unit/test_failing.py -v -s --capture=no --setup-show

# 4. Test database state
python -c "
from src.be.database import SessionLocal
session = SessionLocal()
print(f'✅ Database connection OK')
session.close()
"

# 5. Failure correlation analysis
python tools/log_correlation_demo.py
cat quality/reports/log_correlation_report.json | jq '.failure_patterns'
```

### **RTM System Debugging**
```bash
# 1. Check RTM database schema
python tools/rtm-db.py admin validate --verbose

# 2. GitHub integration debugging
gh api repos/QHuuT/gonogo/issues --paginate | jq length
python tools/github_sync_manager.py --dry-run --validate

# 3. RTM link validation
python tools/rtm-links.py validate --format json | jq '.errors'

# 4. Check epic/user story relationships
python tools/rtm-db.py query epic-progress EP-00005
python tools/rtm-db.py query user-stories --epic-id EP-00005 --format table
```

## 🛠️ Recovery Tools & Scripts

### **Emergency Backup Scripts**
```bash
# Quick backup script
#!/bin/bash
BACKUP_DIR="emergency_backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup critical files
cp -r src/ "$BACKUP_DIR/"
cp -r tests/ "$BACKUP_DIR/"
cp -r tools/ "$BACKUP_DIR/"
cp *.db "$BACKUP_DIR/" 2>/dev/null || true
cp quality/logs/*.db "$BACKUP_DIR/" 2>/dev/null || true

# Backup RTM data
python tools/rtm-db.py data export --output "$BACKUP_DIR/rtm_data.json"

echo "✅ Backup created: $BACKUP_DIR"
```

### **System Health Check Script**
```bash
#!/bin/bash
echo "🔍 GoNoGo System Health Check"
echo "================================"

# Python environment
echo "Python: $(python --version 2>&1)"
echo "Pip: $(pip --version 2>&1)"

# Critical dependencies
echo "FastAPI: $(pip show fastapi | grep Version || echo 'Not installed')"
echo "SQLAlchemy: $(pip show sqlalchemy | grep Version || echo 'Not installed')"
echo "Pytest: $(pip show pytest | grep Version || echo 'Not installed')"

# Server connectivity
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Server: Running"
else
    echo "❌ Server: Not responding"
fi

# Database
if python tools/rtm-db.py admin health-check >/dev/null 2>&1; then
    echo "✅ Database: OK"
else
    echo "❌ Database: Issues detected"
fi

# Git repository
if git status >/dev/null 2>&1; then
    echo "✅ Git: Repository OK"
else
    echo "❌ Git: Repository issues"
fi

# GitHub CLI
if gh auth status >/dev/null 2>&1; then
    echo "✅ GitHub CLI: Authenticated"
else
    echo "❌ GitHub CLI: Not authenticated"
fi

echo "================================"
echo "Health check complete"
```

## 🚨 Escalation Procedures

### **When All Else Fails**
```bash
# 1. Document the issue
echo "Issue Description: $(date)" > emergency_log.txt
git log --oneline -10 >> emergency_log.txt
python --version >> emergency_log.txt
pip list >> emergency_log.txt

# 2. Create comprehensive backup
tar -czf emergency_complete_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  . --exclude='.git' --exclude='__pycache__' --exclude='*.pyc'

# 3. Nuclear option: Fresh start
git stash --include-untracked
git checkout main
git reset --hard origin/main
git clean -fd
rm -rf __pycache__ .pytest_cache src/__pycache__ tests/__pycache__
pip uninstall -y $(pip freeze | cut -d'=' -f1)
pip install -e ".[dev]" && pip install jinja2

# 4. Verify minimum functionality
python -c "from src.be.main import app; print('✅ Basic imports work')"
pytest tests/unit/ --maxfail=1 -q
python tools/rtm-db.py admin health-check
```

### **Emergency Contacts & Resources**
```markdown
## Emergency Documentation
- Project README: README.md
- Setup Guide: CLAUDE.md
- Development Workflow: docs/technical/development-workflow.md
- Quality Assurance: docs/technical/quality-assurance.md

## Key Command References
- RTM Health: `python tools/rtm-db.py admin health-check`
- Server Start: `python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8000`
- Quick Test: `pytest tests/unit/ -q --maxfail=3`
- Git Status: `git status && git log --oneline -5`

## Recovery Priorities
1. Preserve data (RTM database, user work)
2. Restore basic functionality (server, tests)
3. Verify GitHub integration
4. Restore full feature set
```

## 🔄 Prevention & Monitoring

### **Proactive Health Monitoring**
```bash
# Daily health check script
python tools/rtm-db.py admin health-check
curl -f http://localhost:8000/health && echo "✅ Server OK" || echo "❌ Server issue"
pytest tests/unit/ -q --maxfail=1 && echo "✅ Tests OK" || echo "❌ Test failures"
git status | grep -q "nothing to commit" && echo "✅ Git clean" || echo "⚠️ Uncommitted changes"
```

### **Backup Automation**
```bash
# Automated backup (run weekly)
#!/bin/bash
BACKUP_DIR="backups/weekly_$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# RTM data export
python tools/rtm-db.py data export --output "$BACKUP_DIR/rtm_backup.json"

# Code backup
tar -czf "$BACKUP_DIR/code_backup.tar.gz" src/ tests/ tools/ docs/

# Cleanup old backups (keep 4 weeks)
find backups/ -name "weekly_*" -type d -mtime +28 -exec rm -rf {} \;
```

## 🔗 Integration with Other Agents

- **🔧 Daily Development**: [Daily Dev Agent](.claude/daily-dev.md) - Report issues found during development
- **🧪 Test Review**: [Test Review Agent](.claude/test-review.md) - Escalate test failures
- **📚 Documentation**: [Documentation Agent](.claude/documentation.md) - Document emergency procedures
- **🎨 UX/UI**: [UX/UI Agent](.claude/ux-ui-design.md) - Fix critical UI breaking issues

---

**📖 Remember**: This agent handles system emergencies and recovery. For routine troubleshooting, try the appropriate specialized agent first. Use this agent when systems are broken or unresponsive.