# Claude Code Configuration

This file contains configuration and commands for Claude Code to help with development tasks.

## Project Information
- **Project**: gonogo - GDPR-compliant blog with comments
- **Language**: Python
- **Framework**: FastAPI + Jinja2 templates
- **Database**: SQLite (dev) → PostgreSQL (prod)
- **Deployment**: DigitalOcean App Platform (EU)
- **Content**: Markdown-based blog posts

## Tech Stack
- **Backend**: FastAPI + Jinja2 templates
- **Frontend**: Python templates + minimal CSS/JS
- **Database**: SQLAlchemy ORM
- **Testing**: Pytest (unit-focused pyramid)
- **Security**: GDPR-compliant, security headers
- **CI/CD**: GitHub Actions
- **Hosting**: DigitalOcean App Platform (Amsterdam/Frankfurt)

## Setup and Dependencies
```bash
# Install dependencies (required for testing and development)
pip install -e ".[dev]"  # Install project with dev dependencies
pip install jinja2       # Required for report generation
```

## Common Commands
```bash
# Development
python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8000

# Testing (Enhanced Test Runner with Structured Logging)
pytest tests/ -v                    # All tests (standard mode)
pytest --mode=silent --type=all     # All tests, minimal output
pytest --mode=verbose --type=unit   # Unit tests with detailed output
pytest --mode=detailed --type=integration  # Integration tests with full debugging
pytest --type=unit                  # Unit tests only
pytest --type=integration           # Integration tests only
pytest --type=security              # Security tests only
pytest --type=e2e                   # End-to-end tests only
pytest --type=bdd                   # BDD scenarios only
pytest --cov=src tests/             # Coverage report

# Test Execution Modes
# --mode=silent    : Minimal output, fastest execution
# --mode=standard  : Default pytest behavior
# --mode=verbose   : Detailed test information
# --mode=detailed  : Maximum debugging (no output capture, locals shown)

# Test Report Generation (NEW)
python tools/report_generator.py --demo                    # Generate demo report
python tools/report_generator.py --input quality/logs/test_execution.log  # Generate from logs
python tools/report_generator.py --type unit --output quality/reports/    # Filtered reports
python tools/report_generator.py --input quality/logs/ --filename custom_report.html  # Custom output

# Code Quality
black src/ tests/                   # Format code
isort src/ tests/                   # Sort imports
flake8 src/ tests/                  # Lint
mypy src/                          # Type checking

# Database
alembic upgrade head                # Apply migrations
alembic revision --autogenerate     # Create migration

# Production
docker build -t gonogo .
docker-compose up -d                # Local production test
```

## Development Procedures

### 🔄 GitHub-First Development Workflow (ALWAYS follow this)
**📖 Detailed Process**: See [Development Workflow](docs/technical/development-workflow.md)

1. **Plan**: Read CLAUDE.md → Create GitHub issue (Epic/US/DEF) using templates
2. **Code**: Implement changes following project conventions
3. **Test**: Run relevant tests (unit → integration → security)
4. **Quality**: Complete quality gates (linting, type checking, coverage)
5. **Document**: Update RTM and relevant documentation
   - ⚠️ **REMINDER**: Check referenced docs (development-workflow.md, quality-assurance.md, etc.)
6. **Commit**: Reference linked issue in commit message
7. **Trace**: Update Requirements Traceability Matrix with progress

### 📝 Before Every Session (GitHub-First Protocol)
- [ ] Read CLAUDE.md completely
- [ ] Verify dependencies: `pip install -e ".[dev]" && pip install jinja2`
- [ ] Check current git status
- [ ] Review recent commits for context
- [ ] Check [GitHub Issues](../../issues) for assigned work
- [ ] Verify RTM status for any in-progress tasks

