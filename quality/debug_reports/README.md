# Debug Reports

This folder contains detailed debug reports and analysis documentation for issues, fixes, and regression prevention measures.

## Naming Convention

All debug reports should follow this naming pattern:
```
[F-|W-]YYYYMMDD-short-descriptive-name.md
```

### Prefixes
- **F-** (Failure): System failures, critical errors, broken functionality, test failures
- **W-** (Warning): Performance issues, potential problems, non-critical issues, improvement opportunities

**Examples:**
- `F-20250926-cli-commands-rich-console-testability.md` (Test failures)
- `F-20250925-database-connection-timeout-analysis.md` (System failure)
- `W-20250924-epic-model-performance-optimization.md` (Performance warning)
- `F-20250923-api-500-error-regression-tests.md` (Critical failure)
- `W-20250922-memory-usage-trends-analysis.md` (Resource warning)

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

### 🚨 F- (Failure) Reports
Critical system failures requiring immediate investigation and resolution.

#### 🐛 Bug Analysis Reports (F-)
Detailed analysis of bugs, their root causes, and fixes.
- **F-** System crashes, broken functionality, critical bugs
- **F-** Test failures, integration failures
- **F-** Security vulnerabilities with active exploitation risk

#### 🔧 System Failure Reports (F-)
Documentation of system outages and critical issues.
- **F-** Database connection failures
- **F-** API endpoint failures (500 errors)
- **F-** Authentication/authorization failures
- **F-** Data corruption or loss incidents

### ⚠️ W- (Warning) Reports
Non-critical issues requiring attention and analysis.

#### 📊 Performance Investigation Reports (W-)
Analysis of performance issues and optimizations.
- **W-** Slow database query optimization
- **W-** API response time degradation
- **W-** Memory usage trend analysis
- **W-** Resource utilization concerns

#### 🔍 Security Analysis Reports (W-)
Security-related investigations and improvements.
- **W-** Potential vulnerability analysis
- **W-** Security hardening recommendations
- **W-** Compliance gap analysis

#### 🔧 Process Improvement Reports (W-)
Documentation of process enhancements and preventive measures.
- **W-** Code quality improvements
- **W-** Development workflow optimizations
- **W-** Monitoring and alerting enhancements

## Usage Guidelines

### Before Creating a New Debug Report

**ALWAYS check for similar existing issues first:**

1. **Search existing debug reports** in this folder for similar patterns:
   ```bash
   # Search for similar technical issues
   grep -r "Rich console" quality/debug_reports/
   grep -r "Click test" quality/debug_reports/
   grep -r "database connection" quality/debug_reports/

   # Search by file patterns and prefixes
   ls quality/debug_reports/F-*cli*        # Failure reports related to CLI
   ls quality/debug_reports/W-*performance* # Warning reports related to performance
   ls quality/debug_reports/F-*test*       # Failure reports related to testing
   ls quality/debug_reports/W-*            # All warning reports
   ls quality/debug_reports/F-*            # All failure reports
   ```

2. **Review related reports** to identify patterns:
   - Same root cause (e.g., Rich console vs Click echo)
   - Same component (e.g., CLI commands, API endpoints)
   - Same error type (e.g., testability issues, database errors)

3. **Decision matrix** for update vs new report:

| Scenario | Action | Rationale |
|----------|--------|-----------|
| **Exact same root cause, same component** | Update existing report | Add new instance, update prevention measures |
| **Same pattern, different component** | Create new report, reference existing | Document pattern spread, cross-reference |
| **Same component, different root cause** | Create new report, reference existing | Different technical issue, maintain separation |
| **Follow-up issue from previous fix** | Update existing report | Part of same debugging effort |

### When to Update Existing Reports

**Update an existing report when:**
- Same technical root cause occurs in different location
- Additional debugging information discovered
- Prevention measures need enhancement
- Follow-up issues from same fix
- Pattern recognition reveals systemic issue

**Example Update Scenarios:**
- **CLI Rich Console Issue**: If health-check and validate commands have same Rich console testability issue, consolidate into single comprehensive report covering both commands
- **Database Connection Pattern**: Multiple commands showing same connection handling issue
- **API Error Handling**: Same error handling pattern across different endpoints

### When to Create New Reports

**Create a new report when:**
- Fundamentally different root cause
- Different system component involved
- New category of issue (performance vs functional vs security)
- Complex issue requiring full investigation documentation

### Report Creation Process

1. **Search for similar issues** (5-10 minutes):
   ```bash
   # Technical pattern search
   find quality/debug_reports/ -name "*.md" -exec grep -l "keyword" {} \;

   # Prefix and component-based search
   find quality/debug_reports/ -name "F-*component*"  # Failure reports for component
   find quality/debug_reports/ -name "W-*component*"  # Warning reports for component

   # Recent reports check by type
   ls -la quality/debug_reports/F-* | head -5        # Recent failure reports
   ls -la quality/debug_reports/W-* | head -5        # Recent warning reports
   ls -la quality/debug_reports/ | head -10          # All recent reports
   ```

2. **If similar issue found**:
   - Read existing report thoroughly
   - Determine if update or new report needed
   - If updating: Add "Additional Instance" or "Pattern Update" section
   - If new: Reference existing report in "Related Issues" section

3. **Document pattern recognition**:
   - Note if this is second+ occurrence of same pattern
   - Update prevention measures in original report if applicable
   - Cross-reference between related reports

4. **Include code snippets** and logs where relevant
5. **Document team knowledge** to help future debugging efforts

### Cross-Referencing Guidelines

**In new reports**, always include:
- **Similar Past Issues**: Links to related debug reports
- **Pattern References**: Note if this continues an established pattern
- **Prevention Updates**: Reference if existing prevention measures need updating

**In updated reports**, add sections:
- **Pattern Spread** (YYYY-MM-DD): Document where else this issue appeared
- **Additional Instances**: New occurrences with brief summary
- **Enhanced Prevention**: Updated measures based on pattern recognition

### Examples

**Consolidation Scenario:**
```markdown
# Consolidated: F-20250926-cli-commands-rich-console-testability.md

## Issue Summary
- **Problem**: RTM database CLI commands (health check and validate) test failures due to Rich console output not being captured by Click test runner
- **Resolution**: Consolidated both issues into single comprehensive failure report
- **Prefix**: F- (Failure) - Test failures blocking development workflow

## Solution Implemented
### Fix Description
Changed multiple CLI commands from Rich console output to Click echo:

**Health Check Command:** tools/rtm-db.py:516
**Validate Command:** tools/rtm-db.py:588, tools/rtm-db.py:580

### Total Coverage
10 CLI tests (4 health check + 6 validate) ensuring comprehensive regression prevention
```

**New Report Scenarios:**
```markdown
# Failure Report: F-20250926-api-500-errors-dashboard.md
- **Type**: F- (Critical system failure)
- **Reason**: API endpoints returning 500 errors, users unable to access dashboard

# Warning Report: W-20250926-database-query-performance.md
- **Type**: W- (Performance warning)
- **Reason**: Database queries taking >2 seconds, but system still functional

## Related Issues
- **Similar Pattern**: F-20250926-cli-commands-rich-console-testability.md
- **Same Component**: CLI commands, but different severity (API failure vs testability)
- **Pattern Type**: Critical failure vs warning issue
```

## Report Templates

### Bug Report Template
```markdown
# [F-|W-][YYYYMMDD] - [Issue Title]

**Prefix Selection Guide:**
- Use **F-** for: System failures, critical errors, broken functionality, test failures, security vulnerabilities
- Use **W-** for: Performance issues, potential problems, non-critical issues, improvement opportunities

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