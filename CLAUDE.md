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

## Recent Updates
- **2025-09-20**: EP-00006 stabilization completed
  - ✅ Fixed GitHub label mapper test mocking issues (2 tests restored)
  - ✅ Resolved DEF-00007 RTM namespace collision with direct module loading
  - ✅ Disabled DEF-00006 log_failure_correlator test pending complex import resolution
  - ✅ Archive manager fully validated with comprehensive demo
  - **Test Status**: 125+ tests passing, robust stabilization achieved

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

# Test Report Generation with Coverage Integration (NEW)
python tools/report_generator.py --demo                    # Generate demo report with coverage
python tools/report_generator.py --input quality/logs/test_execution.log  # Generate from logs
python tools/report_generator.py --type unit --output quality/reports/    # Filtered reports
python tools/report_generator.py --input quality/logs/ --filename custom_report.html  # Custom output

# Quality Reports Guide - 📚 COMPREHENSIVE DOCUMENTATION
# See quality/README.md for detailed guide to all report types
# See quality/QUICK_REFERENCE.md for common commands and quality thresholds
# See quality/DATABASE_INSPECTION_GUIDE.md for SQLite database examination

# Database Inspection (NEW)
python tools/db_inspector.py                                    # Overview of all SQLite databases
python tools/db_inspector.py --db quality/logs/test_failures.db # Examine specific database
python tools/db_inspector.py --db quality/logs/test_failures.db --interactive  # Interactive browser mode

# Test Failure Tracking and Analysis (NEW)
python tools/failure_tracking_demo.py                      # Generate failure analysis with sample data
# View: quality/reports/failure_analysis_report.html (interactive failure dashboard)
# View: quality/reports/failure_summary_daily.json (failure statistics)

# Log-Failure Correlation for Debugging (NEW)
python tools/log_correlation_demo.py                       # Generate correlation analysis
# View: quality/reports/log_correlation_report.json (correlation data)
# View: quality/reports/reproduction_script_*.py (auto-generated debug scripts)

# GitHub Issue Creation from Test Failures (NEW)
python tools/github_issue_creation_demo.py --dry-run       # Generate issue templates (dry-run)
python tools/github_issue_creation_demo.py                 # Create actual GitHub issues
# View: quality/reports/issue_template_*.md (generated issue templates)

# Test Log Generation (NEW)
python tools/generate_test_logs.py                         # Generate sample test logs with proper structure
# View: quality/logs/test_execution.log (structured test logs with test_status)

# Test Archive Management and Retention (NEW)
python tools/archive_cleanup.py --metrics                  # Storage analysis and recommendations
python tools/archive_cleanup.py --dry-run                  # Preview cleanup actions
python tools/archive_cleanup.py --apply                    # Apply retention policies
python tools/archive_cleanup.py --search "test_report"     # Search archived files
python tools/archive_cleanup.py --bundle backup --patterns "reports/*.html"  # Create archive bundles

# RTM (Requirements Traceability Matrix) Automation (NEW)
python tools/rtm-links.py validate                         # Validate all RTM links
python tools/rtm-links.py validate --format json           # Validate with JSON output
python tools/rtm-links.py update --dry-run                 # Preview RTM link updates
python tools/rtm-links.py update --backup                  # Update RTM with backup
python tools/rtm-links.py generate-link EP-00001 --bold    # Generate GitHub issue link
python tools/rtm-links.py generate-bdd-link tests/bdd/features/auth.feature user_login  # Generate BDD link
python tools/rtm-links.py config-info                      # Show RTM configuration
python tools/rtm-links.py doctor                          # Run RTM health diagnostics

# RTM Database Management CLI (NEW - Enhanced Database Operations)
python tools/rtm-db.py --help                             # Show all available commands

## Entity Management
python tools/rtm-db.py entities create-epic --epic-id EP-00005 --title "Epic Title" --priority high
python tools/rtm-db.py entities create-user-story --user-story-id US-00055 --epic-id EP-00005 --github-issue 55 --title "User Story Title" --story-points 8
python tools/rtm-db.py entities create-test --test-type unit --test-file tests/unit/test_example.py --title "Test Title" --epic-id EP-00005

## Query and Reporting
python tools/rtm-db.py query epics                        # List all epics (table format)
python tools/rtm-db.py query epics --format json          # List epics in JSON format
python tools/rtm-db.py query epics --status planned --priority high  # Filter epics
python tools/rtm-db.py query user-stories --epic-id EP-00005  # User stories for specific epic
python tools/rtm-db.py query epic-progress EP-00005        # Detailed progress report for epic

