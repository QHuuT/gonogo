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

## BDD + RTM Development Workflow

### 🎯 Strategic Approach: Requirements to Implementation

Our development follows a **5-Layer Requirements Architecture**:
1. **Business Requirements** → User Stories
2. **Functional Requirements** → BDD Scenarios (Gherkin)
3. **Technical Documentation** → Auto-generated from scenarios
4. **Implementation** → Code guided by BDD tests
5. **Traceability** → RTM linking all layers

### 📋 Core Development Workflow

#### **Phase 1: Requirements Analysis**
1. **Read CLAUDE.md** (this file) for current project state
2. **Select User Story** from `docs/01-business/user-stories.md`
3. **Review BDD Scenarios** in `docs/02-technical/bdd-scenarios/`
4. **Check RTM Status** in `docs/traceability/requirements-matrix.md`
5. **Verify GDPR Implications** in `docs/traceability/gdpr-compliance-map.md`

#### **Phase 2: Test-Driven Implementation**
6. **Write/Update BDD Step Definitions** in `tests/bdd/step_definitions/`
7. **Run BDD Tests** (should fail - RED phase)
   ```bash
   pytest tests/bdd/ -v --tb=short
   ```
8. **Implement Minimum Code** to make tests pass (GREEN phase)
9. **Refactor** while keeping tests green (REFACTOR phase)
10. **Run Full Test Suite** to ensure no regressions

#### **Phase 3: Documentation & Traceability**
11. **Update RTM** in `docs/traceability/requirements-matrix.md`
12. **Update Technical Docs** if architecture changed
13. **Verify GDPR Compliance** if personal data involved
14. **Update CLAUDE.md** if workflow or structure changed

#### **Phase 4: Quality Gates**
15. **Run Quality Checks**:
    ```bash
    black src/ tests/ && isort src/ tests/ && flake8 src/ tests/ && mypy src/
    ```
16. **Run Security Tests**: `pytest tests/security/ -v`
17. **Run GDPR Compliance Tests**: `pytest tests/security/test_gdpr_compliance.py -v`
18. **Verify Test Coverage**: `pytest --cov=src tests/ --cov-report=term-missing`

#### **Phase 5: Integration & Commit**
19. **Integration Test**: `pytest tests/integration/ -v`
20. **E2E Test** (if applicable): `pytest tests/e2e/ -v`
21. **Commit with Conventional Message**:
    ```bash
    git commit -m "feat: implement [user story] with BDD coverage

    - Add BDD scenarios for [feature]
    - Implement [specific functionality]
    - Update RTM with traceability
    - Ensure GDPR compliance

    Closes: US-XXX
    Tests: BDD scenarios passing
    Coverage: XX% maintained"
    ```

### 🔄 BDD Scenario Development Process

#### **Writing New BDD Scenarios**
1. **Use Template**: Copy from `docs/02-technical/bdd-scenarios/scenario-template.feature`
2. **Follow Gherkin Best Practices**:
   - **Given**: Set up initial context
   - **When**: Perform the action
   - **Then**: Verify expected outcome
3. **Tag Appropriately**: `@functional @gdpr @security @performance`
4. **Include GDPR Scenarios**: Always consider privacy implications
5. **Link to User Story**: Reference US-XXX in comments

#### **Implementing Step Definitions**
1. **Create Step File**: `tests/bdd/step_definitions/test_[feature]_steps.py`
2. **Import Scenarios**: `scenarios("../features/[feature].feature")`
3. **Implement Steps**: Use `@given`, `@when`, `@then` decorators
4. **Use Fixtures**: Leverage `bdd_context`, `bdd_test_client`, etc.
5. **Mock External Dependencies**: Keep tests isolated

### 📊 Requirements Traceability Matrix (RTM) Updates

#### **When to Update RTM**
- New user story implemented
- BDD scenario added or modified
- Code implementation completed
- Test status changed
- Defect discovered or resolved

#### **RTM Update Process**
1. **Open**: `docs/traceability/requirements-matrix.md`
2. **Update Status**: Change from 📝 Planned → ⏳ In Progress → ✅ Done
3. **Link Artifacts**: Ensure all columns are filled
4. **Update Metrics**: Recalculate coverage percentages
5. **Note Dependencies**: Update any blocking items
6. **Link Defects**: Update defects column with DEF-XXX references

### 🛡️ GDPR Compliance Integration

#### **For Every Feature Involving Personal Data**
1. **Check GDPR Map**: Review `docs/traceability/gdpr-compliance-map.md`
2. **Identify Legal Basis**: Consent, Legitimate Interest, etc.
3. **Implement Privacy by Design**: Minimize data collection
4. **Add GDPR BDD Scenarios**: Test consent, access, erasure
5. **Update Data Processing Records**: Document in RTM

#### **GDPR Testing Checklist**
- [ ] Consent collection tested
- [ ] Data minimization verified
- [ ] Retention policies implemented
- [ ] Right to access working
- [ ] Right to erasure working
- [ ] Data export functional

### 🐛 Defect Management Workflow

#### **When a Defect is Discovered**
1. **Create Defect Report**: Copy `docs/01-business/defect-template.md`
2. **Create File**: `docs/01-business/defects/DEF-XXX-defect-name.md`
3. **Link to Epic/User Story**: Identify related requirements
4. **Assess Business Impact**: Priority, severity, GDPR implications
5. **Update RTM**: Add defect reference to affected requirements
6. **Create Fix BDD Scenario**: Test for the fix (if needed)

#### **Defect Resolution Process**
1. **Analyze Root Cause**: Document in defect report
2. **Fix Implementation**: Follow standard BDD workflow
3. **Update BDD Scenarios**: Prevent regression
4. **Verify Fix**: All acceptance criteria now pass
5. **Update RTM**: Mark defect as resolved
6. **Close Defect**: Update status and verify date

#### **Defect Prevention**
- Review defect patterns monthly
- Update BDD scenarios to catch similar issues
- Improve quality gates based on defect analysis
- Update development guidelines to prevent recurrence

### 🚀 Ready for Team Scaling

#### **Solo Developer Benefits**
- Clear structure for complex features
- Built-in quality assurance
- GDPR compliance by design
- Complete audit trail
- Systematic defect tracking

#### **Team Integration Ready**
- Shared BDD scenarios as living documentation
- RTM provides project overview
- Clear handoff procedures
- Standardized quality gates
- Traceable defect management

### 📈 Success Metrics

#### **Development Quality**
- 100% User Story → BDD Scenario coverage
- 90%+ test coverage maintained
- All GDPR scenarios passing
- Zero high-severity security issues

#### **Process Quality**
- RTM updated within 24h of changes
- Documentation current with code
- All commits linked to user stories
- Quality gates passing before merge

---

**Next Development Session Checklist:**
1. [ ] Read CLAUDE.md (this file)
2. [ ] Review current RTM status
3. [ ] Select next user story
4. [ ] Follow BDD workflow
5. [ ] Update documentation
6. [ ] Verify GDPR compliance