# Test Organization Guide

**QA Team Reference for Test Discovery and Execution**

This guide explains the test organization structure and how to efficiently discover and run tests for the GoNoGo project.

## 📁 Directory Structure

### Overview
```
tests/
├── unit/                    # Component-focused tests
│   ├── backend/            # Backend RTM, filters
│   ├── security/           # GDPR, input validation
│   ├── shared/             # Models, utilities
│   └── [component]/        # Other components
│
├── integration/            # Component interaction tests
│   ├── rtm_api/           # RTM API integration
│   ├── rtm_database/      # RTM database integration
│   ├── rtm_filter/        # RTM filter integration
│   ├── rtm_workflow/      # End-to-end RTM workflows
│   ├── github_rtm/        # GitHub integration
│   ├── component_system/  # Component API tests
│   ├── database_workflow/ # Database workflows
│   └── gdpr_compliance/   # GDPR integration
│
├── e2e/                   # Critical end-to-end journeys
│   └── complete_blog_workflow/
│
└── bdd/                   # Behavior-driven tests
    ├── features/          # .feature files
    └── step_definitions/  # Step implementations
```

### Design Philosophy

**Unit Tests** - Organized by **component**
- Browse by component for focused testing
- Test individual units in isolation
- Fast execution, high coverage

**Integration Tests** - Organized by **combination/feature**
- Tests how components work together
- Grouped by integration point (e.g., rtm_api, rtm_database)
- Validate component interactions

**E2E Tests** - Organized by **use case**
- Complete user workflows
- Critical path testing
- Slower but comprehensive

**BDD Tests** - Keep existing structure
- Feature files in natural language
- Stakeholder-friendly scenarios

## 🏷️ Pytest Markers

All tests are tagged with pytest markers for flexible filtering:

### Available Markers

```python
@pytest.mark.user_story("US-00001", "US-00002")  # Link to user stories
@pytest.mark.epic("EP-00005")                     # Link to epic
@pytest.mark.component("backend", "database")     # Component(s)
@pytest.mark.defect("DEF-00010")                 # Defect regression
@pytest.mark.priority("critical")                 # Test priority
```

### Marker Usage

**Multiple values supported:**
```python
@pytest.mark.epic("EP-00001", "EP-00005")
@pytest.mark.user_story("US-00054", "US-00055")
@pytest.mark.component("backend", "security")
```

## 🚀 Running Tests

### By Folder (Browsing-Based)

```bash
# Test entire component
pytest tests/unit/backend/

# Test specific integration
pytest tests/integration/rtm_filter/

# Test all security tests
pytest tests/unit/security/

# Run E2E tests
pytest tests/e2e/
```

### By Markers (Flexible Filtering)

```bash
# Test specific user story
pytest -m "user_story=='US-00054'"

# Test specific epic
pytest -m "epic=='EP-00005'"

# Component regression
pytest -m "component=='backend'"

# Multiple components (AND)
pytest -m "component=='auth' and component=='database'"

# Priority-based
pytest -m "priority=='critical'"

# Defect regression
pytest -m "defect=='DEF-00010'"
```

### Combined Approaches

```bash
# Folder + marker filtering
pytest tests/unit/backend/ -m "user_story=='US-00054'"

# Component folder with priority
pytest tests/unit/security/ -m "priority=='high'"

# Epic folder with specific US
pytest tests/integration/rtm_workflow/ -m "user_story=='US-00055'"
```

## 📊 Test Discovery Tools

### Coverage Report

**Full coverage overview:**
```bash
python tools/test_coverage_report.py
```

**User Story-specific:**
```bash
python tools/test_coverage_report.py --user-story 54
```

**Example Output:**
```
COVERAGE BY EPIC:
  Requirements Traceability Matrix Automation:
    Tests: 14
    User Stories: 23

COVERAGE BY COMPONENT:
  backend: 14 test(s)
  security: 4 test(s)
  shared: 11 test(s)
```

### Validation Tool

**Check test associations:**
```bash
python tools/validate_test_associations.py
```

**Reports:**
- Orphaned tests (no US/Epic)
- Invalid references
- Database sync status

## 🎯 Common QA Workflows

### 1. Test a User Story

**Option A: By marker**
```bash
pytest -m "user_story=='US-00054'" -v
```

