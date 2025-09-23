# Pytest Markers Cheatsheet

**Quick Reference for Test Filtering and Organization**

## 📋 Available Markers

| Marker | Purpose | Example | Multiple Values |
|--------|---------|---------|-----------------|
| `user_story` | Link to User Story | `@pytest.mark.user_story("US-00054")` | ✅ Yes |
| `epic` | Link to Epic | `@pytest.mark.epic("EP-00005")` | ✅ Yes |
| `component` | Specify component | `@pytest.mark.component("backend")` | ✅ Yes |
| `defect` | Defect regression | `@pytest.mark.defect("DEF-00010")` | ✅ Yes |
| `priority` | Test priority | `@pytest.mark.priority("critical")` | ❌ No |

## 🏷️ Marker Syntax

### Single Value
```python
@pytest.mark.user_story("US-00054")
@pytest.mark.epic("EP-00005")
@pytest.mark.component("backend")
@pytest.mark.priority("high")
```

### Multiple Values
```python
@pytest.mark.user_story("US-00054", "US-00055")
@pytest.mark.epic("EP-00001", "EP-00005")
@pytest.mark.component("backend", "database", "security")
```

### Complete Example
```python
import pytest

@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00054", "US-00055")
@pytest.mark.component("backend", "database")
@pytest.mark.priority("high")
def test_rtm_sync():
    """Test RTM database synchronization."""
    pass
```

## 🔍 Running Tests by Marker

### Basic Filtering

```bash
# Single user story
pytest -m "user_story=='US-00054'"

# Single epic
pytest -m "epic=='EP-00005'"

# Single component
pytest -m "component=='backend'"

# By priority
pytest -m "priority=='critical'"
```

### Multiple Values (OR Logic)

```bash
# Tests for US-00054 OR US-00055
pytest -m "user_story=='US-00054' or user_story=='US-00055'"

# Tests for backend OR security
pytest -m "component=='backend' or component=='security'"
```

### Combined Filters (AND Logic)

```bash
# Epic AND specific user story
pytest -m "epic=='EP-00005' and user_story=='US-00054'"

# Component AND priority
pytest -m "component=='backend' and priority=='high'"

# Multiple conditions
pytest -m "epic=='EP-00005' and component=='backend' and priority=='critical'"
```

### Negation (NOT Logic)

```bash
# Everything except backend
pytest -m "not component=='backend'"

# High priority, not security
pytest -m "priority=='high' and not component=='security'"
```

## 📊 Common Use Cases

### 1. User Story Testing
```bash
# Test all tests for a user story
pytest -m "user_story=='US-00054'" -v

# User story with specific component
pytest -m "user_story=='US-00054' and component=='backend'"

# Multiple user stories
pytest -m "user_story=='US-00054' or user_story=='US-00055'"
```

### 2. Epic Testing
```bash
# All tests for an epic
pytest -m "epic=='EP-00005'" -v

# Epic with high priority only
pytest -m "epic=='EP-00005' and priority=='high'"

# Epic excluding specific component
pytest -m "epic=='EP-00005' and not component=='frontend'"
```

### 3. Component Regression
```bash
# All backend tests
pytest -m "component=='backend'" -v

# Backend + database tests
pytest -m "component=='backend' and component=='database'"

# Security tests only
pytest -m "component=='security'"
```

### 4. Priority-Based
```bash
# Critical tests (smoke tests)
pytest -m "priority=='critical'" -v

# High priority tests
pytest -m "priority=='high'"

# Critical OR high priority
pytest -m "priority=='critical' or priority=='high'"
```

### 5. Defect Regression
```bash
# Test specific defect fix
pytest -m "defect=='DEF-00010'" -v

# All defect regression tests
pytest -m "defect"

# Recent defects (DEF-00010 and above)
pytest -m "defect=='DEF-00010' or defect=='DEF-00011'"
```

## 🎯 Advanced Patterns

### Cross-Component Testing
```bash
# Tests that touch both auth AND database
pytest -m "component=='auth' and component=='database'"

# Either auth OR gdpr
pytest -m "component=='auth' or component=='gdpr'"
```