## Data Import/Export
python tools/rtm-db.py data import-rtm docs/traceability/requirements-matrix.md  # Import from markdown
python tools/rtm-db.py data import-rtm --dry-run docs/file.md  # Preview import without changes
python tools/rtm-db.py data export --output rtm_backup.json   # Export all data to JSON
python tools/rtm-db.py data export --format json --include-tests  # Export with test data

## Database Administration
python tools/rtm-db.py admin health-check                 # Check database connectivity and status
python tools/rtm-db.py admin validate                     # Validate data integrity and relationships
python tools/rtm-db.py admin validate --fix               # Auto-fix validation issues (when implemented)
python tools/rtm-db.py admin reset --confirm              # Reset database (delete all data)

## GitHub Integration Status
python tools/rtm-db.py github sync-status                 # Show recent GitHub sync status
python tools/rtm-db.py github sync --issue-number 55      # Sync specific issue (when implemented)
python tools/rtm-db.py github sync --dry-run              # Preview sync operations

# RTM Test-Database Integration CLI (NEW - Test Execution Integration)
python tools/test-db-integration.py --help               # Show all available commands

## Test Discovery and Synchronization
python tools/test-db-integration.py discover tests       # Discover all tests and sync to database
python tools/test-db-integration.py discover tests --dry-run  # Preview test discovery without changes
python tools/test-db-integration.py discover scenarios   # Discover BDD scenarios and link to User Stories
python tools/test-db-integration.py discover scenarios --dry-run  # Preview BDD scenario linking

## Enhanced Test Execution with Database Integration
python tools/test-db-integration.py run tests            # Run tests with basic database integration
python tools/test-db-integration.py run tests --sync-tests  # Sync tests before running
python tools/test-db-integration.py run tests --link-scenarios  # Link BDD scenarios before running
python tools/test-db-integration.py run tests --auto-defects  # Auto-create defects from failures
python tools/test-db-integration.py run tests --test-type unit  # Run specific test type
python tools/test-db-integration.py run tests --sync-tests --link-scenarios --auto-defects  # Full integration

## Integration Status and Analysis
python tools/test-db-integration.py status overview       # Show test-database integration status
python tools/test-db-integration.py utils analyze        # Analyze test-database integration patterns
python tools/test-db-integration.py utils analyze --show-epic-refs  # Show Epic references in tests
python tools/test-db-integration.py utils analyze --show-orphaned   # Show tests without Epic links

## Enhanced Pytest Integration (NEW)
pytest --sync-tests --link-scenarios --auto-defects tests/  # Run tests with full database integration
pytest --sync-tests tests/unit/                         # Sync unit tests and run with database tracking
pytest --link-scenarios tests/bdd/                      # Link BDD scenarios and run
pytest --auto-defects tests/integration/                # Auto-create defects from integration test failures

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
- [ ] Check failure patterns: `python tools/failure_tracking_demo.py` (review failure trends)
- [ ] Verify archive status: `python tools/archive_cleanup.py --metrics` (storage optimization)
- [ ] Run linting: `black src/ tests/ && isort src/ tests/ && flake8 src/ tests/`
- [ ] Run type checking: `mypy src/`

**🧪 MANDATORY UNIT TEST COVERAGE** (Critical Quality Gate):
- [ ] **For ANY implementation or fix: Create unit tests before updating documentation**
- [ ] **TDD Approach**: Write tests first (failing) → Implement → Tests pass
- [ ] **Regression Prevention**: Add tests that would have caught the original issue
- [ ] **Edge Cases**: Test error conditions, boundary values, and platform differences
- [ ] ⚠️ **NEVER commit fixes without corresponding unit tests**
- [ ] ⚠️ **ALWAYS validate tests catch the specific problem being solved**

**🚨 MANDATORY DOCUMENTATION WORKFLOW** (⚠️ NEVER SKIP - ALWAYS COMPLETE!):
- [ ] **ALWAYS UPDATE RTM FIRST**: Mark US-XXXXX status and add implementation details
- [ ] **UPDATE GITHUB ISSUE**: Comment with completion details and close issue
- [ ] **CHECK REFERENCED DOCS**: Update development-workflow.md, quality-assurance.md if changes made
- [ ] **UPDATE CLAUDE.md**: Add new commands, update project structure if changed
- [ ] **VALIDATE TRACEABILITY**: Ensure all links in RTM still work
- [ ] ⚠️ **DOCUMENTATION IS NOT OPTIONAL - IT'S PART OF IMPLEMENTATION**
- [ ] ⚠️ **INCOMPLETE DOCUMENTATION = INCOMPLETE WORK**

