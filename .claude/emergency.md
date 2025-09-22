# 🚨 Emergency & Troubleshooting Agent

**Purpose**: System recovery, troubleshooting, and emergency procedures

## 🆘 Quick Emergency Commands

### **Server Issues**
```bash
# Kill zombie server processes
# Windows
netstat -ano | findstr :8000                    # Find process using port 8000
taskkill /F /PID <PID_NUMBER>                   # Kill specific process
wmic process where "name='python.exe' and commandline like '%uvicorn%'" delete  # Nuclear option

# PowerShell
Get-Process python* | Stop-Process -Force       # Kill all Python processes

# macOS/Linux
lsof -ti:8000 | xargs kill -9                   # Kill process on port 8000
pkill -f uvicorn                                # Kill uvicorn processes

# Verify port is free
netstat -ano | findstr :8000                    # Windows
lsof -i :8000                                   # macOS/Linux
```

### **Database Recovery**
```bash
# Database health check
python tools/rtm-db.py admin health-check       # Check database connectivity
python tools/rtm-db.py admin validate          # Validate data integrity

# Database backup
python tools/rtm-db.py data export --output emergency_backup.json  # Export all data

# Database reset (DANGEROUS - last resort)
python tools/rtm-db.py admin reset --confirm   # Reset database (delete all data)

# Database migration issues
alembic downgrade -1                            # Rollback one migration
alembic upgrade head                            # Apply latest migrations
```

## 🔥 Test Failure Recovery

### **Mass Test Failures**
```bash
# Quick test failure analysis
pytest tests/ -v --tb=short                    # Run tests with short traceback
pytest tests/ --lf                             # Run only last failed tests
pytest tests/ -x                               # Stop on first failure

# Test failure debugging
pytest tests/unit/test_specific.py --pdb       # Drop into debugger
pytest tests/unit/test_specific.py -s          # No output capture
pytest --mode=detailed tests/unit/test_specific.py  # Maximum debugging

# Test environment reset
rm -rf quality/logs/*                          # Clear test logs
rm -rf .pytest_cache/                          # Clear pytest cache
python tools/test-db-integration.py discover tests  # Re-sync test database
```

### **Test Database Issues**
```bash
# Test database inspection
python tools/db_inspector.py                   # Overview of all databases
python tools/db_inspector.py --db quality/logs/test_failures.db  # Examine test failures

# Test discovery issues
python tools/test-db-integration.py discover tests --dry-run  # Preview test discovery
python tools/test-db-integration.py status overview  # Check integration status

# Re-sync test-database integration
python tools/test-db-integration.py discover tests  # Re-discover all tests
python tools/test-db-integration.py discover scenarios  # Re-link BDD scenarios
```

## 🗄️ Storage & Archive Recovery

### **Storage Issues**
```bash
# Check storage usage
python tools/archive_cleanup.py --metrics      # Storage analysis
df -h .                                        # Disk usage (Unix)
dir /s quality\                               # Directory size (Windows)

# Emergency cleanup
python tools/archive_cleanup.py --apply        # Apply retention policies
rm -rf quality/logs/old_*                     # Manual log cleanup
rm -rf quality/reports/old_*                  # Manual report cleanup

# Archive management
python tools/archive_cleanup.py --search "pattern"  # Search archives
python tools/archive_cleanup.py --bundle emergency  # Create emergency bundle
```

### **File Recovery**
```bash
# Git recovery
git status                                     # Check current state
git log --oneline -10                         # Recent commits
git checkout HEAD~1 -- path/to/file           # Restore file from previous commit
git reflog                                     # View all git operations

# Backup restoration
cp emergency_backup.json quality/backup/      # Copy backup to safe location
python tools/rtm-db.py data import emergency_backup.json  # Restore from backup
```

## 🔧 System Diagnostics

### **Environment Diagnostics**
```bash
# Python environment check
python --version                               # Python version
pip list | grep -i pytest                     # Pytest version
pip list | grep -i fastapi                    # FastAPI version
pip check                                     # Check for broken dependencies

# System resources
# Windows
tasklist | findstr python                     # Running Python processes
wmic process get name,processid,workingsetsize | findstr python  # Memory usage

# macOS/Linux
ps aux | grep python                          # Running Python processes
top -p $(pgrep python)                        # Process monitoring
```

### **Network & Port Issues**
```bash
# Port diagnostics
netstat -ano | findstr :8000                  # Windows port check
ss -tulpn | grep :8000                        # Linux port check
lsof -i :8000                                 # macOS port check

# Network connectivity
curl http://localhost:8000/health             # Test health endpoint
ping localhost                                # Basic connectivity
nslookup localhost                             # DNS resolution
```

