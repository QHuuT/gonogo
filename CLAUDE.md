# Claude Code Configuration

**Agent-Specialized Documentation for the GoNoGo Project**

## 🎯 Project Overview

- **Project**: gonogo - GDPR-compliant blog with comments
- **Language**: Python
- **Framework**: FastAPI + Jinja2 templates
- **Database**: SQLite (dev) → PostgreSQL (prod)
- **Deployment**: DigitalOcean App Platform (EU)
- **Content**: Markdown-based blog posts

### **Tech Stack**
- **Backend**: FastAPI + Jinja2 templates
- **Frontend**: Python templates + minimal CSS/JS
- **Database**: SQLAlchemy ORM
- **Testing**: Pytest (unit-focused pyramid)
- **Security**: GDPR-compliant, security headers
- **CI/CD**: GitHub Actions
- **Hosting**: DigitalOcean App Platform (Amsterdam/Frankfurt)

## 🤖 Agent Navigation

**Choose your specialized agent based on your current task:**

### **🔧 Daily Development Agent**
**Use when**: Coding, daily development tasks, basic testing
**File**: [`.claude/daily-dev.md`](.claude/daily-dev.md)
**Contains**: Server commands, basic testing, code quality, GitHub workflow, RTM essentials

### **🧪 Code Review & Testing Agent**
**Use when**: Comprehensive testing, code reviews, quality analysis
**File**: [`.claude/test-review.md`](.claude/test-review.md)
**Contains**: All testing modes, coverage analysis, failure debugging, RTM test integration

### **📚 Documentation Agent**
**Use when**: Creating/updating docs, maintaining cross-references
**File**: [`.claude/documentation.md`](.claude/documentation.md)
**Contains**: Documentation workflows, RTM documentation, style guides, link management

### **🎨 UX/UI Design & Accessibility Agent**
**Use when**: Design tasks, accessibility improvements, UI harmonization
**File**: [`.claude/ux-ui-design.md`](.claude/ux-ui-design.md)
**Contains**: Design system, accessibility standards, RTM dashboard design, component library

### **🚨 Emergency & Troubleshooting Agent**
**Use when**: System issues, debugging, recovery procedures
**File**: [`.claude/emergency.md`](.claude/emergency.md)
**Contains**: Server recovery, test failure debugging, database recovery, system diagnostics

## ⚡ Quick Setup

### **Dependencies**
```bash
# Install dependencies (required for all agents)
pip install -e ".[dev]"  # Install project with dev dependencies
pip install jinja2       # Required for report generation
```

### **Essential Commands**
```bash
# Start development server
python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8000

# RTM Web Dashboard (after starting server)
# Access: http://localhost:8000/api/rtm/reports/matrix?format=html

# Basic test run
pytest tests/ -v

# RTM health check
python tools/rtm-db.py admin health-check
```

## 🆘 Emergency Commands

**For immediate system issues (detailed procedures in** [`.claude/emergency.md`](.claude/emergency.md)**)**

### **Kill Zombie Processes**
```bash
# Windows
netstat -ano | findstr :8000 && taskkill /F /PID <PID>

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

### **Database Recovery**
```bash
# Health check
python tools/rtm-db.py admin health-check