**GitHub Integration & Project Management**:
- [ ] Reference linked GitHub issue in commit message (Implements/Fixes US-XXXXX)
- [ ] Comment on linked issue with implementation details
- [ ] Add BDD scenarios to issue description if created
- [ ] **Update GitHub Project status**: Move from "Backlog" → "In Progress" → "Done"
- [ ] **Update parent/child relationships**: Ensure Epic/US/DEF hierarchy is maintained
- [ ] **Update dependency status**: Mark blocking issues as resolved if applicable

**Documentation & Traceability**:
- [ ] Update RTM with implementation progress and project tracking
- [ ] Validate RTM links if traceability matrix modified: `python tools/rtm-links.py validate`
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
- **Coverage Integration**: Visual coverage analysis with file-level details (NEW)
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
   - **Find next unused ID**: `python tools/find_next_unused_id.py --type user-story` (check database, not GitHub)
   - **Verify ID availability**: `python tools/find_next_unused_id.py --type user-story --show-gaps` (shows all gaps)
   - **Set up project integration**: `export GONOGO_PROJECT_ID=$(gh project list --owner QHuuT --json number,title | jq -r '.[] | select(.title=="GoNoGo") | .number')`
   - **Create issue + add to project**:
     ```bash
     NEXT_ID=$(python tools/find_next_unused_id.py --type user-story)
     ISSUE_URL=$(gh issue create --title "$NEXT_ID: Title" --body "**Parent Epic**: EP-XXXXX\n**Dependencies**:\n- Blocks: #X\n- Blocked by: #Y" --label "user-story,priority/medium")
     gh project item-add $GONOGO_PROJECT_ID --url $ISSUE_URL
     ```
   - **Set hierarchical relationships**: Epic → User Story → Defect
   - **Document dependencies**: "Blocks #X" or "Blocked by #Y" relationships

### **🔢 RTM ID Management Commands**
```bash
# Find next unused ID for any entity type
python tools/find_next_unused_id.py --type user-story   # Next unused US-XXXXX
python tools/find_next_unused_id.py --type epic        # Next unused EP-XXXXX
python tools/find_next_unused_id.py --type defect      # Next unused DEF-XXXXX

# Show gaps in ID sequence (helpful for reusing lower numbers)
python tools/find_next_unused_id.py --type user-story --show-gaps
# Example output: "Next unused ID: US-00001" (reuses gaps instead of incrementing)

# Database ID verification (check what's actually used in RTM database)
python tools/rtm-db.py query user-stories --format table    # See all US IDs in database
python tools/rtm-db.py query epics --format table           # See all EP IDs in database
python tools/rtm-db.py query defects --format table         # See all DEF IDs in database
```

### **📊 RTM Report Generation Commands**
```bash
# LIVE DATA - Production RTM Reports (uses real project data)
python tools/rtm_report_generator.py --html              # Generate live RTM report
# Saves to: quality/reports/dynamic_rtm/rtm_matrix_complete.html
# Uses: Real epics, user stories, tests, defects from RTM database
# Features: Interactive test filtering (E2E, Unit, Integration, Security), clickable epic links

# DEMO DATA - Test RTM Reports (uses sample data for development)
python tools/rtm_demo.py --html                          # Generate demo RTM report
python tools/rtm_demo.py --populate-test-data            # Add demo data to database
python tools/rtm_demo.py --reset-to-demo                 # Reset database to demo-only
# Saves to: quality/reports/dynamic_rtm/rtm_matrix_demo.html
# Uses: EP-DEMO-XXX, US-DEMO-XXX, etc. sample data

# 🐍 Python-Based RTM Filtering (SERVER-SIDE) ✨
python tools/rtm_python_filter.py --help                # Show all filtering options
python tools/rtm_python_filter.py --us-status completed # Filter by user story status
python tools/rtm_python_filter.py --test-type e2e       # Show only E2E tests (default)
python tools/rtm_python_filter.py --defect-priority critical  # Show only critical defects
python tools/rtm_python_filter.py --format html --output filtered.html  # Custom output
python tools/rtm_python_filter.py --show-stats --verbose # Detailed filtering info
# Python server-side filtering: Pre-filtered data, CLI automation, faster for large datasets

# 📊 RTM Report Types & Filtering Options
# 1. STATIC HTML Reports (Client-side JavaScript filtering)
#    - Generated files work offline, no server needed
#    - JavaScript filters work in any browser
#    - Click buttons to filter user stories, tests, defects
#
# 2. PYTHON CLI Filtering (Server-side filtering)
#    - Pre-filtered data generation
#    - Command-line automation friendly
#    - Faster for large datasets, more secure

# RTM Database Management
python tools/rtm-db.py query epics --format table       # View all epics in database
python tools/rtm-db.py query user-stories --format table # View all user stories
python tools/rtm-db.py admin health-check               # Verify database integrity
python tools/import_real_github_data.py --import        # Import from GitHub issues
```

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