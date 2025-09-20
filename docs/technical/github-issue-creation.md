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

### **Step 4: GitHub Project Setup**
```bash
# Check current authentication status
gh auth status

# Refresh authentication with project scope (if needed)
gh auth refresh -s project -h github.com

# List existing projects
gh project list --owner QHuuT

# Get project ID for GoNoGo project
export GONOGO_PROJECT_ID=$(gh project list --owner QHuuT --json number,title | jq -r '.[] | select(.title=="GoNoGo") | .number')
```

**Note**: GitHub Projects integration requires `project` scope in authentication.

## 🔧 Issue Creation Commands

### **For Epics (EP-XXXXX)**
```bash
# Step 1: Create the epic issue
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

## Dependencies
- **Blocks**: [List of issues this epic blocks]
- **Blocked by**: [List of issues blocking this epic]

## Story Points Estimate
[Total points]

**Priority**: High - [rationale]
**Release**: [v1.0/v1.1/etc]
**Related Issues**: [List dependent/related issues]" \
  --label "epic,priority/high,epic/[category],status/backlog"

# Step 2: Add to GitHub Project
gh project item-add $GONOGO_PROJECT_ID --url [ISSUE-URL]

# Step 3: Set project fields (requires project item ID)
ITEM_ID=$(gh project item-list $GONOGO_PROJECT_ID --format json | jq -r '.items[] | select(.content.title | contains("EP-00006")) | .id')
gh project item-edit --id $ITEM_ID --field "Priority" --value "High"
gh project item-edit --id $ITEM_ID --field "Status" --value "Backlog"
```

### **For User Stories (US-XXXXX)**
```bash
# Step 1: Create the user story issue
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

## Dependencies
- **Blocks**: [List of issues this user story blocks]
- **Blocked by**: [List of issues blocking this user story]

## Technical Notes
[Implementation details]

## Definition of Done
- [ ] BDD scenarios written and passing
- [ ] Unit tests implemented
- [ ] Code reviewed and merged
- [ ] RTM updated

**Parent Epic**: EP-XXXXX
**Story Points**: [1-8]
**Priority**: Medium - [rationale]
**Related Issues**: [List dependent/related issues]" \
  --label "user-story,priority/medium,epic/[category],status/backlog,component/backend"

# Step 2: Add to GitHub Project
gh project item-add $GONOGO_PROJECT_ID --url [ISSUE-URL]

# Step 3: Set project fields and parent relationship
ITEM_ID=$(gh project item-list $GONOGO_PROJECT_ID --format json | jq -r '.items[] | select(.content.title | contains("US-00018")) | .id')
gh project item-edit --id $ITEM_ID --field "Priority" --value "Medium"
gh project item-edit --id $ITEM_ID --field "Epic Parent" --value "EP-XXXXX"
gh project item-edit --id $ITEM_ID --field "Status" --value "Backlog"
```

### **For Defects (DEF-XXXXX)**
```bash
# Step 1: Create the defect issue
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

## Dependencies
- **Blocks**: [List of issues this defect blocks]
- **Blocked by**: [List of issues blocking this defect fix]

## ✅ Acceptance Criteria

- [ ] [Fix criterion 1]
- [ ] [Fix criterion 2]

**Parent User Story**: US-XXXXX (if defect relates to specific user story)
**Priority**: High - [affects RTM navigation usability]
**Epic**: EP-XXXXX (if applicable)
**Related Issues**: [US-XXXXX, etc.]" \
  --label "defect,priority/high,epic/[category],component/backend"

# Step 2: Add to GitHub Project
gh project item-add $GONOGO_PROJECT_ID --url [ISSUE-URL]

# Step 3: Set project fields and parent relationship
ITEM_ID=$(gh project item-list $GONOGO_PROJECT_ID --format json | jq -r '.items[] | select(.content.title | contains("DEF-00003")) | .id')
gh project item-edit --id $ITEM_ID --field "Priority" --value "High"
gh project item-edit --id $ITEM_ID --field "Parent User Story" --value "US-XXXXX"
gh project item-edit --id $ITEM_ID --field "Status" --value "Backlog"
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

## 🔗 Dependency Management

### **Issue Linking Strategies**

**In Issue Body** (automatically creates references):
```markdown
## Dependencies
- **Blocks**: #12, #13 (This issue blocks these issues)
- **Blocked by**: #8, #9 (These issues must be completed first)
- **Related to**: #15, #16 (Related but not blocking)

## Parent Relationship
- **Epic**: EP-00005 (Parent epic for user stories)
- **User Story**: US-00014 (Parent user story for defects)
```

**GitHub Issue References**:
- Use `#12` format to auto-link issues
- Use "Blocks #12" or "Blocked by #8" for dependency tracking
- Use "Closes #12" in commit messages to auto-close

### **Hierarchical Relationships**

**Epic → User Stories → Defects**:
```bash
# Epic has child user stories
Epic Body: "## User Stories\n- US-00018: #18\n- US-00019: #19"

# User Story references parent epic
US Body: "**Parent Epic**: EP-00005 (#7)"

# Defect references parent user story
DEF Body: "**Parent User Story**: US-00014 (#8)"
```

## 📚 Quick Reference Commands

```bash
# Setup GitHub Project Integration
export GONOGO_PROJECT_ID=$(gh project list --owner QHuuT --json number,title | jq -r '.[] | select(.title=="GoNoGo") | .number')

# Check next available IDs
gh issue list --limit 50 --state all | grep -E "(EP-|US-|DEF-)" | tail -10

# Check available labels
gh label list | grep -E "(priority|epic|component|status)"

# Create epic with project integration
ISSUE_URL=$(gh issue create --title "EP-XXXXX: Title" --body "Content" --label "epic,priority/high")
gh project item-add $GONOGO_PROJECT_ID --url $ISSUE_URL

# Create user story with parent relationship
ISSUE_URL=$(gh issue create --title "US-XXXXX: Title" --body "**Parent Epic**: EP-XXXXX" --label "user-story,priority/medium")
gh project item-add $GONOGO_PROJECT_ID --url $ISSUE_URL

# Create defect with parent relationship
ISSUE_URL=$(gh issue create --title "DEF-XXXXX: Title" --body "**Parent User Story**: US-XXXXX" --label "defect,priority/high")
gh project item-add $GONOGO_PROJECT_ID --url $ISSUE_URL

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