### Epic + Priority
```bash
# Critical tests in RTM epic
pytest -m "epic=='EP-00005' and priority=='critical'"

# High priority tests excluding specific epic
pytest -m "priority=='high' and not epic=='EP-00003'"
```

### User Story Coverage
```bash
# All tests for user stories in a range
pytest -m "user_story=='US-00052' or user_story=='US-00053' or user_story=='US-00054'"
```

## 📈 Combining with Other Pytest Options

### With Verbosity
```bash
pytest -m "user_story=='US-00054'" -v          # Verbose
pytest -m "user_story=='US-00054'" -vv         # Extra verbose
```

### With Test Collection
```bash
# See what would run without executing
pytest -m "epic=='EP-00005'" --collect-only
```

### With Coverage
```bash
pytest -m "component=='backend'" --cov=src/be
```

### With Specific Output
```bash
# Only show failures
pytest -m "priority=='critical'" --tb=short

# Stop on first failure
pytest -m "user_story=='US-00054'" -x
```

## 🛠️ Marker Management

### List All Markers
```bash
pytest --markers
```

### Verify Marker Syntax
```bash
# Check for typos or missing markers
python tools/validate_test_associations.py
```

### Coverage Report
```bash
# See marker distribution
python tools/test_coverage_report.py
```

## ⚠️ Common Mistakes

### ❌ Wrong Syntax

```bash
# Missing quotes around value
pytest -m "user_story==US-00054"           # WRONG

# Correct
pytest -m "user_story=='US-00054'"         # CORRECT
```

### ❌ Invalid References

```bash
# Non-existent user story
pytest -m "user_story=='US-99999'"         # May run 0 tests

# Check with validation tool first
python tools/validate_test_associations.py
```

### ❌ Marker Not Applied

```python
# Marker on wrong line
def test_something():
    @pytest.mark.user_story("US-00054")    # WRONG
    pass

# Correct
@pytest.mark.user_story("US-00054")        # CORRECT
def test_something():
    pass
```

## 📝 Priority Levels

| Priority | Use Case | Example |
|----------|----------|---------|
| `critical` | Smoke tests, blocking issues | Login, core workflows |
| `high` | Important features | User creation, data access |
| `medium` | Standard features | UI elements, helpers |
| `low` | Edge cases, nice-to-have | Formatting, tooltips |

## 🔗 Component Names

**Standard components:**
- `backend` - Backend services, APIs
- `frontend` - UI components
- `database` - Database operations
- `security` - Security, GDPR
- `shared` - Shared utilities
- `auth` - Authentication
- `api` - API endpoints

## 📚 Related Commands

```bash
# Full test discovery
pytest --collect-only

# List markers
pytest --markers

# Coverage report
python tools/test_coverage_report.py

# Validation
python tools/validate_test_associations.py

# Database sync
python tools/sync_tests_to_rtm.py
```

## 🎓 Learning Path

1. **Start simple:** `pytest -m "component=='backend'"`
2. **Add filters:** `pytest -m "component=='backend' and priority=='high'"`
3. **Use OR logic:** `pytest -m "user_story=='US-00054' or user_story=='US-00055'"`
4. **Complex queries:** Combine epic + component + priority

## 🆘 Quick Troubleshooting

**No tests found?**
- Check marker spelling: `pytest --markers`
- Validate references: `python tools/validate_test_associations.py`
- Use `--collect-only` to debug

**Unknown marker warning?**
- Marker not registered in `pyproject.toml`
- Check `conftest.py` for custom markers

**Tests not synced?**
- Run: `python tools/sync_tests_to_rtm.py`

---

**Quick Commands:**
```bash
pytest -m "user_story=='US-XXXXX'"                    # User story
pytest -m "epic=='EP-XXXXX'"                          # Epic
pytest -m "component=='backend'"                       # Component
pytest -m "priority=='critical'"                       # Priority
pytest -m "epic=='EP-XXXXX' and component=='backend'" # Combined
```

*Last Updated: 2025-09-23*
*Related: TEST_ORGANIZATION_GUIDE.md, pyproject.toml*