# Development Workflow

**Last Updated**: 2025-09-20

## 🎯 Overview

This document defines the complete development workflow for GoNoGo, integrating BDD practices, requirements traceability, and GDPR compliance into a systematic approach to feature development.

## 📋 Core Development Workflow

### **Phase 1: Requirements Analysis & GitHub Issue Creation**
1. **Read CLAUDE.md** for current project state and commands
2. **Check GitHub Issues** for active epics and user stories
3. **CREATE GITHUB ISSUE** using templates when planning new tasks:
   ```bash
   # For new features/epics
   gh issue create --template epic --title "EP-XXXXX: Feature Name"

   # For specific requirements
   gh issue create --template user-story --title "US-XXXXX: Specific Requirement"

   # For bug fixes
   gh issue create --template defect --title "DEF-XXXXX: Bug Description"
   ```
4. **Review Context** in `docs/context/` for background decisions and compliance
5. **Review BDD Scenarios** in `tests/bdd/features/`
6. **Check RTM Status** in `docs/traceability/requirements-matrix.md`
7. **Verify GDPR Implications** in `docs/context/compliance/gdpr-requirements.md`

### **Phase 2: Test-Driven Implementation**
8. **Write/Update BDD Step Definitions** in `tests/bdd/step_definitions/`
9. **ADD BDD SCENARIOS TO GITHUB ISSUE** in the issue description:
   ```markdown
   ## BDD Scenarios
   - Feature: authentication.feature:user_login
   - Feature: authentication.feature:user_logout
   ```
10. **Run BDD Tests** (should fail - RED phase)
    ```bash
    pytest tests/bdd/ -v --tb=short
    ```
11. **Implement Minimum Code** to make tests pass (GREEN phase)
12. **Refactor** while keeping tests green (REFACTOR phase)
13. **Run Full Test Suite** to ensure no regressions

### **Phase 3: Documentation & Traceability**
14. **UPDATE RTM** in `docs/traceability/requirements-matrix.md` with:
    - Link to GitHub issue
    - Implementation status (⏳ In Progress → ✅ Done)
    - BDD scenario references
    - Test implementation links
15. **Update Technical Docs** if architecture changed (see [Documentation Workflow](documentation-workflow.md))
16. **Verify GDPR Compliance** if personal data involved
17. **Update CLAUDE.md** if workflow or structure changed

### **Phase 4: Quality Gates (MANDATORY) - Enhanced with Structured Logging**
18. **Run Tests with Structured Logging** (generates logs automatically):
    ```bash
    pytest tests/ -v  # Creates quality/logs/test_execution.log
    ```
19. **Generate Test Report** (NEW - review for failures):
    ```bash
    python tools/report_generator.py --input quality/logs/
    # Review quality/reports/test_report.html for issues
    ```
20. **Run Quality Checks** (must pass before commit):
    ```bash
    black src/ tests/ && isort src/ tests/ && flake8 src/ tests/ && mypy src/
    ```
21. **Run Security Tests**: `pytest tests/security/ -v`
22. **Run GDPR Compliance Tests**: `pytest tests/security/test_gdpr_compliance.py -v`
23. **Verify Test Coverage**: `pytest --cov=src tests/ --cov-report=term-missing`
24. **Validate RTM Links** if RTM was modified:
    ```bash
    python tools/rtm-links-simple.py --validate
    ```

### **Phase 5: Integration & GitHub-First Commit**
23. **Integration Test**: `pytest tests/integration/ -v`
24. **E2E Test** (if applicable): `pytest tests/e2e/ -v`
25. **COMMIT WITH GITHUB ISSUE REFERENCE**:
    ```bash
    git commit -m "feat: implement user authentication system

    Implements US-00018: User login with GDPR consent

    - Add login/logout BDD scenarios
    - Implement authentication service
    - Add GDPR consent handling
    - Update RTM with completion status

    🤖 Generated with [Claude Code](https://claude.ai/code)

    Co-Authored-By: Claude <noreply@anthropic.com>"
    ```
26. **COMMENT ON GITHUB ISSUE** with implementation details:
    ```bash
    gh issue comment [ISSUE-NUMBER] --body "
    ## Implementation Completed ✅

    **Files Changed:**
    - \`src/be/services/auth_service.py\` - Authentication logic
    - \`tests/bdd/features/authentication.feature\` - BDD scenarios
    - \`tests/bdd/step_definitions/auth_steps.py\` - Test implementations

    **BDD Scenarios Implemented:**
    - User login with valid credentials
    - User logout functionality
    - GDPR consent validation

    **Quality Gates Passed:**
    - All tests passing ✅
    - Code quality checks passed ✅
    - GDPR compliance validated ✅
    - RTM updated ✅

    **Commit:** [commit-hash]
    "
    ```

## 🔄 BDD Scenario Development Process

