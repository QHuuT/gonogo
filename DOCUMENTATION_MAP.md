# 📚 GoNoGo Documentation Map

**Quick navigation guide to find the right documentation for your needs**

---

## 🎯 I Want To...

### **Start Development**
→ **[CLAUDE.md](CLAUDE.md)** - Choose your specialized agent based on task:
- 🔧 **Daily Development** → [`.claude/daily-dev.md`](.claude/daily-dev.md)
- 🧪 **Testing & Code Review** → [`.claude/test-review.md`](.claude/test-review.md)
- 📚 **Documentation** → [`.claude/documentation.md`](.claude/documentation.md)
- 🎨 **UX/UI Design** → [`.claude/ux-ui-design.md`](.claude/ux-ui-design.md)
- 🚨 **Troubleshooting** → [`.claude/emergency.md`](.claude/emergency.md)

### **Understand the Project**
→ **[README.md](README.md)** - Project overview, quick start, features

### **Create or Track Work**
→ **[GitHub Issues](../../issues)** - All active project management
→ **[Issue Templates](../../issues/new/choose)** - Create Epics, User Stories, Defects

### **View Requirements & Traceability**
→ **[RTM Web Dashboard](http://localhost:8000/api/rtm/reports/matrix?format=html)** - Interactive requirements matrix
→ **[quality/RTM_GUIDE.md](quality/RTM_GUIDE.md)** - How to use the RTM dashboard

### **Run Tests**
→ **[quality/TESTING_GUIDE.md](quality/TESTING_GUIDE.md)** - Comprehensive testing workflows
→ **[quality/QUICK_REFERENCE.md](quality/QUICK_REFERENCE.md)** - Quick command reference

### **Fix Issues or Debug**
→ **[quality/TROUBLESHOOTING.md](quality/TROUBLESHOOTING.md)** - Common issues & solutions
→ **[.claude/emergency.md](.claude/emergency.md)** - Emergency recovery procedures
→ **[quality/DATABASE_GUIDE.md](quality/DATABASE_GUIDE.md)** - Database troubleshooting

### **Understand Architecture**
→ **[docs/technical/cross-cutting-architecture/](docs/technical/cross-cutting-architecture/)** - System design
→ **[docs/context/decisions/](docs/context/decisions/)** - Architecture Decision Records (ADRs)

### **Ensure Compliance**
→ **[docs/context/compliance/gdpr-requirements.md](docs/context/compliance/gdpr-requirements.md)** - GDPR requirements
→ **[docs/traceability/gdpr-compliance-map.md](docs/traceability/gdpr-compliance-map.md)** - Compliance mapping

---

## 📂 Documentation by Location

### **Root Directory**
| File | Purpose | When to Use |
|------|---------|-------------|
| **[CLAUDE.md](CLAUDE.md)** | Agent navigation & project overview | Starting any development task |
| **[README.md](README.md)** | Project overview & quick start | First-time project setup |
| **[DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md)** | This file - documentation navigation | Finding the right documentation |

### **Agent Documentation (`.claude/`)**
Specialized task-focused documentation for AI agents and developers:

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **[daily-dev.md](.claude/daily-dev.md)** | Daily coding tasks | 80% of development work |
| **[test-review.md](.claude/test-review.md)** | Testing & code review | Comprehensive testing, PR reviews |
| **[documentation.md](.claude/documentation.md)** | Documentation maintenance | Creating/updating docs |
| **[ux-ui-design.md](.claude/ux-ui-design.md)** | Design & accessibility | UI work, accessibility improvements |
| **[emergency.md](.claude/emergency.md)** | Troubleshooting & recovery | System issues, debugging |

### **Quality Assurance (`quality/`)**
Testing, traceability, and quality documentation:

| File | Purpose | When to Use |
|------|---------|-------------|
| **[RTM_GUIDE.md](quality/RTM_GUIDE.md)** | RTM dashboard user guide | Understanding requirements traceability |
| **[TESTING_GUIDE.md](quality/TESTING_GUIDE.md)** | Comprehensive testing workflows | Running tests, understanding test types |
| **[QUICK_REFERENCE.md](quality/QUICK_REFERENCE.md)** | Quick command cheatsheet | Need commands fast |
| **[DATABASE_GUIDE.md](quality/DATABASE_GUIDE.md)** | Database RTM management | Database RTM operations |
| **[TROUBLESHOOTING.md](quality/TROUBLESHOOTING.md)** | Common issues & solutions | Fixing problems |
| **[README.md](quality/README.md)** | Quality reports overview | Understanding quality reports |

### **Technical Documentation (`docs/technical/`)**
Implementation details and architecture:

| Directory | Purpose | When to Use |
|-----------|---------|-------------|
| **[cross-cutting-architecture/](docs/technical/cross-cutting-architecture/)** | System architecture | Understanding system design |
| **[bdd-scenarios/](docs/technical/bdd-scenarios/)** | BDD test scenarios | Writing executable specifications |
| **[api-docs/](docs/technical/api-docs/)** | API documentation | API reference |
| **[development-workflow.md](docs/technical/development-workflow.md)** | Complete dev workflow | End-to-end development process |
| **[quality-assurance.md](docs/technical/quality-assurance.md)** | Code quality standards | Quality gates and standards |

### **Context Documentation (`docs/context/`)**
Stable decisions and compliance:

| Directory | Purpose | When to Use |
|-----------|---------|-------------|
| **[decisions/](docs/context/decisions/)** | Architecture Decision Records | Understanding why decisions were made |
| **[compliance/](docs/context/compliance/)** | GDPR & legal requirements | Ensuring compliance |

### **Development Tools (`tools/`)**
Scripts and utilities:

| Tool | Purpose | When to Use |
|------|---------|-------------|
| **[rtm-db.py](tools/rtm-db.py)** | RTM database management | Managing RTM data |
| **[sync_github_issues.py](tools/sync_github_issues.py)** | GitHub issue sync | Syncing issues to RTM |
| **[collect_test_functions.py](tools/collect_test_functions.py)** | Test function extraction | Collecting test metadata |

---

## 🔄 Common Workflows

### **New Feature Development**
1. **Plan**: Read [`.claude/daily-dev.md`](.claude/daily-dev.md) → Create [GitHub Issue](../../issues/new/choose)
2. **Implement**: Follow [development workflow](docs/technical/development-workflow.md)
3. **Test**: Use [testing guide](quality/TESTING_GUIDE.md)
4. **Document**: Update with [`.claude/documentation.md`](.claude/documentation.md)
5. **Trace**: Update [RTM dashboard](http://localhost:8000/api/rtm/reports/matrix?format=html)

### **Bug Fix**
1. **Diagnose**: Check [troubleshooting guide](quality/TROUBLESHOOTING.md)
2. **Fix**: Use [`.claude/daily-dev.md`](.claude/daily-dev.md) for commands
3. **Validate**: Run tests per [testing guide](quality/TESTING_GUIDE.md)
4. **Document**: Update defect in [GitHub Issues](../../issues)

### **Code Review**
1. **Review**: Use [`.claude/test-review.md`](.claude/test-review.md)
2. **Test**: Run comprehensive tests
3. **Quality**: Check against [quality standards](docs/technical/quality-assurance.md)

### **Design Changes**
1. **Design**: Use [`.claude/ux-ui-design.md`](.claude/ux-ui-design.md)
2. **Implement**: Switch to [`.claude/daily-dev.md`](.claude/daily-dev.md)
3. **Validate**: Use [`.claude/test-review.md`](.claude/test-review.md)

---

## 📊 Documentation Status

### **Database RTM System** ✅ Active
- **Dashboard**: http://localhost:8000/api/rtm/reports/matrix?format=html
- **Guide**: [quality/RTM_GUIDE.md](quality/RTM_GUIDE.md)
- **Database**: `gonogo.db` (SQLite)
- **Status**: 98.7% data quality, production-ready

### **Test Suite** ✅ Excellent
- **Total Tests**: 482 (426 non-BDD, 56 BDD)
- **Quality Grade**: A+ (99.5% legitimate)
- **Guide**: [quality/TESTING_GUIDE.md](quality/TESTING_GUIDE.md)
- **Analysis**: [test_cleanup_recommendations.md](test_cleanup_recommendations.md)

### **Agent Documentation** ✅ Complete
- **Location**: `.claude/`
- **Status**: 5 specialized agents, task-focused
- **Update**: 2025-09-22 (agent-specialized system)

---

## 🆘 Emergency Quick Reference

### **Server Issues**
```bash
# Kill zombie processes (Windows)
netstat -ano | findstr :8000 && taskkill /F /PID <PID>

# Kill zombie processes (macOS/Linux)
lsof -ti:8000 | xargs kill -9
```

### **Database Issues**
```bash
# Health check
python tools/rtm-db.py admin health-check

# Emergency backup
python tools/rtm-db.py data export --output emergency_backup.json
```

### **Test Failures**
```bash
# Run with verbose output
pytest tests/ -v --tb=short

# Run specific test
pytest tests/path/to/test.py::test_name -v
```

**📖 Full Emergency Procedures**: [.claude/emergency.md](.claude/emergency.md)

---

## 🔗 External Links

- **[GitHub Repository](https://github.com/your-org/gonogo)** - Source code
- **[GitHub Issues](../../issues)** - Project management
- **[RTM Dashboard](http://localhost:8000/api/rtm/reports/matrix?format=html)** - Requirements traceability (requires server running)
- **[DigitalOcean Deployment](https://cloud.digitalocean.com/)** - Production environment

---

## 📝 Documentation Maintenance

### **When to Update This Map**
- ✅ New documentation file created
- ✅ Documentation moved or renamed
- ✅ New workflow added
- ✅ Documentation structure changed

### **How to Update**
1. Edit this file: `DOCUMENTATION_MAP.md`
2. Update relevant agent docs in `.claude/`
3. Update [docs/README.md](docs/README.md) if needed
4. Commit with message: `docs: update documentation map`

---

**📌 Quick Start**: New to the project? Start with [README.md](README.md) → [CLAUDE.md](CLAUDE.md) → Choose your agent → Start coding!

**🎯 Remember**: This is a living document. Keep it updated as documentation evolves.