# GitHub Issue Creation Guide

**Last Updated**: 2025-09-20
**Purpose**: Standardized process for creating GitHub issues following enhanced GitHub-first workflow protocol

## 🎯 Overview

This guide provides step-by-step instructions for creating GitHub issues using the CLI, avoiding common errors, and ensuring proper ID sequencing following the CLAUDE.md protocol.

## 📋 Pre-Creation Checklist

### **Step 1: Follow CLAUDE.md Protocol**
- [ ] Read CLAUDE.md completely
- [ ] Check current GitHub issues for assigned work
- [ ] Review Requirements Matrix for current status

### **Step 2: Determine Next Available ID**
```bash
# Check existing issues to avoid duplicates
gh issue list --limit 50 --state all --json number,title

# Look for highest existing IDs:
# EP-XXXXX (Epics)
# US-XXXXX (User Stories)
# DEF-XXXXX (Defects)
```

**Current ID Status** (as of 2025-09-20):
- **Epics**: EP-00001 to EP-00005 (next: EP-00006)
- **User Stories**: US-00001 to US-00017 (next: US-00018)
- **Defects**: DEF-00001 to DEF-00002 (next: DEF-00003)

### **Step 3: Check Available Labels**
```bash
# Verify labels exist before using them
gh label list --limit 30
```

**Standard Label Categories**:
- **Type**: `epic`, `user-story`, `defect`
- **Priority**: `priority/critical`, `priority/high`, `priority/medium`, `priority/low`
- **Epic**: `epic/blog-content`, `epic/comment-system`, `epic/github-workflow`, `epic/privacy-consent`
- **Status**: `status/backlog`, `status/ready`, `status/in-progress`, `status/testing`, `status/done`
- **Component**: `component/frontend`, `component/backend`

## 🔧 Issue Creation Commands

### **For Epics (EP-XXXXX)**
```bash
gh issue create \
  --title "EP-00006: [Epic Name]" \
  --body "## Epic Description

[Detailed epic description]

## User Stories
- US-XXXXX: [User story 1]
- US-XXXXX: [User story 2]

## Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Story Points Estimate
[Total points]

**Priority**: [High/Medium/Low]
**Release**: [v1.0/v1.1/etc]" \
  --label "epic,priority/high,epic/[category],status/backlog"
```

### **For User Stories (US-XXXXX)**
```bash
gh issue create \
  --title "US-00018: [User Story Title]" \
  --body "## User Story

As a [user type], I want [functionality] so that [benefit].

## Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

## BDD Scenarios
- [feature-name.feature:scenario_name]

## Technical Notes
[Implementation details]

## Definition of Done
- [ ] BDD scenarios written and passing
- [ ] Unit tests implemented
- [ ] Code reviewed and merged
- [ ] RTM updated

**Epic**: EP-XXXXX
**Story Points**: [1-8]
**Priority**: [High/Medium/Low]" \
  --label "user-story,priority/medium,epic/[category],status/backlog,component/backend"
```

### **For Defects (DEF-XXXXX)**
```bash
gh issue create \
  --title "DEF-00003: [Brief defect description]" \
  --body "## 🐛 Problem Description

[Clear description of the issue]

## 📍 Expected Behavior

[What should happen]

## 📍 Actual Behavior

[What actually happens]

## 🔍 Steps to Reproduce

1. [Step 1]
2. [Step 2]
3. [Step 3]

## 🔍 Root Cause Analysis

[Technical analysis of the issue]

## 📋 Files Affected

- \`file1.py\` - [Description]
- \`file2.md\` - [Description]

## 🔧 Proposed Solution

[Solution approach]

## ✅ Acceptance Criteria

- [ ] [Fix criterion 1]
- [ ] [Fix criterion 2]

**Priority**: [Critical/High/Medium/Low]
**Epic**: [Related Epic if applicable]
**Related Issues**: [US-XXXXX, etc.]" \
  --label "defect,priority/high,epic/[category],component/backend"
```

