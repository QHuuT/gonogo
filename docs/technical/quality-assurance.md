# Quality Assurance Guidelines

**Last Updated**: 2025-09-20

## 🎯 Overview

This document defines the quality assurance practices, code standards, and testing strategies for the GoNoGo project, ensuring consistent, secure, and maintainable code.

## 🐍 Python Code Style

### **Formatting Standards**
- **Formatting**: Black (line length 88)
- **Import sorting**: isort
- **Linting**: flake8
- **Type hints**: mypy (strict mode)
- **Naming**: snake_case for functions/variables, PascalCase for classes

### **Code Quality Commands**
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## 🧹 Clean Code Principles

### **Single Responsibility Principle (SRP)**
- Each class/function has one reason to change
- Functions should do one thing and do it well
- Classes should have a single, well-defined purpose

### **DRY (Don't Repeat Yourself)**
- Eliminate code duplication through abstraction
- Extract common functionality into reusable functions
- Use configuration instead of hardcoded values

### **KISS (Keep It Simple, Stupid)**
- Favor simplicity over cleverness
- Write code that others can easily understand
- Avoid unnecessary complexity

### **Function Design Rules**
- Functions should be small (20 lines max preferred)
- Function arguments: 0-2 ideal, 3+ requires strong justification
- Use descriptive names that explain what the function does

## 📖 Code as Documentation

### **Meaningful Names**
Variables, functions, and classes should clearly express their purpose:

```python
# Good examples
customer_email = "user@example.com"
calculate_tax_amount(gross_amount, tax_rate)
class UserAuthenticationService:
    pass

# Bad examples
x = "user@example.com"
def process(data):
    pass
class Service1:
    pass
```

### **Replace Magic Numbers**
Use named constants instead of hard-coded values:

```python
# Bad
if user.age > 18:
    grant_access()

# Good
LEGAL_AGE = 18
if user.age > LEGAL_AGE:
    grant_access()
```

## 💬 Rational Commenting

### **Comment WHY, not WHAT**
Code shows what, comments explain why:

```python
# Bad - explains what
user_count += 1  # Increment user count

# Good - explains why
user_count += 1  # Track for billing calculation at month end
```

### **Comment Guidelines**
- **Avoid Redundant Comments**: If code is self-explanatory, don't comment
- **Focus on Intent**: Explain business logic, algorithms, and design decisions
- **Context and Rationale**: Why this approach over alternatives?
- **Update Comments**: Keep comments current with code changes
- **No Commented Code**: Delete unused code, don't comment it out

## 🛡️ Security & GDPR Guidelines

### **Data Protection Rules**
- **Never log personal data** (emails, IPs after anonymization)
- **Always require consent** for data collection
- **Implement data retention** policies
- **Use secure headers** in all responses
- **Validate all inputs** and sanitize outputs

### **Security Best Practices**
```python
# Anonymize sensitive data for logging
logger.info(f"User action: {action}", extra={
    'user_id_hash': anonymize_user_id(user.id),
    'ip_hash': anonymize_ip(request.client.host)
})

# Validate and sanitize inputs
def create_comment(content: str) -> Comment:
    if not content or len(content) > MAX_COMMENT_LENGTH:
        raise ValidationError("Invalid comment content")

    sanitized_content = sanitize_html(content)
    return Comment(content=sanitized_content)
```

## 🧪 Testing Strategy

### **Test Pyramid Structure**
- **Unit tests**: 70% (fast, isolated, mock dependencies)
- **Integration tests**: 20% (database, external services)
- **E2E tests**: 10% (critical user flows only)
- **Security tests**: Always test GDPR compliance and input validation

### **Testing Commands (Enhanced with Structured Logging)**
```bash
# All tests with structured logging (NEW)
pytest tests/ -v                    # Creates quality/logs/test_execution.log

# Enhanced test execution modes (NEW)
pytest --mode=silent --type=all     # All tests, minimal output
pytest --mode=verbose --type=unit   # Unit tests with detailed output
pytest --mode=detailed --type=integration  # Integration tests with full debugging

# Test categories
pytest tests/unit/ -v               # Unit tests only
pytest tests/integration/ -v        # Integration tests
pytest tests/security/ -v           # Security tests
pytest tests/e2e/ -v               # End-to-end tests

# Coverage report
pytest --cov=src tests/ --cov-report=term-missing

# GDPR compliance tests
pytest tests/security/test_gdpr_compliance.py -v
```

