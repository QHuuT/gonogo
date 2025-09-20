# Defect Template

**Defect ID**: DEF-XXX
**Related Epic**: [EP-XXX: Epic Name](epics/EP-XXX-epic-name.md)
**Related User Story**: [US-XXX: Story Name](user-stories/US-XXX-story-name.md)
**Priority**: Critical/High/Medium/Low
**Severity**: Blocker/Critical/Major/Minor/Trivial

## Defect Summary
Brief one-line description of the defect

## Environment
- **Browser/Platform**: [Browser version, OS, device type]
- **Environment**: [Local/Staging/Production]
- **Version**: [App version or commit hash]

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen according to the user story acceptance criteria

## Actual Behavior
What actually happens

## Business Impact
- **User Impact**: [How many users affected, severity of impact]
- **Business Value Lost**: [Revenue, engagement, compliance risk]
- **Workaround Available**: [Yes/No - describe if yes]

## GDPR Considerations (if applicable)
### Privacy Impact
- **Personal Data Affected**: [None/Low/Medium/High]
- **Compliance Risk**: [None/Low/Medium/High]
- **Data Subject Rights Impacted**: [List any rights affected]

### Immediate Actions Required
- [ ] Data breach assessment needed
- [ ] User notification required
- [ ] Consent system affected
- [ ] Data retention impacted

## Evidence
### Screenshots/Videos
- [Attach screenshots or videos]

### Error Messages/Logs
```
[Paste error messages or relevant log entries]
```

### Network/Console Logs
```
[Browser console errors, network failures, etc.]
```

## Acceptance Criteria Violated
Reference specific acceptance criteria from the related user story:
- [ ] **AC-X**: [Copy violated acceptance criteria]
- [ ] **NFR-X**: [Copy violated non-functional requirement]

## Root Cause Analysis (when identified)
- **Category**: [Code defect/Design flaw/Integration issue/Data issue/Configuration]
- **Root Cause**: [Detailed explanation]
- **Contributing Factors**: [What led to this defect]

## Fix Implementation
### Technical Solution
- [ ] Code changes required
- [ ] Database changes required
- [ ] Configuration changes required
- [ ] Infrastructure changes required

### Testing Requirements
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] BDD scenarios updated
- [ ] Manual testing completed
- [ ] Regression testing completed

### Verification Steps
1. [How to verify the fix works]
2. [How to verify no regression introduced]

## Definition of Done
- [ ] Root cause identified and documented
- [ ] Fix implemented and tested
- [ ] All acceptance criteria now pass
- [ ] No regression in related functionality
- [ ] BDD scenarios updated if needed
- [ ] Documentation updated if needed
- [ ] Code reviewed and approved
- [ ] Deployed to staging and verified
- [ ] RTM updated with fix traceability

## Links
- **Epic**: [EP-XXX: Epic Name](epics/EP-XXX-epic-name.md)
- **User Story**: [US-XXX: Story Name](user-stories/US-XXX-story-name.md)
- **BDD Scenarios**: [feature-name.feature](../02-technical/bdd-scenarios/feature-name.feature)
- **RTM Entry**: [Requirements Matrix](../traceability/requirements-matrix.md)
- **Related Defects**: [List any related defects]

## Defect Lifecycle
**Created**: [Date]
**Assigned**: [Developer]
**Status**: New/Assigned/In Progress/Testing/Resolved/Closed/Reopened
**Resolution**: [Fixed/Won't Fix/Duplicate/Not Reproducible/By Design]
**Resolved Date**: [Date]
**Verified By**: [Tester/Product Owner]

---
**Reporter**: [Name]
**Assignee**: [Name]
**Last Updated**: [Date]