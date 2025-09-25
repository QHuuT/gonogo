# GoNoGo Documentation Map

Quick navigation guide to find the right documentation for your needs.

---

## I Want To...

### Start Development
- [docs/technical/development-workflow.md](docs/technical/development-workflow.md) – End-to-end engineering workflow
- [quality/TESTING_GUIDE.md](quality/TESTING_GUIDE.md) – Test strategy and commands
- [quality/QUICK_REFERENCE.md](quality/QUICK_REFERENCE.md) – Common development commands

### Understand the Project
- [README.md](README.md) – Project overview, quick start, features
- [docs/README.md](docs/README.md) – Full documentation index

### Create or Track Work
- [GitHub Issues](../../issues) – Active project management
- [Issue Templates](../../issues/new/choose) – Create Epics, User Stories, Defects

### View Requirements & Traceability
- [RTM Web Dashboard](http://localhost:8000/api/rtm/reports/matrix?format=html) – Interactive requirements matrix
- [quality/RTM_GUIDE.md](quality/RTM_GUIDE.md) – How to use the RTM dashboard

### Run Tests
- [quality/TESTING_GUIDE.md](quality/TESTING_GUIDE.md) – Comprehensive testing workflows
- [quality/QUICK_REFERENCE.md](quality/QUICK_REFERENCE.md) – Quick command reference

### Fix Issues or Debug
- [quality/TROUBLESHOOTING.md](quality/TROUBLESHOOTING.md) – Common issues & solutions
- [quality/DATABASE_GUIDE.md](quality/DATABASE_GUIDE.md) – Database troubleshooting

### Understand Architecture
- [docs/technical/cross-cutting-architecture/](docs/technical/cross-cutting-architecture/) – System design
- [docs/context/decisions/](docs/context/decisions/) – Architecture Decision Records (ADRs)

### Ensure Compliance
- [docs/context/compliance/gdpr-requirements.md](docs/context/compliance/gdpr-requirements.md) – GDPR requirements
- [docs/traceability/gdpr-compliance-map.md](docs/traceability/gdpr-compliance-map.md) – Compliance mapping

---

## Documentation by Location

### Root Directory
| File | Purpose | When to Use |
|------|---------|-------------|
| [README.md](README.md) | Project overview & quick start | First-time project setup |
| [DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md) | Documentation navigation | Finding the right documentation |

### Quality Assurance (quality/)
Testing, traceability, and quality documentation:

| File | Purpose | When to Use |
|------|---------|-------------|
| [RTM_GUIDE.md](quality/RTM_GUIDE.md) | RTM dashboard user guide | Understanding requirements traceability |
| [TESTING_GUIDE.md](quality/TESTING_GUIDE.md) | Comprehensive testing workflows | Running tests, understanding test types |
| [QUICK_REFERENCE.md](quality/QUICK_REFERENCE.md) | Quick command cheatsheet | Need commands fast |
| [DATABASE_GUIDE.md](quality/DATABASE_GUIDE.md) | Database RTM management | Database RTM operations |
| [TROUBLESHOOTING.md](quality/TROUBLESHOOTING.md) | Common issues & solutions | Fixing problems |
| [README.md](quality/README.md) | Quality reports overview | Understanding quality reports |

### Technical Documentation (docs/technical/)
Implementation details and architecture:

| Directory | Purpose | When to Use |
|-----------|---------|-------------|
| [cross-cutting-architecture/](docs/technical/cross-cutting-architecture/) | System architecture | Understanding system design |
| [bdd-scenarios/](docs/technical/bdd-scenarios/) | BDD test scenarios | Writing executable specifications |
| [api-docs/](docs/technical/api-docs/) | API documentation | API reference |
| [development-workflow.md](docs/technical/development-workflow.md) | Complete dev workflow | End-to-end development process |
| [quality-assurance.md](docs/technical/quality-assurance.md) | Code quality standards | Quality gates and standards |
| [documentation-workflow.md](docs/technical/documentation-workflow.md) | Documentation process | Maintaining documentation |
| [github-issue-creation.md](docs/technical/github-issue-creation.md) | Issue management workflow | Creating and updating issues correctly |

### Context Documentation (docs/context/)
Stable decisions and compliance:

| Directory | Purpose | When to Use |
|-----------|---------|-------------|
| [decisions/](docs/context/decisions/) | Architecture Decision Records | Understanding why decisions were made |
| [compliance/](docs/context/compliance/) | GDPR & legal requirements | Ensuring compliance |

### Development Tools (	ools/)
Scripts and utilities:

| Tool | Purpose | When to Use |
|------|---------|-------------|
| [rtm-db.py](tools/rtm-db.py) | RTM database management | Managing RTM data |
| [github_sync_manager.py](tools/github_sync_manager.py) | GitHub issue sync | Syncing issues to RTM |
| [collect_test_functions.py](tools/collect_test_functions.py) | Test function extraction | Collecting test metadata |

---

## Common Workflows

### New Feature Development
1. Plan: review [development workflow](docs/technical/development-workflow.md) and create a [GitHub Issue](../../issues/new/choose)
2. Implement: follow engineering steps in the development workflow guide
3. Test: run suites from the [testing guide](quality/TESTING_GUIDE.md)
4. Document: update relevant guides listed above
5. Trace: sync progress with the [RTM dashboard](http://localhost:8000/api/rtm/reports/matrix?format=html)

### Bug Fix
1. Diagnose: check the [troubleshooting guide](quality/TROUBLESHOOTING.md)
2. Fix: apply the development workflow
3. Validate: run targeted tests
4. Document: update the associated GitHub issue

### Code Review
1. Review: follow the expectations in [quality-assurance.md](docs/technical/quality-assurance.md)
2. Test: execute the suites defined in the testing guide
3. Report: capture findings in the relevant GitHub issue or pull request

### Design Changes
1. Research: consult design guidelines in docs/ (e.g., accessibility, UI standards)
2. Implement: follow the development workflow
3. Validate: run regression and accessibility checks as needed

---

## Documentation Status

### Database RTM System — Active
- Dashboard: http://localhost:8000/api/rtm/reports/matrix?format=html
- Guide: [quality/RTM_GUIDE.md](quality/RTM_GUIDE.md)
- Database: gonogo.db (SQLite)
- Status: 98.7% data quality, production-ready

### Test Suite — Excellent
- Total Tests: 482 (426 non-BDD, 56 BDD)
- Quality Grade: A+ (99.5% legitimate)
- Guide: [quality/TESTING_GUIDE.md](quality/TESTING_GUIDE.md)
- Analysis: [test_cleanup_recommendations.md](test_cleanup_recommendations.md)

---

## Emergency Quick Reference

### Server Issues
`
# Kill zombie processes (Windows)
netstat -ano | findstr :8000 && taskkill /F /PID <PID>

# Kill zombie processes (macOS/Linux)
lsof -ti:8000 | xargs kill -9
`

### Database Issues
`
# Health check
python tools/rtm-db.py admin health-check

# Emergency backup
python tools/rtm-db.py data export --output emergency_backup.json
`

### Test Failures
`
# Run with verbose output
pytest tests/ -v --tb=short

# Run specific test
pytest tests/path/to/test.py::test_name -v
`

More troubleshooting detail: [quality/TROUBLESHOOTING.md](quality/TROUBLESHOOTING.md)

---

## External Links

- [GitHub Repository](https://github.com/your-org/gonogo) – Source code
- [GitHub Issues](../../issues) – Project management
- [RTM Dashboard](http://localhost:8000/api/rtm/reports/matrix?format=html) – Requirements traceability (requires server running)
- [DigitalOcean Deployment](https://cloud.digitalocean.com/) – Production environment

---

## Documentation Maintenance

### When to Update This Map
- New documentation file created
- Documentation moved or renamed
- New workflow added
- Documentation structure changed

### How to Update
1. Edit this file: DOCUMENTATION_MAP.md
2. Update supporting references in docs/
3. Update [docs/README.md](docs/README.md) if needed
4. Commit with message: docs: update documentation map

---

Quick start: begin with [README.md](README.md) ? [docs/technical/development-workflow.md](docs/technical/development-workflow.md) ? run tests with [quality/TESTING_GUIDE.md](quality/TESTING_GUIDE.md).

This is a living document—keep it accurate as the project evolves.
