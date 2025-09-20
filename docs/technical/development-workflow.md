# Development Workflow

**Last Updated**: 2025-09-20

## 🎯 Overview

This document defines the complete development workflow for GoNoGo, integrating BDD practices, requirements traceability, and GDPR compliance into a systematic approach to feature development.

## 📋 Core Development Workflow

### **Phase 1: Requirements Analysis**
1. **Read CLAUDE.md** for current project state and commands
2. **Check GitHub Issues** for active epics and user stories
3. **Review Context** in `docs/context/` for background decisions and compliance
4. **Review BDD Scenarios** in `tests/bdd/features/`
5. **Check RTM Status** in `docs/traceability/requirements-matrix.md`
6. **Verify GDPR Implications** in `docs/context/compliance/gdpr-requirements.md`

### **Phase 2: Test-Driven Implementation**
7. **Write/Update BDD Step Definitions** in `tests/bdd/step_definitions/`
8. **Run BDD Tests** (should fail - RED phase)
   ```bash
   pytest tests/bdd/ -v --tb=short
   ```
9. **Implement Minimum Code** to make tests pass (GREEN phase)
10. **Refactor** while keeping tests green (REFACTOR phase)
11. **Run Full Test Suite** to ensure no regressions

### **Phase 3: Documentation & Traceability**
12. **Update RTM** in `docs/traceability/requirements-matrix.md`
13. **Update Technical Docs** if architecture changed (see [Documentation Workflow](documentation-workflow.md))
14. **Verify GDPR Compliance** if personal data involved
15. **Update CLAUDE.md** if workflow or structure changed

### **Phase 4: Quality Gates**
16. **Run Quality Checks**:
    ```bash
    black src/ tests/ && isort src/ tests/ && flake8 src/ tests/ && mypy src/
    ```
17. **Run Security Tests**: `pytest tests/security/ -v`
18. **Run GDPR Compliance Tests**: `pytest tests/security/test_gdpr_compliance.py -v`
19. **Verify Test Coverage**: `pytest --cov=src tests/ --cov-report=term-missing`

### **Phase 5: Integration & Commit**
20. **Integration Test**: `pytest tests/integration/ -v`
21. **E2E Test** (if applicable): `pytest tests/e2e/ -v`
22. **Commit with Conventional Message**:
    ```bash
    git commit -m "feat: implement [user story] with BDD coverage

    - Add BDD scenarios for [feature]
    - Implement [specific functionality]
    - Update RTM with traceability
    - Ensure GDPR compliance

    Closes: US-XXX
    Tests: BDD scenarios passing
    Coverage: XX% maintained"
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

---

**Related Documentation**:
- [Documentation Workflow](documentation-workflow.md) - How to maintain documentation
- [BDD Scenarios](../../tests/bdd/features/) - Executable test specifications
- [Requirements Matrix](../traceability/requirements-matrix.md) - Current traceability status