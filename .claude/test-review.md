# 🧪 Code Review & Testing Agent

**Comprehensive testing workflows and quality analysis**

## 🎯 Agent Purpose
This agent specializes in **comprehensive testing, code reviews, and quality analysis** - all testing modes, coverage analysis, failure debugging, and RTM test integration.

**🔄 For other tasks**: [Agent Navigation](../CLAUDE.md#🤖-agent-navigation)

## ⚡ Quick Start

### **Complete Testing Setup**
```bash
# Install all testing dependencies
pip install -e ".[dev]" && pip install jinja2

# Verify test environment
pytest --version && coverage --version

# RTM test integration check
python tools/test-db-integration.py status overview
```

## 🧪 Comprehensive Testing Workflows

### **Full Test Suite Execution**
```bash
# Complete test suite with all modes
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Test pyramid execution (recommended order)
pytest tests/unit/ -v                     # Unit tests (70% of suite)
pytest tests/integration/ -v              # Integration tests (20%)
pytest tests/security/ -v                 # Security tests (GDPR critical)
pytest tests/e2e/ -v                      # E2E tests (10%)

# BDD scenarios (when applicable)
pytest tests/bdd/ -v --gherkin-terminal-reporter
```

### **Advanced Testing Modes**
```bash
# Testing with structured logging
pytest --mode=silent --type=all           # Minimal output, all tests
pytest --mode=verbose --type=unit         # Detailed unit test output
pytest --mode=detailed --type=integration # Full debugging, integration

# Parallel testing (for large suites)
pytest tests/ -n auto                     # Auto-detect CPU cores
pytest tests/unit/ -n 4                   # Specific number of workers

# Test discovery and collection
pytest --collect-only tests/              # Show all discovered tests
pytest --co -q tests/unit/                # Quick collection check
```

## 📊 Test Coverage Analysis

### **Coverage Reports & Analysis**
```bash
# Generate comprehensive coverage report
pytest --cov=src tests/ --cov-report=html --cov-report=json --cov-report=term

# Coverage with branch analysis
pytest --cov=src --cov-branch tests/ --cov-report=html

# Missing coverage report
coverage report --show-missing --include="src/*"

# Coverage thresholds (quality gates)
pytest --cov=src tests/ --cov-fail-under=80  # Fail if coverage < 80%
```

### **Test Report Generation**
```bash
# Generate detailed HTML test reports
python tools/report_generator.py --input quality/logs/test_execution.log

# Coverage-integrated reports
python tools/report_generator.py --demo --type all --output quality/reports/

# Custom filtered reports
python tools/report_generator.py --type unit --input quality/logs/ \
  --filename unit_test_report.html
```

## 🔍 Test Failure Analysis

### **Debugging Test Failures**
```bash
# Run only failed tests from last run
pytest --lf -v                            # Last failed
pytest --ff -v                            # Failed first, then others

# Detailed failure analysis
pytest tests/unit/test_failing.py -v -s --tb=long
pytest tests/unit/test_failing.py --pdb   # Drop into debugger

# Failure pattern analysis
python tools/failure_tracking_demo.py     # Generate failure analysis
# View: quality/reports/failure_analysis_report.html
```

### **Test Environment Debugging**
```bash
# Check test isolation issues
pytest tests/unit/ --forked               # Fork each test (isolation)
pytest tests/unit/ --capture=no           # Disable output capture

# Database state debugging (for integration tests)
pytest tests/integration/ -v -s --keep-db # Keep test database

# Dependency and import debugging
python -c "import sys; print(sys.path)"
python -c "from src.be.models import Epic; print('✅ Imports OK')"
```

## 🏗️ RTM Test Integration

### **Test-Database Integration**
```bash
# Complete RTM test integration workflow
python tools/test-db-integration.py discover tests --sync-tests
python tools/test-db-integration.py run tests --link-scenarios --auto-defects

# Test discovery and linking
python tools/test-db-integration.py discover tests --dry-run    # Preview
python tools/test-db-integration.py discover scenarios --dry-run # BDD preview

# Test execution with RTM tracking
pytest --sync-tests --link-scenarios tests/unit/
pytest --auto-defects tests/integration/  # Create defects from failures
```

### **RTM Test Analysis**
```bash
# Test coverage by epic/user story
python tools/test-db-integration.py utils analyze --show-epic-refs
python tools/test-db-integration.py utils analyze --show-orphaned

# Integration status overview
python tools/test-db-integration.py status overview
```

## 🎯 Specialized Testing Workflows

### **Security & GDPR Testing**
```bash
# Comprehensive security test suite
pytest tests/security/ -v --tb=short

# GDPR compliance testing
pytest tests/security/ -k "gdpr" -v
pytest tests/security/ -k "privacy" -v

# Security scan integration
bandit -r src/ -f json -o quality/reports/security_scan.json
safety check --json --output quality/reports/safety_report.json
```

### **Performance & Load Testing**
```bash
# Performance regression tests
pytest tests/performance/ -v --benchmark-only

# Memory leak detection
pytest tests/unit/ --memray
pytest tests/integration/ --profile

# Database performance testing
pytest tests/integration/test_database.py -v --durations=10
```

### **BDD Scenario Testing**
```bash
# Gherkin feature validation
pytest tests/bdd/ -v --gherkin-terminal-reporter

# Scenario-to-user-story linking
python tools/test-db-integration.py discover scenarios --link-scenarios

# BDD report generation
pytest tests/bdd/ --html=quality/reports/bdd_report.html --self-contained-html
```

## 📋 Code Review Workflows

### **Pre-Review Quality Gates**
```bash
# Complete quality check before review
black src/ tests/ --check                 # Code formatting
isort src/ tests/ --check-only             # Import sorting
flake8 src/ tests/ --max-line-length=88    # Linting
mypy src/ --ignore-missing-imports         # Type checking

# Security and dependency checks
bandit -r src/ -ll                         # Security issues
safety check                              # Vulnerable dependencies
pip-audit                                  # Additional security scan
```

### **Review Analysis Tools**
```bash
# Test coverage analysis for review
pytest --cov=src tests/ --cov-report=term --cov-report=html
coverage report --sort=cover              # Sort by coverage

# Code complexity analysis
radon cc src/ -a                           # Cyclomatic complexity
radon mi src/                              # Maintainability index

# Test quality metrics
pytest tests/ --durations=20              # Slowest tests
pytest tests/ --collect-only | grep "test" | wc -l  # Test count
```

## 🔄 Continuous Integration Testing

### **CI/CD Test Simulation**
```bash
# Simulate GitHub Actions testing locally
pytest tests/ -v --cov=src --cov-fail-under=75 --tb=short

# Multi-environment testing (if using tox)
tox -e py39,py310,py311                   # Multiple Python versions

# Docker-based testing
docker-compose -f docker-compose.test.yml up --build
```

### **Quality Metrics Collection**
```bash
# Generate all quality reports for CI
python tools/report_generator.py --type all --input quality/logs/
python tools/failure_tracking_demo.py     # Failure patterns
python tools/archive_cleanup.py --metrics # Storage analysis

# RTM validation for CI
python tools/rtm-links.py validate --format json
python tools/rtm-db.py admin validate
```

## 🛠️ Advanced Testing Tools

### **Test Data Management**
```bash
# Test log generation and analysis
python tools/generate_test_logs.py        # Generate structured logs
cat quality/logs/test_execution.log | grep "FAILED"  # Quick failure check

# Test database management
python tools/test-db-integration.py utils reset-test-data
python tools/test-db-integration.py utils backup-test-data
```

### **Performance Monitoring**
```bash
# Test execution timing analysis
pytest tests/ --durations=0 | head -20    # Slowest 20 tests
pytest tests/unit/ --benchmark-save=unit_benchmark

# Memory usage profiling
pytest tests/integration/ --profile-svg   # Generate SVG profile
pytest tests/unit/ --memray --memray-bin-path=quality/reports/
```

## 🚨 Test Failure Recovery

### **Systematic Failure Resolution**
```bash
# 1. Identify failure patterns
pytest tests/ --tb=line | grep "FAILED"   # Quick failure list
python tools/failure_tracking_demo.py     # Pattern analysis

# 2. Isolate problematic tests
pytest tests/failing_test.py::test_method -v -s --pdb

# 3. Environment debugging
python tools/test-db-integration.py utils analyze --show-orphaned
python tools/rtm-db.py admin health-check

# 4. Correlation analysis
python tools/log_correlation_demo.py      # Generate correlation data
# View: quality/reports/log_correlation_report.json
```

## 📊 Quality Reporting

### **Comprehensive Test Reports**
```bash
# Generate complete testing report
python tools/report_generator.py --input quality/logs/ --type all

# Testing dashboard generation
python tools/rtm_report_generator.py --html  # RTM with test integration
# Access: http://localhost:8000/api/rtm/reports/matrix?format=html

# Export for stakeholders
python tools/report_generator.py --input quality/logs/ --format csv
```

## 🔗 Integration with Other Agents

- **🔧 Daily Development**: [Daily Dev Agent](.claude/daily-dev.md) - Basic testing commands
- **📚 Documentation**: [Documentation Agent](.claude/documentation.md) - Test documentation
- **🎨 UX/UI**: [UX/UI Agent](.claude/ux-ui-design.md) - UI testing strategies
- **🚨 Emergency**: [Emergency Agent](.claude/emergency.md) - Test failure recovery

---

**📖 Remember**: This agent provides comprehensive testing capabilities. For daily development testing, use the Daily Dev agent. For test failure emergencies, switch to the Emergency agent.