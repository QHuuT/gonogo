# GoNoGo Blog

A GDPR-compliant blog platform with comments, built with FastAPI and designed for quality-focused development.

## 🎯 Project Overview

**GoNoGo** is a personal blog platform featuring:
- FastAPI + Jinja2 templates for Python-centric development
- GDPR-compliant comment system (no authentication required)
- Privacy-by-design architecture
- Comprehensive testing and documentation
- GitHub-integrated project management

## 🏗️ Architecture Overview

### Project Management (GitHub-First)
- **Primary Source**: GitHub Issues with custom templates
- **Issue Types**: Epic, User Story, Defect Report templates in `.github/ISSUE_TEMPLATE/`
- **Automation**: Auto-generated documentation from GitHub Issues
- **Traceability**: Requirements Traceability Matrix (RTM) links to live GitHub Issues

### Documentation Structure
```
📁 Project Structure:
├── .github/                 # GitHub integration & project management
│   ├── ISSUE_TEMPLATE/      # Epic, Story, Defect templates
│   ├── workflows/           # GitHub Actions (future: auto-docs)
│   └── *.md                 # GitHub workflow documentation
├── docs/                    # Documentation (mix of manual + generated)
│   ├── generated/           # Auto-generated from GitHub Issues (future)
│   ├── manual/              # Hand-written guides and decisions
│   └── traceability/        # Requirements Traceability Matrix
├── src/                     # Source code
└── tests/                   # BDD tests + unit/integration tests
```

### Development Approach
- **BDD + RTM Workflow**: Behavior-Driven Development with Requirements Traceability
- **GitHub Integration**: Issues → Code → Tests → Documentation
- **Quality Gates**: Automated testing, linting, type checking
- **GDPR Compliance**: Built-in privacy considerations

## 🚀 Getting Started

### For Development
1. **Check Current Work**: See active [GitHub Issues](../../issues)
2. **Review Workflow**: Read [development workflow guide](docs/technical/development-workflow.md)
3. **Follow BDD Process**: Requirements → Tests → Implementation

### For Project Management
1. **Create Issues**: Use [Issue Templates](../../issues/new/choose)
2. **Track Progress**: Monitor [Project Board](../../projects) (when configured)
3. **Review RTM**: Check [Requirements Matrix](docs/traceability/requirements-matrix.md)

## 📋 Current Status

### MVP Features (Target)
- [x] GitHub workflow integration (US-009)
- [ ] Basic blog post viewing (US-001)
- [ ] GDPR consent system (US-006)
- [ ] Comment system with privacy compliance (US-003)

**Total Scope**: 74 story points across 4 epics
**Current Progress**: Foundation complete, core development ready

### Active Epics
- **EP-001**: Blog Content Management (8 pts)
- **EP-002**: GDPR-Compliant Comment System (16 pts)
- **EP-003**: Privacy and Consent Management (29 pts)
- **EP-004**: GitHub Workflow Integration (21 pts) ✅

## 🛠️ Tech Stack

- **Backend**: FastAPI + Jinja2 templates
- **Database**: SQLite (dev) → PostgreSQL (prod)
- **Frontend**: Server-side rendering + minimal CSS/JS
- **Testing**: pytest + pytest-bdd for executable specifications
- **Deployment**: DigitalOcean App Platform (EU region)
- **CI/CD**: GitHub Actions

## 📖 Key Documentation

### For Developers
- [**Development Workflow**](docs/technical/development-workflow.md) - Project standards and day-to-day process
- [**GitHub Workflow**](.github/GITHUB_WORKFLOW.md) - Issue templates and project management
- [**Requirements Matrix**](docs/traceability/requirements-matrix.md) - Full traceability

### For Stakeholders
- [**Business Requirements**](docs/01-business/README.md) - Epic and user story overview
- **Live Issues**: [GitHub Issues](../../issues) for current work status

## 🔗 Quick Links

- **📋 Create New Work**: [Issue Templates](../../issues/new/choose)
- **📊 Track Progress**: [GitHub Issues](../../issues)
- **📚 Full Documentation**: [docs/](docs/)
- **🔧 Development Guide**: [docs/technical/development-workflow.md](docs/technical/development-workflow.md)

---

**Quality First**: This project emphasizes thorough requirements, comprehensive testing, and GDPR compliance from day one.



