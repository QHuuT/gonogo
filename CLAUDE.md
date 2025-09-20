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

## Common Commands
```bash
# Development
python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8000

# Testing
pytest tests/ -v                    # All tests
pytest tests/unit/ -v               # Unit tests only
pytest tests/integration/ -v        # Integration tests
pytest tests/security/ -v           # Security tests
pytest --cov=src tests/             # Coverage report

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

### 🔄 Standard Workflow (ALWAYS follow this)
**📖 Detailed Process**: See [Development Workflow](docs/technical/development-workflow.md)

1. **Start**: Read CLAUDE.md for current project state
2. **Code**: Implement changes following project conventions
3. **Test**: Run relevant tests (unit → integration → security)
4. **Quality**: Run linting and type checking
5. **Document**: Update CLAUDE.md and relevant documentation
6. **Commit**: Use conventional commit messages

### 📝 Before Every Session
- [ ] Read CLAUDE.md completely
- [ ] Check current git status
- [ ] Review recent commits for context
- [ ] Update todos if needed

### ✅ Before Every Commit
**📖 Complete Checklist**: See [Quality Assurance Guidelines](docs/technical/quality-assurance.md#quality-gates)

- [ ] Run tests: `pytest tests/ -v`
- [ ] Run linting: `black src/ tests/ && isort src/ tests/ && flake8 src/ tests/`
- [ ] Run type checking: `mypy src/`
- [ ] Update documentation if needed
- [ ] Update CLAUDE.md if project structure changed

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
├── quality/                # Quality assurance
│   ├── monitoring/         # Logs and monitoring
│   └── reports/           # Test and coverage reports
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

### **🚀 New Development Session**
1. [ ] Read CLAUDE.md (this file)
2. [ ] Check [GitHub Issues](../../issues) for current work
3. [ ] Review [Development Workflow](docs/technical/development-workflow.md) if needed
4. [ ] Check [Requirements Matrix](docs/traceability/requirements-matrix.md) status
5. [ ] Verify [GDPR implications](docs/context/compliance/gdpr-requirements.md) if handling personal data

### **✅ Before Every Commit**
1. [ ] Follow [Development Workflow](docs/technical/development-workflow.md) phases
2. [ ] Complete [Quality Gates](docs/technical/quality-assurance.md#quality-gates)
3. [ ] Update [Documentation](docs/technical/documentation-workflow.md) if needed
4. [ ] Use [Conventional Commit](docs/technical/quality-assurance.md#commit-message-standards) format

---

**📌 Remember**: This file provides quick reference and commands. For detailed processes, workflows, and guidelines, see the linked documentation in `docs/`.