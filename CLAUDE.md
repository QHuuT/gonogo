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
│   ├── 01-business/         # Business requirements
│   ├── 02-technical/        # Technical documentation
│   └── 03-user/            # User guides
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

## Development Guidelines

### 🐍 Python Code Style
- **Formatting**: Black (line length 88)
- **Import sorting**: isort
- **Linting**: flake8
- **Type hints**: mypy (strict mode)
- **Naming**: snake_case for functions/variables, PascalCase for classes

### 🛡️ Security & GDPR
- **Never log personal data** (emails, IPs after anonymization)
- **Always require consent** for data collection
- **Implement data retention** policies
- **Use secure headers** in all responses
- **Validate all inputs** and sanitize outputs

### 🧪 Testing Strategy
- **Unit tests**: 70% (fast, isolated, mock dependencies)
- **Integration tests**: 20% (database, external services)
- **E2E tests**: 10% (critical user flows only)
- **Security tests**: Always test GDPR compliance and input validation

### 📝 Commit Messages
```
feat: add comment system with GDPR consent
fix: resolve SQL injection in search
docs: update deployment instructions
test: add unit tests for blog post service
```

### 🚀 Deployment
- **Staging**: Auto-deploy from `develop` branch
- **Production**: Manual approval from `main` branch
- **Environment vars**: Never commit secrets
- **Database**: Always backup before migrations

## Advanced Development Practices

### 📖 Code as Documentation (Self-Documenting Code)
- **Meaningful Names**: Variables, functions, and classes should clearly express their purpose
  - Good: `customer_email`, `calculate_tax_amount`, `UserAuthenticationService`
  - Bad: `x`, `data`, `process`, `Service1`
- **Function Design**: Each function should do one thing and do it well (Single Responsibility)
- **Clear Structure**: Organize code logically with consistent patterns
- **Replace Magic Numbers**: Use named constants instead of hard-coded values
  ```python
  # Bad
  if user.age > 18:

  # Good
  LEGAL_AGE = 18
  if user.age > LEGAL_AGE:
  ```

### 🧹 Clean Code Principles (Uncle Bob Martin)
- **Single Responsibility Principle (SRP)**: Each class/function has one reason to change
- **DRY (Don't Repeat Yourself)**: Eliminate code duplication through abstraction
- **KISS (Keep It Simple, Stupid)**: Favor simplicity over cleverness
- **Open/Closed Principle**: Open for extension, closed for modification
- **Boy Scout Rule**: Always leave code cleaner than you found it
- **Function Rules**:
  - Functions should be small (20 lines max preferred)
  - Functions should do one thing
  - Function arguments: 0-2 ideal, 3+ requires strong justification

### 💬 Rational Commenting
- **Comment WHY, not WHAT**: Code shows what, comments explain why
  ```python
  # Bad - explains what
  user_count += 1  # Increment user count

  # Good - explains why
  user_count += 1  # Track for billing calculation at month end
  ```
- **Avoid Redundant Comments**: If code is self-explanatory, don't comment
- **Focus on Intent**: Explain business logic, algorithms, and design decisions
- **Context and Rationale**: Why this approach over alternatives?
- **Update Comments**: Keep comments current with code changes
- **No Commented Code**: Delete unused code, don't comment it out

### 🎯 Avoiding Marketing Style in Technical Writing
- **Be Direct and Precise**: Use specific, concrete language
  - Bad: "This really amazing function greatly improves performance"
  - Good: "This function reduces query time from 2s to 200ms"
- **No Filler Words**: Eliminate "really", "quite", "very", "awesome", "great"
- **Active Voice**: Use subject-verb-object structure
  - Bad: "Data will be processed by the system"
  - Good: "The system processes data"
- **One Concept Per Sentence**: Keep sentences focused and clear
- **Avoid Jargon**: Use plain language unless technical terms are necessary
- **No Emotional Appeals**: Stick to facts and technical requirements
- **Concrete Examples**: Provide specific examples rather than vague descriptions