# Emergency backup
python tools/rtm-db.py data export --output emergency_backup.json
```

## 📊 Recent Updates

### **2025-09-22**: Agent-Specialized Documentation System
- ✅ **Agent Navigation**: Specialized documentation for different agent types
- ✅ **Daily Development**: Streamlined commands for daily coding tasks
- ✅ **Testing & Review**: Comprehensive testing workflows (no auto-defects)
- ✅ **Documentation**: Complete documentation maintenance workflows
- ✅ **UX/UI Design**: Design system and accessibility standards
- ✅ **Emergency**: Troubleshooting and recovery procedures
- **Focus**: Reduced cognitive load with task-specific documentation

### **2025-09-22**: RTM Migration to Database-Only System (US-00060)
- ✅ **Complete migration from file-based to database RTM**
- ✅ Interactive web dashboard at http://localhost:8000/api/rtm/reports/matrix?format=html
- ✅ Real-time GitHub issue synchronization and progress tracking
- ✅ Comprehensive documentation updated with database RTM workflow
- ✅ Legacy markdown RTM deprecated in favor of dynamic database system
- **RTM Status**: Database RTM is now the single source of truth

## 🗂️ Project Structure (Quick Reference)

```
gonogo/
├── .claude/                   # Agent-specialized documentation
│   ├── daily-dev.md          # 🔧 Daily development commands
│   ├── test-review.md        # 🧪 Testing and code review
│   ├── documentation.md      # 📚 Documentation workflows
│   ├── ux-ui-design.md       # 🎨 Design and accessibility
│   └── emergency.md          # 🚨 Troubleshooting procedures
├── src/                      # Source code
│   ├── be/                   # Backend (FastAPI)
│   ├── shared/               # Shared utilities
│   └── security/             # GDPR/security code
├── tests/                    # Test files (pyramid structure)
│   ├── unit/                 # Unit tests (most tests here)
│   ├── integration/          # Integration tests
│   ├── security/             # Security tests
│   └── e2e/                  # End-to-end tests (minimal)
├── quality/                  # Quality assurance and reporting
│   ├── RTM_GUIDE.md          # RTM dashboard user guide
│   ├── TESTING_GUIDE.md      # Comprehensive testing guide
│   └── README.md             # Quality reports guide
├── docs/                     # Documentation
│   ├── technical/            # Technical implementation docs
│   ├── context/              # Stable decisions & compliance
│   └── legacy/               # Deprecated files
└── tools/                    # Development tools and scripts
```

## 📚 Documentation Quick Reference

### **Essential Guides**
- **[RTM User Guide](quality/RTM_GUIDE.md)** - Complete RTM dashboard usage
- **[Testing Guide](quality/TESTING_GUIDE.md)** - Comprehensive testing workflows
- **[Development Workflow](docs/technical/development-workflow.md)** - Complete development process
- **[Quality Assurance](docs/technical/quality-assurance.md)** - Code standards and quality gates

### **Project Management**
- **[GitHub Issues](../../issues)** - Active project management (EP-XXX, US-XXX, DEF-XXX)
- **[RTM Web Dashboard](http://localhost:8000/api/rtm/reports/matrix?format=html)** - Interactive requirements traceability
- **[Documentation Hub](docs/README.md)** - Complete documentation overview

## 🔄 GitHub-First Development Workflow

**📖 Detailed Process**: See [Development Workflow](docs/technical/development-workflow.md)

1. **Plan**: Read agent docs → Create GitHub issue using templates
2. **Code**: Implement changes following project conventions
3. **Test**: Run relevant tests (see testing agent for comprehensive options)
4. **Quality**: Complete quality gates (linting, type checking, coverage)
5. **Document**: Update RTM and relevant documentation
6. **Commit**: Reference linked issue in commit message
7. **Trace**: Update Requirements Traceability Matrix with progress

## 💡 Agent Usage Tips

### **Choosing the Right Agent**
- **🔧 Daily Dev**: For 80% of development work - server, basic tests, commits
- **🧪 Test Review**: For comprehensive testing, PR reviews, quality analysis
- **📚 Documentation**: For creating/updating any documentation
- **🎨 UX/UI**: For design work, accessibility improvements, UI consistency
- **🚨 Emergency**: When things break and you need recovery procedures

### **Cross-Agent Workflows**
- **New Feature**: Start with Daily Dev → Use Testing for validation → Update with Documentation
- **Bug Fix**: Start with Emergency for diagnosis → Daily Dev for fix → Testing for validation
- **Design Change**: Start with UX/UI for design → Daily Dev for implementation → Testing for validation

## ⚠️ Important Notes

- **No Auto-Defects**: All agent documentation excludes auto-defect creation commands per user request
- **Database RTM Only**: All RTM references point to database system, not legacy files
- **Agent Focus**: Each agent file is optimized for specific tasks to reduce cognitive load
- **Cross-References**: All agents link to each other for comprehensive workflows

---

**🎯 Start Here**: Choose your agent based on your current task. Each agent provides focused, task-specific documentation to maximize productivity and minimize confusion.**

**📖 Remember**: This file provides project overview and agent navigation. For detailed commands and workflows, always refer to the appropriate agent documentation.**