### **Test Quality Standards**
- **100% coverage** for critical business logic
- **90%+ overall coverage** maintained
- **All GDPR scenarios** must pass
- **Zero high-severity security issues**

## 📝 Commit Message Standards

### **Conventional Commit Format**
```bash
<type>: <description>

[optional body]

[optional footer]
```

### **Commit Types**
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **test**: Adding or updating tests
- **refactor**: Code refactoring
- **style**: Code style changes (formatting, etc.)
- **perf**: Performance improvements
- **security**: Security-related changes

### **Examples**
```bash
feat: add comment system with GDPR consent

- Implement comment creation with privacy controls
- Add consent collection and validation
- Include data retention policies
- Update GDPR compliance documentation

Closes: US-003
Tests: BDD scenarios passing
Coverage: 92% maintained

fix: resolve SQL injection in search endpoint

- Sanitize search query parameters
- Add input validation middleware
- Update security tests

Security-Impact: High
```

## 🔍 Quality Gates

### **Before Every Commit Checklist**
- [ ] Run tests: `pytest tests/ -v`
- [ ] Run linting: `black src/ tests/ && isort src/ tests/ && flake8 src/ tests/`
- [ ] Run type checking: `mypy src/`
- [ ] Update documentation if needed
- [ ] Update CLAUDE.md if project structure changed
- [ ] Verify GDPR compliance if personal data involved

### **Code Review Checklist**
- [ ] Code follows style guidelines
- [ ] Functions are small and focused
- [ ] Names are descriptive and meaningful
- [ ] Comments explain why, not what
- [ ] Security best practices followed
- [ ] GDPR compliance maintained
- [ ] Tests cover new functionality
- [ ] Documentation updated if needed

## 🎯 Avoiding Marketing Style in Technical Writing

### **Technical Writing Guidelines**
- **Be Direct and Precise**: Use specific, concrete language
- **No Filler Words**: Eliminate "really", "quite", "very", "awesome", "great"
- **Active Voice**: Use subject-verb-object structure
- **One Concept Per Sentence**: Keep sentences focused and clear
- **Avoid Jargon**: Use plain language unless technical terms are necessary
- **No Emotional Appeals**: Stick to facts and technical requirements
- **Concrete Examples**: Provide specific examples rather than vague descriptions

### **Examples**
```markdown
# Bad - marketing style
This really amazing function greatly improves performance and provides awesome user experience!

# Good - technical style
This function reduces query time from 2s to 200ms by implementing query result caching.
```

## 📊 Quality Metrics

### **Code Quality Metrics**
- **Test Coverage**: > 90%
- **Type Coverage**: > 95%
- **Linting Issues**: 0
- **Security Vulnerabilities**: 0 high/critical
- **GDPR Compliance**: 100% scenarios passing

### **Process Quality Metrics**
- **Documentation Currency**: Updated within 24h of changes
- **Code Review**: 100% of PRs reviewed
- **Quality Gates**: 100% passing before merge
- **Defect Escape Rate**: < 5% to production

## 📊 Test Reporting and Analysis (NEW)

### **HTML Test Reports**
Generate interactive test reports for analysis and debugging:
```bash
# Generate report from test logs
python tools/report_generator.py --input quality/logs/

# Generate demo report for testing
python tools/report_generator.py --demo

# Generate filtered reports
python tools/report_generator.py --type unit --input quality/logs/
```

### **Report Features**
- **Interactive Filtering**: Filter by test status, type, and search terms
- **Timeline Visualization**: See test execution patterns over time
- **Failure Analysis**: Categorized error patterns and debugging information
- **Export Capabilities**: CSV export for external analysis
- **GDPR Compliance**: Personal data sanitization in logs and reports

### **Quality Gates Enhancement**
Before every commit, now includes:
1. ✅ **Run tests**: `pytest tests/ -v` (generates structured logs)
2. ✅ **Generate report**: `python tools/report_generator.py --input quality/logs/`
3. ✅ **Review report**: Check `quality/reports/test_report.html` for issues
4. ✅ **Code quality**: Run black, isort, flake8, mypy
5. ✅ **Type checking**: Ensure mypy passes

---

**Related Documentation**:
- [Development Workflow](development-workflow.md) - Complete development process
- [Security Architecture](cross-cutting-architecture/security-architecture.md) - Security implementation
- [GDPR Requirements](../context/compliance/gdpr-requirements.md) - Privacy compliance