## ⚠️ Common Errors and Solutions

### **Error 1: `--template` is not supported when using `--body`**
**Solution**: Choose either template OR body, not both:
```bash
# Use template (requires interactive mode)
gh issue create --template defect --title "Title"

# OR use body (non-interactive)
gh issue create --title "Title" --body "Content"
```

### **Error 2: `could not add label: 'label-name' not found`**
**Solution**: Check available labels first:
```bash
gh label list --limit 30
# Use exact label names from the list
```

### **Error 3: `must provide --title and --body when not running interactively`**
**Solution**: Always provide both title and body for CLI usage:
```bash
gh issue create --title "Required Title" --body "Required body content"
```

### **Error 4: Duplicate Issue IDs**
**Solution**: Always check existing issues first:
```bash
gh issue list --limit 50 --state all | grep -E "(EP-|US-|DEF-)"
```

## 🔄 Post-Creation Workflow

### **Step 1: Update RTM Immediately**
After creating the issue, update `docs/traceability/requirements-matrix.md`:

1. **Add to Epic Mapping Table** (if epic):
   ```markdown
   | **EP-00006** | [Epic Name] | US-XXXXX, US-XXXXX | [Points] | [Priority] | 📝 Planned |
   ```

2. **Add to Main RTM Table**:
   ```markdown
   | [**EP-XXXXX**](https://github.com/QHuuT/gonogo/issues/[NUMBER]) | **REQ-001** | [Description] | [Priority] | [US-XXXXX](https://github.com/QHuuT/gonogo/issues/[NUMBER]) | [scenario] | [test] | [impl] | - | 📝 Planned | [Notes] |
   ```

### **Step 2: Comment on Issue** (following CLAUDE.md protocol):
```bash
gh issue comment [ISSUE-NUMBER] --body "## Issue Created ✅

Created following enhanced GitHub-first workflow protocol from CLAUDE.md.

**Next Steps:**
- [ ] Add to Requirements Traceability Matrix
- [ ] Create BDD scenarios if applicable
- [ ] Begin implementation when ready

**RTM Status**: Added to requirements matrix
**Workflow Phase**: Planning Complete"
```

### **Step 3: Validate RTM Links**
```bash
python tools/rtm-links-simple.py --validate
```

## 📚 Quick Reference Commands

```bash
# Check next available IDs
gh issue list --limit 50 --state all | grep -E "(EP-|US-|DEF-)" | tail -10

# Check available labels
gh label list | grep -E "(priority|epic|component|status)"

# Create epic
gh issue create --title "EP-XXXXX: Title" --body "Content" --label "epic,priority/high,epic/category,status/backlog"

# Create user story
gh issue create --title "US-XXXXX: Title" --body "Content" --label "user-story,priority/medium,epic/category,status/backlog,component/backend"

# Create defect
gh issue create --title "DEF-XXXXX: Title" --body "Content" --label "defect,priority/high,epic/category,component/backend"

# Update RTM after creation
# Edit docs/traceability/requirements-matrix.md manually

# Validate RTM
python tools/rtm-links-simple.py --validate
```

## 🔧 Automation Scripts

### **Future Enhancement**: Create issue ID helper script
```bash
# Create tools/next-issue-id.py for automated ID generation
python tools/next-issue-id.py --type defect  # Returns: DEF-00003
python tools/next-issue-id.py --all          # Shows all next IDs
```

### **Integration with RTM Automation**
When creating issues, the RTM automation system should:
1. Auto-detect new GitHub issues
2. Generate direct issue links (not search links)
3. Update RTM automatically
4. Validate all links work correctly

---

**Related Documentation**:
- [CLAUDE.md](../../CLAUDE.md) - Enhanced GitHub-first workflow protocol
- [Development Workflow](development-workflow.md) - Complete development process
- [Documentation Workflow](documentation-workflow.md) - RTM update requirements
- [Requirements Matrix](../traceability/requirements-matrix.md) - Current RTM status