**Option B: Check coverage first**
```bash
python tools/test_coverage_report.py --user-story 54
# Then run specific tests shown
```

### 2. Component Regression

**Option A: Browse by folder**
```bash
pytest tests/unit/backend/ -v
```

**Option B: Filter by marker**
```bash
pytest -m "component=='backend'" -v
```

### 3. Epic Testing

**Option A: By marker**
```bash
pytest -m "epic=='EP-00005'" -v
```

**Option B: Check coverage**
```bash
python tools/test_coverage_report.py
# View "COVERAGE BY EPIC" section
```

### 4. Smoke Tests (Critical Path)

```bash
pytest -m "priority=='critical'" -v
```

### 5. Defect Verification

```bash
pytest -m "defect=='DEF-00010'" -v
```

## 📈 RTM Integration

All test associations are synced to the RTM database:

### View in RTM Dashboard

```bash
# Start server
python -m uvicorn src.be.main:app --reload

# Open RTM dashboard
# http://localhost:8000/api/rtm/reports/matrix?format=html
```

### Sync Tests to Database

```bash
python tools/sync_tests_to_rtm.py
```

### Database Queries

Tests are linked via:
- `github_user_story_number` → User Stories
- `epic_id` → Epics (foreign key)
- `component` → Component tags (CSV for multiple)

## 🔍 Finding Tests

### Scenario: "Which tests cover US-00054?"

**Method 1: Coverage report**
```bash
python tools/test_coverage_report.py --user-story 54
```

**Method 2: Grep for marker**
```bash
grep -r "@pytest.mark.user_story.*US-00054" tests/
```

**Method 3: Pytest collection**
```bash
pytest -m "user_story=='US-00054'" --collect-only
```

### Scenario: "What RTM tests exist?"

**Method 1: Browse folders**
```bash
ls tests/integration/rtm_*/
```

**Method 2: Coverage report**
```bash
python tools/test_coverage_report.py
# Check "COVERAGE BY COMPONENT" for backend
```

### Scenario: "Find orphaned tests"

```bash
python tools/validate_test_associations.py
# Check "ORPHANED TESTS" section
```

## 🛠️ Maintenance

### Adding Markers to New Tests

```python
import pytest

@pytest.mark.epic("EP-00005")
@pytest.mark.user_story("US-00054", "US-00055")
@pytest.mark.component("backend", "database")
@pytest.mark.priority("high")
def test_rtm_database_sync():
    """Test RTM database synchronization."""
    pass
```

### Moving Tests (When US Changes Epic)

```bash
# Run reorganization (dry run first)
python tools/reorganize_tests.py

# Execute
python tools/reorganize_tests.py --execute

# Sync to database
python tools/sync_tests_to_rtm.py
```

## 📝 Best Practices

### For QA Engineers

1. **Start with folders** for browsing and exploration
2. **Use markers** for precise filtering and reporting
3. **Check coverage reports** before testing user stories
4. **Validate associations** regularly to find orphaned tests
5. **Sync to RTM** after adding new test markers

### For Developers

1. **Always add markers** to new tests:
   - user_story (required if known)
   - epic (if known)
   - component (required)
   - priority (recommended)

2. **Use consistent naming**:
   - US-XXXXX format for user stories
   - EP-XXXXX format for epics
   - Lowercase component names

3. **Place tests correctly**:
   - Unit → by component
   - Integration → by combination
   - E2E → by use case

## 🆘 Troubleshooting

### Tests not found by marker

**Check marker syntax:**
```bash
pytest -m "user_story=='US-00054'"  # Correct
pytest -m "user_story==US-00054"    # Wrong (missing quotes)
```

### Invalid marker warnings

Run validation:
```bash
python tools/validate_test_associations.py
```

### Database out of sync

Re-sync:
```bash
python tools/sync_tests_to_rtm.py
```

---

**Quick Reference Card:**
```bash
# Browse by component
pytest tests/unit/backend/

# Filter by user story
pytest -m "user_story=='US-00054'"

# Coverage report
python tools/test_coverage_report.py

# Validate associations
python tools/validate_test_associations.py

# Sync to RTM database
python tools/sync_tests_to_rtm.py
```

*Last Updated: 2025-09-23*
*Related: TEST_REORGANIZATION_PLAN.md, PYTEST_MARKERS_CHEATSHEET.md*