### ✅ Before Every Commit (Enhanced Protocol)
**📖 Complete Checklist**: See [Quality Assurance Guidelines](docs/technical/quality-assurance.md#quality-gates)

**Quality Gates**:
- [ ] Run tests: `pytest tests/ -v` (generates structured logs)
- [ ] Generate test report: `python tools/report_generator.py --input quality/logs/`
- [ ] Review test report for any failures or issues
- [ ] Run linting: `black src/ tests/ && isort src/ tests/ && flake8 src/ tests/`
- [ ] Run type checking: `mypy src/`

**Documentation Updates** (⚠️ CRITICAL - Don't forget!):
- [ ] Check if referenced docs need updates when implementing new infrastructure
- [ ] Update docs/technical/development-workflow.md if workflow changes
- [ ] Update docs/technical/quality-assurance.md if testing changes
- [ ] Update docs/technical/documentation-workflow.md if doc process changes

**GitHub Integration & Project Management**:
- [ ] Reference linked GitHub issue in commit message (Implements/Fixes US-XXXXX)
- [ ] Comment on linked issue with implementation details
- [ ] Add BDD scenarios to issue description if created
- [ ] **Update GitHub Project status**: Move from "Backlog" → "In Progress" → "Done"
- [ ] **Update parent/child relationships**: Ensure Epic/US/DEF hierarchy is maintained
- [ ] **Update dependency status**: Mark blocking issues as resolved if applicable

**Documentation & Traceability**:
- [ ] Update RTM with implementation progress and project tracking
- [ ] Validate RTM links if traceability matrix modified
- [ ] Update documentation if needed
- [ ] Update CLAUDE.md if project structure changed
- [ ] **Sync priority mapping**: Ensure issue labels match project priority fields

## Project Structure

```
gonogo/
├── .github/                    # GitHub workflows and templates
│   └── workflows/             # CI/CD automation
├── config/                    # Configuration files
│   ├── environments/          # Environment-specific configs
│   ├── database/             # DB migrations and seeds
│   └── gdpr/                 # GDPR compliance configs
├── content/                  # Blog content (Markdown files)
│   ├── posts/               # Blog post markdown files
│   └── pages/               # Static pages
├── docs/                    # Documentation
│   ├── context/             # Stable decisions & compliance
│   │   ├── decisions/       # Architecture Decision Records (ADRs)
│   │   └── compliance/      # GDPR and legal requirements
│   ├── technical/           # Technical implementation docs
│   │   ├── cross-cutting-architecture/  # System architecture
│   │   ├── development-workflow.md # Development process guide
│   │   ├── documentation-workflow.md # Documentation maintenance
│   │   ├── quality-assurance.md # Code standards and quality
│   │   ├── api-docs/        # API documentation
│   │   └── technical-epics/ # Technical implementation guides
│   ├── user/               # End-user documentation
│   ├── traceability/       # Requirements tracking
│   └── generated/          # Auto-generated from GitHub Issues
├── src/                     # Source code
│   ├── be/                  # Backend (FastAPI)
│   │   ├── api/            # API routes
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   ├── templates/      # Jinja2 templates
│   │   └── main.py         # FastAPI app entry
│   ├── shared/             # Shared utilities
│   │   ├── types/          # Type definitions
│   │   └── utils/          # Common functions
│   └── security/           # Security implementations
│       └── gdpr/           # GDPR compliance tools
├── tests/                   # Test files (pyramid structure)
│   ├── unit/               # Unit tests (most tests here)
│   ├── integration/        # Integration tests
│   ├── security/           # Security tests
│   └── e2e/               # End-to-end tests (minimal)
├── quality/                # Quality assurance and reporting
│   ├── logs/              # Structured test execution logs (JSON)
│   └── reports/           # Generated HTML reports and assets
│       ├── templates/     # Jinja2 HTML report templates
│       └── assets/        # CSS, JS, and static assets
├── tools/                  # Development tools and scripts
├── static/                 # Static assets (CSS, JS, images)
├── docker-compose.yml      # Local development
├── Dockerfile             # Production container
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Python project configuration
└── CLAUDE.md              # This file
```

## Documentation Quick Reference

### 📖 **Detailed Workflows & Guidelines**
- **[Development Workflow](docs/technical/development-workflow.md)** - Complete BDD + RTM development process
- **[Documentation Workflow](docs/technical/documentation-workflow.md)** - How to maintain all documentation
- **[GitHub Issue Creation](docs/technical/github-issue-creation.md)** - Step-by-step issue creation with error solutions
- **[Quality Assurance](docs/technical/quality-assurance.md)** - Code standards, testing, and quality gates

### 🎯 **Context & Decisions**
- **[Architecture Decisions](docs/context/decisions/)** - ADRs for major technical and business decisions
- **[GDPR Requirements](docs/context/compliance/gdpr-requirements.md)** - Privacy compliance requirements

### 🏗️ **Technical Architecture**
- **[System Architecture](docs/technical/cross-cutting-architecture/system-architecture.md)** - Overall system design
- **[Security Architecture](docs/technical/cross-cutting-architecture/security-architecture.md)** - Security and GDPR implementation
- **[Integration Patterns](docs/technical/cross-cutting-architecture/integration-patterns.md)** - Service communication

### 🔗 **Project Management**
- **[GitHub Issues](../../issues)** - Active project management (EP-XXX, US-XXX, DEF-XXX)
- **[Requirements Matrix](docs/traceability/requirements-matrix.md)** - GitHub Issues → Implementation traceability
- **[Documentation Hub](docs/README.md)** - Complete documentation overview

## 📊 **Test Execution and Reporting Workflow**

### **Standard Test Execution with Logging**
```bash
# 1. Run tests with structured logging
pytest --type=unit --mode=verbose     # Logs to quality/logs/test_execution.log

# 2. Generate HTML report
python tools/report_generator.py --input quality/logs/test_execution.log

# 3. View report (opens in browser)
open quality/reports/test_report.html  # macOS
start quality/reports/test_report.html # Windows
```

### **Advanced Reporting Features**
- **Interactive Filtering**: Filter by status, test type, search terms
- **Timeline Visualization**: See test execution patterns over time
- **Failure Analysis**: Categorized error patterns and debugging info
- **Export Capabilities**: CSV export for external analysis
- **GDPR Compliance**: Personal data sanitization in logs

### **Report Customization**
- **Templates**: Modify `quality/reports/templates/main_report.html`
- **Styling**: Edit `quality/reports/assets/report.css`
- **Interactivity**: Extend `quality/reports/assets/report.js`

### **Debugging and Troubleshooting**
```bash
# Debug test failures with detailed mode
pytest --mode=detailed --type=unit tests/unit/test_specific.py

# Check structured logs for debugging
cat quality/logs/test_execution.log | grep "error\|failed"

# Generate focused reports
python tools/report_generator.py --type integration --input quality/logs/

# Validate GDPR sanitization
grep -i "email\|ip.*address" quality/logs/test_*.log  # Should show [REDACTED]

# Common Issues and Solutions
# 1. Missing dependencies: pip install -e ".[dev]" && pip install jinja2
# 2. No logs generated: Run pytest first to create logs
# 3. Empty reports: Check that tests actually ran (look for test_*.log files)
# 4. Template errors: Verify templates exist in quality/reports/templates/
```

## Development Guidelines Summary

### 🐍 **Code Standards**
**📖 Complete Guidelines**: See [Quality Assurance](docs/technical/quality-assurance.md)

- **Formatting**: Black (line length 88), isort, flake8, mypy
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Functions**: Small (20 lines max), single responsibility, 0-2 arguments ideal

### 🛡️ **Security & GDPR**
**📖 Detailed Requirements**: See [GDPR Requirements](docs/context/compliance/gdpr-requirements.md)

- **Never log personal data** (emails, IPs after anonymization)
- **Always require consent** for data collection
- **Implement data retention** policies
- **Use secure headers** in all responses
- **Validate all inputs** and sanitize outputs

### 🧪 **Testing Strategy**
**📖 Complete Strategy**: See [Quality Assurance - Testing](docs/technical/quality-assurance.md#testing-strategy)

- **Unit tests**: 70% (fast, isolated, mock dependencies)
- **Integration tests**: 20% (database, external services)
- **E2E tests**: 10% (critical user flows only)
- **Security tests**: Always test GDPR compliance and input validation

### 📝 **Commit Messages**
**📖 Detailed Standards**: See [Quality Assurance - Commit Messages](docs/technical/quality-assurance.md#commit-message-standards)

```
feat: add comment system with GDPR consent
fix: resolve SQL injection in search
docs: update deployment instructions
test: add unit tests for blog post service
```

## Quick Start Checklist

### **🚀 Enhanced Development Session Protocol**
1. [ ] Read CLAUDE.md (this file) completely
2. [ ] Check [GitHub Issues](../../issues) for assigned work
3. [ ] **PLAN**: For any new task, create GitHub issue with full project integration:
   - **📖 Detailed Guide**: See [GitHub Issue Creation Guide](docs/technical/github-issue-creation.md)
   - **Check existing IDs first**: `gh issue list --limit 50 --state all | grep -E "(EP-|US-|DEF-)"`
   - **Set up project integration**: `export GONOGO_PROJECT_ID=$(gh project list --owner QHuuT --json number,title | jq -r '.[] | select(.title=="GoNoGo") | .number')`
   - **Create issue + add to project**:
     ```bash
     ISSUE_URL=$(gh issue create --title "US-XXXXX: Title" --body "**Parent Epic**: EP-XXXXX\n**Dependencies**:\n- Blocks: #X\n- Blocked by: #Y" --label "user-story,priority/medium")
     gh project item-add $GONOGO_PROJECT_ID --url $ISSUE_URL
     ```
   - **Set hierarchical relationships**: Epic → User Story → Defect
   - **Document dependencies**: "Blocks #X" or "Blocked by #Y" relationships
4. [ ] Review [Development Workflow](docs/technical/development-workflow.md) for task-specific processes
5. [ ] Check [Requirements Matrix](docs/traceability/requirements-matrix.md) for current status
6. [ ] Verify [GDPR implications](docs/context/compliance/gdpr-requirements.md) if handling personal data

### **✅ Enhanced Commit Protocol with Project Integration**
1. [ ] Complete all quality gates (tests, linting, type checking)
2. [ ] **COMMIT**: Reference linked GitHub issue (e.g., "Implements US-00018")
3. [ ] **COMMENT**: Update linked issue with implementation details
4. [ ] **PROJECT**: Update GitHub Project status and priority if needed
5. [ ] **TRACE**: Update RTM with progress/completion status and project links
6. [ ] **BDD**: Add any created scenarios to issue description
7. [ ] **DEPENDENCIES**: Update dependency status if issue blocks/unblocks others
8. [ ] Follow [Conventional Commit](docs/technical/quality-assurance.md#commit-message-standards) format

---

**📌 Remember**: This file provides quick reference and commands. For detailed processes, workflows, and guidelines, see the linked documentation in `docs/`.