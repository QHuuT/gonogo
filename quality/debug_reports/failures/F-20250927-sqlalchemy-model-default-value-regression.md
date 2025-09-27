# F-20250927 - SQLAlchemy Model Default Value Regression

## Issue Summary

**Type**: F- (Failure) - Critical test regression caused by incomplete SQLAlchemy 2.0 migration
**Date**: 2025-09-27 15:40 UTC
**Severity**: Critical (7 failing tests)
**Impact**: Unit tests failing, zero-tolerance policy violated
**Status**: ✅ RESOLVED

## Root Cause Analysis

### What Happened
During technical debt cleanup focused on line length violations, I attempted to modernize SQLAlchemy imports in `base.py` by converting from old `Column` syntax to new `Mapped` and `mapped_column` syntax. However, I **accidentally removed critical default value assignment logic** from the `__init__` methods of multiple models.

### Technical Details

**Files Affected:**
- `src/be/models/traceability/base.py` - Missing status default assignment
- `src/be/models/traceability/epic.py` - Missing ALL Epic-specific defaults
- `src/be/models/traceability/user_story.py` - Missing UserStory-specific defaults

**Critical Error Pattern:**
```python
# BEFORE (working):
def __init__(self, **kwargs):
    super().__init__(**kwargs)

    # Set default status if not provided
    if self.status is None:
        self.status = "planned"
    # ... other defaults

# AFTER my changes (broken):
def __init__(self, **kwargs: Any) -> None:
    super().__init__(**kwargs)
    # MISSING: All default value assignment logic!
```

### Tests That Failed
1. `test_epic_creation` - `epic.total_story_points` was None instead of 0
2. `test_calculate_completion_percentage_zero_points` - Default values missing
3. `test_to_dict_basic` - Status None instead of "planned"
4. `test_repr` - TypeError on None values in format strings
5. `test_default_values` (Epic) - Multiple None values instead of defaults
6. `test_default_values` (Test model) - Status None instead of "planned"
7. `test_default_values` (UserStory) - Priority None instead of "medium"

## Impact Assessment

### Immediate Impact
- **ALL unit tests affected**: 7 explicit failures + potential cascading issues
- **Zero-tolerance policy violated**: Development blocked per README protocol
- **Model behavior broken**: Database entities created with None values instead of proper defaults

### Why This Was Critical
- SQLAlchemy 2.0 `default=` in column definitions ≠ Python object initialization defaults
- The original code relied on explicit `__init__` logic for NOT NULL constraints
- Removing this logic broke core model functionality across the inheritance hierarchy

## Solution Implemented

### Step 1: Root Cause Identification
Used git diff to compare with working version:
```bash
git diff HEAD~1 src/be/models/traceability/base.py
```

### Step 2: Restore Default Assignment Logic
**TraceabilityBase (`base.py`):**
```python
def __init__(self, **kwargs: Any) -> None:
    """Initialize TraceabilityBase with default values."""
    super().__init__(**kwargs)

    # Set default status if not provided
    if self.status is None:
        self.status = "planned"
```

**Epic Model (`epic.py`):**
```python
# Set defaults for fields that are NOT NULL
if self.total_story_points is None:
    self.total_story_points = 0
if self.completed_story_points is None:
    self.completed_story_points = 0
if self.completion_percentage is None:
    self.completion_percentage = 0.0
if self.priority is None:
    self.priority = "medium"
if self.risk_level is None:
    self.risk_level = "medium"
if self.gdpr_applicable is None:
    self.gdpr_applicable = False
if self.component is None:
    self.component = "backend"
```

**UserStory Model (`user_story.py`):**
```python
# Set defaults for fields that are NOT NULL
if self.story_points is None:
    self.story_points = 0
if self.priority is None:
    self.priority = "medium"
if self.implementation_status is None:
    self.implementation_status = "todo"
if self.has_bdd_scenarios is None:
    self.has_bdd_scenarios = False
if self.affects_gdpr is None:
    self.affects_gdpr = False
```

### Step 3: Validation
- **Syntax validation**: All modified files pass `ast.parse()`
- **Individual test validation**: Each originally failing test now passes
- **Comprehensive validation**: All 327 unit tests pass
- **Regression test**: Comprehensive syntax validation confirms no new issues

## Prevention Measures

### Immediate Actions Taken
1. **Complete restoration** of all default assignment logic
2. **Comprehensive test validation** following README mandatory protocol
3. **Documentation** of this regression pattern for future reference

### Process Improvements
1. **Never modify `__init__` methods without understanding their purpose**
2. **Always compare git diffs when modernizing SQLAlchemy code**
3. **Understand that SQLAlchemy column `default=` ≠ Python object defaults**
4. **Test immediately after each model modification**

### Updated Development Protocol
```bash
# MANDATORY when modifying SQLAlchemy models:
# 1. Check for existing default assignment logic
git show HEAD:path/to/model.py | grep -A 20 "def __init__"

# 2. Preserve ALL existing initialization logic
# 3. Validate syntax after EACH file modification
python -c "import ast; ast.parse(open('modified_file.py').read())"

# 4. Run unit tests after EACH model change
pytest tests/unit/shared/models/ -v

# 5. NEVER assume column defaults handle Python object initialization
```

## Lessons Learned

### Technical Insights
1. **SQLAlchemy 2.0 Migration Complexity**: Column `default=` parameters are for database schema, not Python object initialization
2. **Inheritance Chain Dependencies**: Changes to base classes cascade through entire model hierarchy
3. **Test Failure Patterns**: None values in format strings cause TypeErrors, revealing initialization issues

### Process Insights
1. **README Protocol Effectiveness**: The mandatory testing protocol caught this immediately
2. **Zero-Tolerance Policy Value**: Prevented shipping broken model initialization
3. **Git History Critical**: Previous working implementation was essential for diagnosis

## Cross-References

### Related Debug Reports
- **F-20250927-technical-debt-cleanup-test-regression.md**: Import cleanup safety protocols
- **Future**: Any SQLAlchemy 2.0 migration reports should reference this pattern

### Documentation Updates
- This report should inform any future SQLAlchemy modernization efforts
- Model initialization patterns should be documented in development guides

## Verification

### Resolution Confirmed
- ✅ All 7 originally failing tests now pass
- ✅ All 327 unit tests pass (full regression validation)
- ✅ All modified files have valid syntax
- ✅ No new issues introduced in files I modified

### Monitoring
- SQLAlchemy model tests should be monitored for similar default value issues
- Future SQLAlchemy migrations should reference this debug report

---

**Resolution Time**: ~30 minutes from detection to full validation
**Key Learning**: Always preserve existing initialization logic when modernizing SQLAlchemy models
