# 🔧 Daily Development Agent

**Purpose**: Essential commands and workflows for daily coding tasks

## 🚀 Quick Start

### **Setup & Dependencies**
```bash
# Install project dependencies
pip install -e ".[dev]"
pip install jinja2

# Verify installation
python --version
git status
```

### **Server Management**
```bash
# Start development server
python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8000

# Access RTM Web Dashboard (after starting server)
# http://localhost:8000/api/rtm/reports/matrix?format=html

# Kill zombie processes (if port conflicts)
# Windows: netstat -ano | findstr :8000 && taskkill /F /PID <PID>
# macOS/Linux: lsof -ti:8000 | xargs kill -9
```

## 🧪 Essential Testing

### **Quick Testing Commands**
```bash
# Basic test runs (most common)
pytest tests/ -v                    # All tests with verbose output
pytest tests/unit/ -v               # Unit tests only (fastest)
pytest tests/integration/ -v        # Integration tests only

# Test execution modes
pytest --mode=silent tests/         # Minimal output, fastest
pytest --mode=verbose tests/unit/   # Detailed unit test info
pytest --cov=src tests/             # With coverage report
```

### **Test Types by Development Need**
```bash
# During active development
pytest tests/unit/ -v -x            # Stop on first failure
pytest tests/unit/test_specific.py  # Single test file

# Before committing
pytest tests/unit/ tests/integration/ -v  # Core tests
pytest --cov=src tests/ --cov-report=term-missing  # Coverage check

# Pre-PR validation
pytest tests/ -v                    # Full test suite
```

## 🛠️ Code Quality

### **Pre-Commit Quality Gates**
```bash
# Code formatting and linting (run before every commit)
black src/ tests/                   # Format code
isort src/ tests/                   # Sort imports
flake8 src/ tests/                  # Lint code
mypy src/                          # Type checking

# Quick quality check
black src/ tests/ && isort src/ tests/ && flake8 src/ tests/ && mypy src/
```

### **Database Operations**
```bash
# Database migrations
alembic upgrade head                # Apply latest migrations
alembic revision --autogenerate -m "description"  # Create new migration
```

## 📋 GitHub Workflow

### **Issue Management**
```bash
# Check assigned work
gh issue list --assignee @me

# Create new issue with project integration
NEXT_ID=$(python tools/find_next_unused_id.py --type user-story)
gh issue create --title "$NEXT_ID: Description" --label "user-story,priority/medium"

# View specific issue
gh issue view 123
```

### **RTM Integration (Essential Commands)**
```bash
# Quick RTM status check
python tools/rtm-db.py admin health-check

# Sync with GitHub (daily)
python tools/github_sync_manager.py --dry-run     # Preview changes
python tools/github_sync_manager.py               # Full sync

# Essential RTM queries
python tools/rtm-db.py query epics --format table
python tools/rtm-db.py query user-stories --epic-id EP-XXXXX
```

## 📁 Project Structure (Quick Reference)

### **Key Directories**
```
src/
├── be/                 # Backend FastAPI code
│   ├── api/           # API routes
│   ├── models/        # Database models
│   ├── services/      # Business logic
│   └── templates/     # Jinja2 templates
├── shared/            # Shared utilities
└── security/          # GDPR/security code

tests/
├── unit/              # Unit tests (most frequent)
├── integration/       # Integration tests
├── security/          # Security tests
└── bdd/              # BDD scenarios

quality/
├── logs/             # Test execution logs
├── reports/          # Generated reports
└── README.md         # Quality guide
```

### **Common File Patterns**
```bash
# Find files by pattern
find . -name "*.py" -path "*/unit/*"          # Unit test files
find . -name "test_*.py"                       # All test files
find . -name "*_model.py"                      # Database models
find . -name "*_service.py"                    # Business logic
```

## ⚡ Development Workflow

### **Daily Development Cycle**
1. **Start**: Check GitHub issues → `gh issue list --assignee @me`
2. **Code**: Make changes → run unit tests → `pytest tests/unit/ -v`
3. **Quality**: Format code → `black src/ tests/`
4. **Test**: Run relevant tests → `pytest tests/unit/test_specific.py`
5. **Commit**: Reference issue → `git commit -m "feat: implement US-XXXXX"`

### **Pre-Commit Checklist** ✅
- [ ] Unit tests pass: `pytest tests/unit/ -v`
- [ ] Code formatted: `black src/ tests/`
- [ ] Imports sorted: `isort src/ tests/`
- [ ] Linting clean: `flake8 src/ tests/`
- [ ] Types checked: `mypy src/`
- [ ] RTM updated: Reference issue in commit

### **End of Day**
```bash
# Quick status check
git status
python tools/rtm-db.py admin health-check
gh issue list --assignee @me --state open

# Backup important work
git add . && git commit -m "wip: end of day backup"
```

## 🔗 Quick Links

- **🧪 Testing & Review**: See `.claude/test-review.md` for comprehensive testing
- **📚 Documentation**: See `.claude/documentation.md` for doc workflows
- **🎨 UX/UI Design**: See `.claude/ux-ui-design.md` for design tasks
- **🚨 Emergency**: See `.claude/emergency.md` for troubleshooting
- **📖 Main Guide**: See `CLAUDE.md` for project overview

## 💡 Pro Tips

- **Use `pytest -x`** to stop on first failure during development
- **Run unit tests frequently** - they're fast and catch issues early
- **Keep RTM synced** - run GitHub sync at start of day
- **Format on save** - configure your editor to run `black` automatically
- **Check issues daily** - stay aligned with project priorities

---

**🎯 Focus**: This file contains everything needed for productive daily development. For specialized tasks, see other agent files.**