## 🚨 Critical System Recovery

### **Complete Environment Reset**
```bash
# WARNING: This will reset your development environment
# 1. Stop all processes
pkill -f python                               # Kill all Python processes
pkill -f uvicorn                              # Kill all uvicorn processes

# 2. Clean Python environment
pip uninstall -r requirements.txt -y          # Uninstall all packages
pip install -e ".[dev]"                       # Reinstall project
pip install jinja2                            # Reinstall required packages

# 3. Reset databases
python tools/rtm-db.py admin reset --confirm  # Reset RTM database
rm -rf quality/logs/*                         # Clear logs

# 4. Reinitialize system
python tools/test-db-integration.py discover tests  # Rediscover tests
python tools/github_sync_manager.py           # Sync with GitHub
python tools/rtm-db.py admin health-check     # Verify health
```

### **Git Repository Recovery**
```bash
# Repository corruption recovery
git status                                    # Check repository state
git fsck                                      # Check repository integrity

# Reset to known good state
git log --oneline -10                         # Find good commit
git reset --hard <commit-hash>                # Reset to specific commit
git clean -fd                                 # Remove untracked files

# Branch recovery
git branch -a                                 # List all branches
git checkout main                             # Switch to main branch
git pull origin main                          # Update from remote
```

## 🔍 Debugging Workflows

### **RTM System Debugging**
```bash
# RTM debugging
python tools/rtm-db.py admin health-check     # Database health
python tools/rtm-db.py admin validate         # Data validation
python tools/github_sync_manager.py --dry-run --validate  # GitHub sync validation

# RTM web dashboard debugging
python -m uvicorn src.be.main:app --reload --log-level debug  # Debug server
curl -v http://localhost:8000/api/rtm/reports/matrix  # Test API endpoint

# RTM report generation debugging
python tools/rtm_report_generator.py --html --verbose  # Verbose report generation
```

### **Testing System Debugging**
```bash
# Test system debugging
pytest --collect-only                         # Show collected tests without running
pytest tests/unit/ --setup-show               # Show test setup/teardown
pytest tests/unit/ --fixtures                 # Show available fixtures

# Test database debugging
python tools/test-db-integration.py utils analyze --show-orphaned  # Find orphaned tests
python tools/db_inspector.py --db quality/logs/test_failures.db --interactive  # Interactive debugging
```

## 📞 Escalation Procedures

### **When to Escalate**
- **Data Loss**: Any indication of data corruption or loss
- **Security Issues**: Potential security vulnerabilities discovered
- **System Corruption**: Git repository corruption
- **Performance Degradation**: System becoming unusable
- **Dependency Conflicts**: Unable to resolve package conflicts

### **Information to Collect**
```bash
# System information
python --version                               # Python version
pip list                                       # Installed packages
git status                                     # Git repository state
git log --oneline -5                          # Recent commits

# Error information
pytest tests/ -v --tb=long > error_log.txt    # Full test output
python tools/rtm-db.py admin health-check > health_log.txt  # Health check output

# System logs
# Collect relevant log files from quality/logs/
# Include any error messages or stack traces
```

## 🔗 Cross-Agent References

- **🔧 Daily Development**: See `.claude/daily-dev.md` for normal operations
- **🧪 Testing & Review**: See `.claude/test-review.md` for test troubleshooting
- **📚 Documentation**: See `.claude/documentation.md` for documentation issues
- **🎨 UX/UI Design**: See `.claude/ux-ui-design.md` for UI troubleshooting
- **📖 Main Guide**: See `CLAUDE.md` for project overview

## ⚠️ Safety Guidelines

### **Before Taking Action**
- **Backup Critical Data**: Always backup before destructive operations
- **Understand Impact**: Know what each command does before running
- **Test in Safe Environment**: Use `--dry-run` flags when available
- **Document Steps**: Keep track of what you've tried
- **Know When to Stop**: Don't make things worse

### **Recovery Principles**
- **Least Destructive First**: Try minimal fixes before drastic measures
- **One Change at a Time**: Don't combine multiple fixes
- **Verify Success**: Test that fixes actually work
- **Document Solution**: Record what worked for future reference
- **Review Cause**: Understand why the problem occurred

---

**🎯 Focus**: This file provides emergency procedures and troubleshooting workflows. Use when normal operations fail and system recovery is needed.**