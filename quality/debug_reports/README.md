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
- **Problem**: [Clear description of the issue]
- **Impact**: [What was affected - users, features, performance, etc.]
- **Severity**: Critical | High | Medium | Low
- **Discovery Date**: [YYYY-MM-DD HH:MM]
- **Resolution Date**: [YYYY-MM-DD HH:MM]
- **Resolution Time**: [Duration from discovery to fix]
- **Reporter**: [Who discovered the issue]
- **Environment**: [Production | Staging | Development | Test]

## Debugging Information

### Error Details
```
[Include full error messages, exceptions, or failure descriptions]
```

### Stack Trace
```
[Full stack trace if available - critical for debugging]
```

### Log Excerpts
```
[Relevant log entries showing the issue]
```

### Environment Context
- **OS**: [Windows/Linux/macOS version]
- **Python Version**: [e.g., 3.13.7]
- **Dependencies**: [Key package versions if relevant]
- **Database**: [SQLite version, file size, etc.]
- **Browser**: [If web-related issue]
- **Network**: [If connectivity-related]

### Reproduction Steps
1. [Step-by-step instructions to reproduce the issue]
2. [Include specific commands, URLs, or user actions]
3. [Note any timing or sequence dependencies]

### Data State
- **Database State**: [Relevant table counts, data conditions]
- **File System**: [File permissions, disk space, etc.]
- **Configuration**: [Relevant config values]
- **User Context**: [Logged in user, permissions, etc.]

## Root Cause Analysis

### Investigation Process
[Detailed investigation steps taken to identify the root cause]
- [Tools used: debugger, logs, database queries, etc.]
- [Hypotheses tested and ruled out]
- [Key breakthrough moments in investigation]

### Root Cause
[Technical explanation of what caused the problem]

### Contributing Factors
[Secondary causes or conditions that enabled the issue]

### Timeline
- **[HH:MM]** - [Issue first occurred/discovered]
- **[HH:MM]** - [Investigation began]
- **[HH:MM]** - [Key findings or breakthrough]
- **[HH:MM]** - [Root cause identified]
- **[HH:MM]** - [Fix implemented]
- **[HH:MM]** - [Fix verified]

## Solution Implemented

### Fix Description
[What was changed to resolve the issue]

### Code Changes
**Files Modified:**
- `path/to/file1.py` - [Description of changes]
- `path/to/file2.py` - [Description of changes]

**Before/After Code Snippets:**
```python
# Before (problematic code)
[original code]

# After (fixed code)
[new code]
```

### Configuration Changes
[Any config file modifications, environment variable changes]

### Database Changes
[Schema updates, data migrations, index additions]

### Testing
[How the fix was validated]
- **Unit Tests**: [New/modified tests]
- **Manual Testing**: [Verification steps]
- **Performance Testing**: [If performance-related]

## Prevention Measures

### Regression Tests
[Tests added to prevent this issue from recurring]
- **Test Files**: [List of test files created/modified]
- **Test Coverage**: [What scenarios are now covered]
- **Automation**: [How tests are integrated into CI/CD]

### Monitoring
[Additional monitoring or alerts implemented]
- **Metrics**: [What is now being tracked]
- **Alerts**: [When and how team is notified]
- **Dashboards**: [Visual monitoring added]

### Process Improvements
[Changes to development/deployment processes]
- **Code Review**: [New checklist items]
- **Testing**: [Additional testing requirements]
- **Documentation**: [Knowledge sharing improvements]

### Early Detection
[How similar issues can be caught earlier]
- **Static Analysis**: [New linting rules, type checking]
- **Integration Tests**: [Additional test scenarios]
- **Performance Monitoring**: [Metrics to watch]

## Lessons Learned

### What Went Well
[Positive aspects of the debugging and resolution process]

### What Could Be Improved
[Areas for process enhancement or tools needed]

### Knowledge Gained
[Technical insights for future reference]
- **Technical**: [New understanding of system behavior]
- **Process**: [Workflow improvements identified]
- **Tools**: [Better debugging techniques discovered]

## Reference Information

### Related Issues
- **GitHub Issues**: [#123, #456]
- **Epic/User Story**: [EP-00005, US-00055]
- **Similar Past Issues**: [Links to related debug reports]

### Documentation Updated
- [List of docs that were updated as a result]
- [New documentation created]

### Team Communication
- **Notifications Sent**: [When and to whom]
- **Knowledge Sharing**: [Team meetings, documentation]
- **Stakeholder Updates**: [Customer/management communication]

## Appendix

### Additional Logs
```
[Extended log files, debug output, or raw data]
```

### Screenshots
[If UI-related, include before/after screenshots]

### Performance Data
[Metrics, timing data, resource usage before/after]

### External References
- [Stack Overflow posts consulted]
- [Documentation references]
- [Third-party issue trackers]
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