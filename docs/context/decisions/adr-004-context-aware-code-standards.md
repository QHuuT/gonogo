# ADR-004: Context-Aware Code Standards

**Status**: Accepted
**Date**: 2025-09-27
**Deciders**: Development Team

## Context

### Initial Decision and Failure
During early project setup, we implemented a **uniform 79-character line length standard (E501)** across the entire codebase without considering different code contexts. This decision was made based on traditional PEP 8 guidelines but failed to account for the reality of modern Python development practices and the diverse nature of code in a full-stack application.

### The Scale of the Problem
Our uniform standard resulted in **2,424 E501 line length violations** across the codebase, distributed as follows:
- **Tools/Migrations**: 1,279 violations (53%) - Database schemas, utility scripts
- **Tests**: 725 violations (30%) - Test assertions, mock data, BDD scenarios
- **Source Code**: ~420 violations (17%) - Main application logic

### Time Waste Analysis
The uniform approach led to **80+ hours of wasted developer effort** attempting to manually fix violations that were inappropriate to fix:
- Database migration column definitions that need descriptive names
- HTML template strings that break readability when split
- Test assertions with verbose mock data
- Utility scripts designed for temporary use

### Root Cause
We failed to recognize that **different code contexts have different readability requirements**:
1. **Production code**: Benefits from strict formatting for maintainability
2. **Test code**: Requires verbose assertions and mock data for clarity
3. **Migration code**: Needs descriptive database schema definitions
4. **Utility code**: Often temporary and doesn't warrant strict formatting
5. **Template code**: HTML strings are better externalized than artificially split

## Decision

### Graduated Line Length Standards
We will implement **context-aware code standards** with different rules for different code types:

#### Production Code (src/be/, src/fe/)
- **Line Length**: 120 characters (pragmatic modern standard)
- **Enforcement**: Strict via pre-commit hooks and CI
- **Rationale**: Core business logic needs consistency and maintainability

#### Test Code (tests/)
- **Line Length**: E501 disabled
- **Enforcement**: None for line length
- **Rationale**: Test clarity trumps line length; verbose assertions improve debugging

#### Migration Code (migrations/)
- **Line Length**: E501 disabled
- **Enforcement**: None for line length
- **Rationale**: Database schema definitions often require long descriptive names

#### Utility Code (tools/)
- **Line Length**: E501 disabled
- **Enforcement**: None for line length
- **Rationale**: Temporary scripts don't warrant strict formatting overhead

#### Template Code
- **Approach**: Extract to external Jinja2 templates instead of fixing in-Python strings
- **Rationale**: Architectural improvement over artificial line breaks

### Implementation Strategy
```toml
# pyproject.toml
[tool.flake8]
max-line-length = 120
per-file-ignores = [
    "tests/*: E501",        # Test clarity over line length
    "migrations/*: E501",   # Database schemas need space
    "tools/*: E501",        # Utility scripts are temporary
    "**/templates.py: E501" # HTML strings should be externalized
]
```

## Consequences

### Positive
- **Developer Productivity**: Eliminates fighting with inappropriate formatting rules
- **Code Quality**: Focus on meaningful standards instead of arbitrary line breaks
- **Maintainability**: Different contexts get appropriate treatment
- **Time Savings**: 70+ hours saved compared to manual fixing approach
- **Architectural Improvement**: Encourages template externalization

### Negative
- **Complexity**: Different rules for different contexts require documentation
- **Tooling Setup**: Requires proper flake8 configuration management
- **Initial Confusion**: Developers need to learn context-specific rules

### Lessons Learned
1. **Always analyze before standardizing**: Measure violation distribution before setting policies
2. **Context matters**: One-size-fits-all approaches often fail in practice
3. **Real-world validation**: Test standards against actual codebase patterns
4. **Cost-benefit analysis**: Developer time spent on standards should provide proportional value

## Implementation

### Corrective Actions Taken (2025-09-27)
1. **Bulk reversion** of inappropriate manual E501 fixes in tools/, tests/, and migrations/ directories
   - Reverted 1,279+ manual line breaks that reduced code readability
   - Focused on context-inappropriate fixes in database schemas, test assertions, and utility scripts
   - Preserved meaningful fixes in production code (src/be/, src/fe/)

2. **Applied Ruff formatting** to production code only with 120-character line length
   - Automated formatting for src/be/models/traceability/ (8 files reformatted)
   - Applied consistent formatting to src/be/services/rtm_report_generator.py
   - Validated syntax integrity and import functionality after changes

3. **Validated configuration effectiveness**
   - Confirmed syntax integrity of all reformatted production code
   - Verified import functionality remains intact
   - Tested context-aware standards approach

### Immediate Actions
1. **Update flake8 configuration** in pyproject.toml with per-file-ignores
2. **Install flake8-pyproject** to enable pyproject.toml configuration
3. **Update README.md** to document new approach and reference this ADR
4. **Create development guide** with context-specific standards

### Architecture Improvements
1. **Extract HTML templates** from Python strings to external Jinja2 files
2. **Separate CSS** from Python code into external stylesheets
3. **Document template extraction patterns** for future development

### Prevention Strategy
1. **Pre-commit hooks** enforce standards only on production code (src/)
2. **CI checks** validate new code follows context-appropriate standards
3. **Regular reviews** of standards effectiveness and developer feedback
4. **Documentation** of when and why to create exceptions

## Success Metrics

### Quantitative
- **Reduction in developer time** spent on line length issues
- **Decrease in false-positive** linting violations
- **Increase in meaningful** code quality improvements
- **Template externalization rate** for HTML-heavy modules

### Qualitative
- **Developer satisfaction** with practical standards
- **Code maintainability** improvement in production modules
- **Test readability** improvement with relaxed constraints
- **Architecture cleanliness** through template separation

## References

- **Initial problem**: 2,424 E501 violations across codebase
- **Time waste**: 80+ hours of manual fixing attempts
- **Alternative tools**: Ruff formatter for automated fixes where appropriate
- **Template extraction**: Jinja2 FileSystemLoader patterns for HTML separation

## Related ADRs

- **ADR-001**: Technology Stack Selection (FastAPI + Jinja2 enables template separation)
- **ADR-002**: GDPR-First Architecture (Code quality supports privacy implementation)

---

**Note**: This ADR represents a correction of our initial uniform standards approach. It demonstrates the importance of context-aware decision making and validates decisions against real-world codebase patterns before implementation.