### **Writing New BDD Scenarios**
1. **Use Template**: Copy from `tests/bdd/features/scenario-template.feature`
2. **Follow Gherkin Best Practices**:
   - **Given**: Set up initial context
   - **When**: Perform the action
   - **Then**: Verify expected outcome
3. **Tag Appropriately**: `@functional @gdpr @security @performance`
4. **Include GDPR Scenarios**: Always consider privacy implications
5. **Link to User Story**: Reference US-XXX in comments

### **Implementing Step Definitions**
1. **Create Step File**: `tests/bdd/step_definitions/test_[feature]_steps.py`
2. **Import Scenarios**: `scenarios("../features/[feature].feature")`
3. **Implement Steps**: Use `@given`, `@when`, `@then` decorators
4. **Use Fixtures**: Leverage `bdd_context`, `bdd_test_client`, etc.
5. **Mock External Dependencies**: Keep tests isolated

## 📊 Requirements Traceability Matrix (RTM) Updates

### **When to Update RTM**
- New user story implemented
- BDD scenario added or modified
- Code implementation completed
- Test status changed
- Defect discovered or resolved

### **RTM Update Process**
1. **Open**: `docs/traceability/requirements-matrix.md`
2. **Update Status**: Change from 📝 Planned → ⏳ In Progress → ✅ Done
3. **Link Artifacts**: Ensure all columns are filled
4. **Update Metrics**: Recalculate coverage percentages
5. **Note Dependencies**: Update any blocking items
6. **Link Defects**: Update defects column with DEF-XXX references

## 🛡️ GDPR Compliance Integration

### **For Every Feature Involving Personal Data**
1. **Check GDPR Map**: Review `docs/traceability/gdpr-compliance-map.md`
2. **Identify Legal Basis**: Consent, Legitimate Interest, etc.
3. **Implement Privacy by Design**: Minimize data collection
4. **Add GDPR BDD Scenarios**: Test consent, access, erasure
5. **Update Data Processing Records**: Document in RTM

### **GDPR Testing Checklist**
- [ ] Consent collection tested
- [ ] Data minimization verified
- [ ] Retention policies implemented
- [ ] Right to access working
- [ ] Right to erasure working
- [ ] Data export functional

## 🐛 Defect Management Workflow

### **When a Defect is Discovered**
1. **Create GitHub Issue**: Use defect template
2. **Link to Epic/User Story**: Identify related requirements
3. **Assess Business Impact**: Priority, severity, GDPR implications
4. **Update RTM**: Add defect reference to affected requirements
5. **Create Fix BDD Scenario**: Test for the fix (if needed)

### **Defect Resolution Process**
1. **Analyze Root Cause**: Document in GitHub Issue
2. **Fix Implementation**: Follow standard BDD workflow
3. **Update BDD Scenarios**: Prevent regression
4. **Verify Fix**: All acceptance criteria now pass
5. **Update RTM**: Mark defect as resolved
6. **Close GitHub Issue**: Update status and verify date

### **Defect Prevention**
- Review defect patterns monthly
- Update BDD scenarios to catch similar issues
- Improve quality gates based on defect analysis
- Update development guidelines to prevent recurrence

## 📈 Success Metrics

### **Development Quality**
- 100% User Story → BDD Scenario coverage
- 90%+ test coverage maintained
- All GDPR scenarios passing
- Zero high-severity security issues

### **Process Quality**
- RTM updated within 24h of changes
- Documentation current with code
- All commits linked to user stories
- Quality gates passing before merge

## 🔧 Debugging & Troubleshooting with Structured Logging

### **Test Failure Investigation Process**
1. **Check Test Report** (NEW):
   ```bash
   python tools/report_generator.py --input quality/logs/
   # Open quality/reports/test_report.html in browser
   ```

2. **Analyze Structured Logs**:
   ```bash
   # View recent test failures
   cat quality/logs/test_execution.log | grep "failed\|error"

   # Check specific test logs
   python tools/report_generator.py --type unit --input quality/logs/
   ```

3. **Debug with Detailed Mode**:
   ```bash
   # Run failing tests with maximum detail
   pytest --mode=detailed tests/unit/test_failing.py -v
   ```

4. **Verify GDPR Sanitization**:
   ```bash
   # Ensure no personal data in logs
   grep -i "email\|ip.*address" quality/logs/test_*.log  # Should show [REDACTED]
   ```

### **Common Issues and Solutions**
- **No logs generated**: Run pytest first to create logs
- **Empty reports**: Check that tests actually ran (look for test_*.log files)
- **Template errors**: Verify templates exist in quality/reports/templates/
- **Missing dependencies**: `pip install -e ".[dev]" && pip install jinja2`

---

**Related Documentation**:
- [Documentation Workflow](documentation-workflow.md) - How to maintain documentation
- [BDD Scenarios](../../tests/bdd/features/) - Executable test specifications
- [Requirements Matrix](../traceability/requirements-matrix.md) - Current traceability status
- [Quality Assurance Guidelines](quality-assurance.md) - Code standards and testing