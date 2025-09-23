# 🔧 Daily Development Agent

**Streamlined commands for daily coding tasks**

## 🎯 Agent Purpose
This agent specializes in **80% of daily development work** - server management, basic testing, code quality, commits, and essential RTM operations.

**🔄 For other tasks**: [Agent Navigation](../CLAUDE.md#🤖-agent-navigation)

## ⚡ Quick Start

### **Essential Setup**
```bash
# Install dependencies
pip install -e ".[dev]" && pip install jinja2

# Start development server
python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8000

# Verify server health
curl http://localhost:8000/health || echo "Server not responding"
```

### **RTM Dashboard Access**
```bash
# After starting server, access RTM dashboard:
# http://localhost:8000/api/rtm/reports/matrix?format=html
```

## 🚀 Development Workflow

### **1. Daily Session Start**
```bash
# Check git status and recent commits
git status && git log --oneline -5

# Verify dependencies and RTM health
python tools/rtm-db.py admin health-check

# Check for assigned GitHub issues
gh issue list --assignee @me --state open
```

### **2. Code Development**
```bash
# Start working on issue (replace with actual issue number)
git checkout -b feature/US-XXXXX-description

# Code → Save → Test cycle
pytest tests/unit/ -v --tb=short  # Quick unit tests
pytest tests/integration/ -x     # Stop on first failure

# For specific test files
pytest tests/unit/test_specific.py::test_function -v
```

### **3. Code Quality Gates**
```bash
# Format and lint (run before every commit)
black src/ tests/ && isort src/ tests/
flake8 src/ tests/ --max-line-length=88
mypy src/ --ignore-missing-imports

# Basic security check
bandit -r src/ -f json
```

### **4. RTM Operations**
```bash
# Check epic progress for your user story
python tools/rtm-db.py query epic-progress EP-XXXXX

# Update user story status (after implementation)
python tools/rtm-db.py entities update-user-story US-XXXXX --status completed

# Sync with GitHub (updates from recent issue changes)
python tools/github_sync_manager.py --epic EP-XXXXX --quiet
```

## 📝 Commit & GitHub Workflow

### **Standard Commit Process**
```bash
# Stage changes
git add .

# Commit with proper message format
git commit -m "feat: implement user authentication system

Implements US-00123: Add secure login functionality

- Added password hashing with bcrypt
- Implemented JWT token generation
- Added user session management
- Updated database schema for user table

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to feature branch
git push -u origin feature/US-XXXXX-description
```

### **GitHub Issue Management**
```bash
# View issue details
gh issue view 123

# Comment on issue with progress
gh issue comment 123 --body "Implementation completed. Ready for review."

# Update issue labels
gh issue edit 123 --add-label "status/in-review" --remove-label "status/in-progress"

# Create pull request
gh pr create --title "feat: implement user authentication (US-00123)" \
  --body "Implements user authentication system as described in US-00123"
```

## 🧪 Testing Essentials

### **Quick Test Commands**
```bash
# Essential test runs for daily development
pytest tests/unit/ -v                    # Unit tests (primary focus)
pytest tests/integration/ -x             # Integration tests (stop on fail)
pytest tests/security/ -v                # Security tests (GDPR critical)
pytest tests/ -k "test_authentication"   # Specific functionality

# With coverage (weekly or before PR)
pytest --cov=src tests/ --cov-report=html
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

### **Test Debugging**
```bash
# Debug specific failing test
pytest tests/unit/test_file.py::test_function -v -s --pdb

# Run tests with detailed output (when debugging)
pytest tests/unit/ -v -s --tb=long

# Check test discovery issues
pytest --collect-only tests/
```

## 🗄️ Database Operations

### **Common Database Tasks**
```bash
# Check database status
python tools/rtm-db.py admin health-check

# Apply migrations
alembic upgrade head

# Create new migration (after model changes)
alembic revision --autogenerate -m "add user authentication tables"

# Database backup (before major changes)
python tools/rtm-db.py data export --output backup_$(date +%Y%m%d).json
```

### **RTM Database Quick Operations**
```bash
# Quick entity lookups
python tools/rtm-db.py query epics --format table
python tools/rtm-db.py query user-stories --epic-id EP-XXXXX
python tools/rtm-db.py query user-stories --status in_progress

# Epic progress check
python tools/rtm-db.py query epic-progress EP-XXXXX
```

## 🔧 Server Management

### **Development Server**
```bash
# Start server with reload
python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8000

# Start server in background (when needed)
nohup python -m uvicorn src.be.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# Check if server is running
curl -f http://localhost:8000/health && echo "✅ Server OK" || echo "❌ Server Down"
```

### **Process Management**
```bash
# Find and kill zombie processes (Windows)
netstat -ano | findstr :8000
taskkill /F /PID <PID_NUMBER>

# Find and kill zombie processes (macOS/Linux)
lsof -ti:8000 | xargs kill -9

# Check port usage
netstat -tulpn | grep :8000  # Linux
lsof -i :8000               # macOS
netstat -ano | findstr :8000 # Windows
```

## 🚨 Quick Troubleshooting

### **Common Issues & Solutions**
```bash
# Import errors
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"  # Linux/macOS
set PYTHONPATH=%PYTHONPATH%;%cd%\src          # Windows

# Database connection issues
python tools/rtm-db.py admin health-check
# If fails: check if server is running and database file exists

# Test failures
pytest tests/unit/ -v --tb=short  # Get quick failure summary
pytest tests/ --lf                # Run only last failed tests

# Permission errors (GitHub CLI)
gh auth status
gh auth login  # If not authenticated
```

### **Emergency Reset**
```bash
# Reset development environment
git stash  # Save current work
git checkout main && git pull origin main
pip install -e ".[dev]" && pip install jinja2
python tools/rtm-db.py admin health-check
```

## 📊 Daily Status Check

### **End-of-Session Checklist**
```bash
# 1. Check git status
git status

# 2. Verify all tests pass
pytest tests/unit/ -q

# 3. Check RTM is current
python tools/rtm-db.py admin health-check

# 4. Push any pending work
git push origin feature/current-branch

# 5. Update GitHub issue status
gh issue list --assignee @me --state open
```

## 🔗 Quick Links to Other Agents

- **🧪 Complex Testing**: [Test Review Agent](.claude/test-review.md)
- **📚 Documentation Updates**: [Documentation Agent](.claude/documentation.md)
- **🎨 UI/Design Work**: [UX/UI Agent](.claude/ux-ui-design.md)
- **🚨 System Issues**: [Emergency Agent](.claude/emergency.md)

---

**📖 Remember**: This agent covers daily development essentials. For comprehensive testing, documentation work, or system troubleshooting, switch to the appropriate specialized agent.