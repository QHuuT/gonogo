# Debug Reports

This folder contains detailed debug reports and analysis documentation for issues, fixes, and regression prevention measures.

## Naming Convention

All debug reports should follow this naming pattern:
```
YYYYMMDD-short-descriptive-name.md
```

**Examples:**
- `20250926-metrics-api-500-error-regression-tests.md`
- `20250925-database-connection-timeout-analysis.md`
- `20250924-epic-model-performance-optimization.md`

## File Structure

Each debug report should include:

### 1. Issue Summary
- **Problem Description**: Clear description of the issue
- **Impact**: What was affected (users, features, performance)
- **Severity**: Critical, High, Medium, Low
- **Timeline**: When discovered, time to resolution

### 2. Root Cause Analysis
- **Investigation Process**: Steps taken to identify the issue
- **Root Cause**: Technical explanation of what caused the problem
- **Contributing Factors**: Secondary causes or conditions

### 3. Solution Implemented
- **Fix Description**: What was changed to resolve the issue
- **Code Changes**: Files modified, functions added/updated
- **Testing**: How the fix was validated

### 4. Prevention Measures
- **Regression Tests**: Tests added to prevent recurrence
- **Monitoring**: Additional monitoring or alerts implemented
- **Process Improvements**: Changes to development/deployment processes

### 5. Lessons Learned
- **What Went Well**: Positive aspects of the debugging process
- **What Could Be Improved**: Areas for process enhancement
- **Knowledge Gained**: Technical insights for future reference

## Types of Debug Reports

### 🐛 Bug Analysis Reports
Detailed analysis of bugs, their root causes, and fixes.
- Performance issues
- Functional bugs
- Integration problems
- Security vulnerabilities

### 🔧 Regression Prevention Reports
Documentation of regression tests and prevention measures.
- Test suite creation
- Monitoring setup
- Process improvements

### 📊 Performance Investigation Reports
Analysis of performance issues and optimizations.
- Database query optimization
- API response time improvements
- Memory usage analysis

### 🔍 Security Investigation Reports
Security-related debugging and hardening measures.
- Vulnerability analysis
- Security fix implementation
- Compliance improvements

## Usage Guidelines

1. **Create a report** for any significant debugging effort (>2 hours investigation)
2. **Update existing reports** if new information is discovered
3. **Reference related issues** using GitHub issue numbers or Epic IDs
4. **Include code snippets** and logs where relevant
5. **Document team knowledge** to help future debugging efforts

## Report Templates

### Bug Report Template
```markdown
# [YYYYMMDD] - [Issue Title]

## Issue Summary
- **Problem**:
- **Impact**:
- **Severity**:
- **Discovery Date**:
- **Resolution Date**:

## Root Cause Analysis
### Investigation Process
### Root Cause
### Contributing Factors

## Solution Implemented
### Fix Description
### Code Changes
### Testing

## Prevention Measures
### Regression Tests
### Monitoring
### Process Improvements

## Lessons Learned
### What Went Well
### What Could Be Improved
### Knowledge Gained
```

## Maintenance

- **Review quarterly** to identify patterns and systemic issues
- **Archive old reports** (>1 year) to `quality/archives/debug_reports/`
- **Update naming conventions** as needed for clarity
- **Cross-reference** with related documentation in other quality folders

## Related Folders

- `quality/logs/` - Raw log files and test outputs
- `quality/reports/` - Automated quality reports
- `quality/archives/` - Historical documentation
- `tests/` - Actual test implementations referenced in debug reports