# GitHub Issue Creation Guide

**Last Updated**: 2025-09-22
**Purpose**: Standardized process for creating GitHub issues following enhanced GitHub-first workflow protocol

## 🎯 Overview

This guide provides step-by-step instructions for creating GitHub issues using the CLI, avoiding common errors, and ensuring proper ID sequencing following the CLAUDE.md protocol.

## 🔧 Component-Focused Issue Creation Guidelines

**NEW: Enhanced Component Boundary Guidelines** (Updated 2025-09-22 - Based on US-00014 lessons learned)

### **Epic Creation Strategy**

**Epics SHOULD span multiple components** when the feature naturally requires cross-team collaboration:

- **Multi-Component Epics**: Epics represent high-level features that benefit from broad system integration
- **Component Inheritance**: Epic components are automatically populated from child User Stories
- **Comprehensive Scope**: Epic component field lists ALL components involved in the epic
- **Cross-Team Coordination**: Epics facilitate coordination between Frontend, Backend, Database, Security teams

**Epic Component Examples:**
```markdown
EP-00007: User Authentication System
Components: Frontend/UI, Backend/API, Database, Security/GDPR

EP-00008: Advanced Search Feature
Components: Frontend/UI, Backend/API, Database, Testing
```

### **User Story Creation Strategy**

**User Stories SHOULD be component-focused** for optimal development workflow:

**✅ Component-Focused Approach:**
- **Single Primary Component**: Each user story targets one main system component
- **Clear Team Ownership**: Easy assignment to specific development teams
- **Parallel Development**: Multiple teams can work simultaneously
- **Focused Scope**: Reduced complexity and clearer deliverables

**❌ Multi-Component Anti-Pattern:**
```markdown
US-XXX: Implement complete user login system
- Requires: Frontend forms + Backend API + Database schema + Security validation
- Problems: Unclear ownership, coordination overhead, complex estimation
```

**✅ Component-Focused Pattern:**
```markdown
US-XXX: Design user login UI components (Frontend/UI)
- Clear ownership: Frontend team
- Focused deliverable: Login form, validation UI, error handling

US-XXX: Implement login API endpoints (Backend/API)
- Clear ownership: Backend team
- Focused deliverable: Authentication endpoints, session management

US-XXX: Create user authentication database schema (Database)
- Clear ownership: Database team
- Focused deliverable: User table, indexes, migration scripts
```

### **Cross-Story Coordination Guidelines**

When splitting multi-component features into focused user stories:

**1. Reference Related Stories:**
```markdown
## Dependencies
- **Related Stories**: US-XXX (Frontend), US-XXX (Database)
- **Coordination Points**: API contract definition, data model agreement
```

**2. Link to Parent Epic:**
```markdown
**Parent Epic**: EP-00007: User Authentication System
```

**3. Define Integration Points:**
```markdown
## Integration Requirements
- API contract: /api/auth/login endpoint specification
- Data validation: Username/password format requirements
- Error handling: Consistent error response format
```

### **Benefits of Component-Focused User Stories**

**Development Benefits:**
- **Clear Ownership**: Unambiguous team assignment and accountability
- **Better Estimation**: More accurate story points for single-component work
- **Parallel Development**: Teams work simultaneously without blocking each other
- **Focused Testing**: Component-specific test strategies and coverage

**Project Management Benefits:**
- **Progress Tracking**: Component-specific progress visible in RTM dashboard
- **Resource Planning**: Better team capacity and workload distribution
- **Risk Management**: Isolated component risks don't block entire feature
- **Quality Gates**: Component-specific quality standards and reviews

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

### **For Epics (EP-XXXXX) - Multi-Component Approach**

**Example: Epic spanning multiple components with component inheritance**

```bash
# Step 1: Create the epic issue
gh issue create \
  --title "EP-00007: User Authentication System" \
  --body "## Epic Description

**As a** blog owner and user
**I want** a comprehensive authentication system
**So that** users can securely access personalized features and I can manage user access

Complete user authentication system with secure login, session management, and GDPR-compliant user data handling.

## Multi-Component Architecture

This epic intentionally spans multiple components for integrated feature delivery:

**Components Involved:**
- **Frontend/UI**: Login forms, user interface, client-side validation
- **Backend/API**: Authentication endpoints, session management, security middleware
- **Database**: User schema, session storage, audit logging
- **Security/GDPR**: Password security, session protection, privacy compliance

## Component-Focused User Stories

**Frontend Team:**
- US-00018: Design user login UI components
- US-00021: Implement user registration forms
- US-00024: Create password reset interface

**Backend Team:**
- US-00019: Implement login API endpoints
- US-00022: Build user registration API
- US-00025: Develop password reset endpoints

**Database Team:**
- US-00020: Create user authentication database schema
- US-00023: Implement session storage system
- US-00026: Design audit logging tables

**Security Team:**
- US-00027: Implement password security policies
- US-00028: Add GDPR compliance for user data
- US-00029: Security testing and penetration testing

## Cross-Team Coordination

**Integration Points:**
- API contracts between Frontend and Backend teams
- Database schemas shared between Backend and Database teams
- Security requirements applied across all components
- GDPR compliance verification for all user data flows

**Dependencies:**
- Database schema (US-00020) must be completed before Backend API (US-00019)
- API endpoints (US-00019) must be defined before Frontend integration (US-00018)
- Security policies (US-00027) inform all component implementations

## Epic Acceptance Criteria
- [ ] Users can register with email and password
- [ ] Users can log in and out securely
- [ ] Sessions are managed properly with expiration
- [ ] Password reset functionality works end-to-end
- [ ] All GDPR requirements are met
- [ ] Security testing passes all requirements
- [ ] Performance meets requirements (< 2s login time)

## Story Points Estimate
**Total**: 45 points (distributed across teams)
- Frontend: 12 points (3 + 4 + 5)
- Backend: 15 points (5 + 5 + 5)
- Database: 9 points (3 + 3 + 3)
- Security: 9 points (3 + 3 + 3)

**Priority**: High - Core platform functionality
**Release**: v1.0 - Essential for user features
**Epic Lead**: [Backend Team Lead] (coordination role)" \
  --label "epic,priority/high,epic/authentication,status/backlog"

# Step 2: Add to GitHub Project
gh project item-add $GONOGO_PROJECT_ID --url [ISSUE-URL]

# Step 3: Set project fields (requires project item ID)
ITEM_ID=$(gh project item-list $GONOGO_PROJECT_ID --format json | jq -r '.items[] | select(.content.title | contains("EP-00006")) | .id')
gh project item-edit --id $ITEM_ID --field "Priority" --value "High"
gh project item-edit --id $ITEM_ID --field "Status" --value "Backlog"
```

### **For User Stories (US-XXXXX) - Component-Focused Approach**

**Example: Component-focused user stories from split feature**

```bash
# Frontend-focused user story
gh issue create \
  --title "US-00018: Design user login UI components" \
  --body "## User Story

As a blog visitor, I want an intuitive login interface so that I can easily access my account.

## Component Focus
**Primary Component**: Frontend/UI
**Team Assignment**: Frontend Team

## Acceptance Criteria
- [ ] Login form with username/email and password fields
- [ ] Client-side validation with user-friendly error messages
- [ ] Responsive design for mobile and desktop
- [ ] Loading states during authentication
- [ ] "Remember me" and "Forgot password" links

## BDD Scenarios
- login-ui.feature:display_login_form
- login-ui.feature:validate_form_inputs
- login-ui.feature:show_loading_states

## Integration Requirements
- **API Contract**: POST /api/auth/login endpoint
- **Data Format**: JSON request with username/password
- **Error Handling**: Display backend error messages appropriately

## Dependencies
- **Related Stories**: US-00019 (Backend API), US-00020 (Database schema)
- **Coordination Points**: API contract definition, error message format

## Technical Notes
- Use existing form component library
- Implement client-side validation patterns
- Follow accessibility guidelines (WCAG 2.1)

## Definition of Done
- [ ] UI components implemented and styled
- [ ] Client-side validation working
- [ ] BDD scenarios passing
- [ ] Responsive design tested
- [ ] Accessibility compliance verified

**Parent Epic**: EP-00007: User Authentication System
**Story Points**: 3
**Priority**: High - Core authentication functionality
**Related Issues**: US-00019 (Backend), US-00020 (Database)" \
  --label "user-story,priority/high,epic/authentication,status/backlog,component/frontend"

# Backend-focused user story
gh issue create \
  --title "US-00019: Implement login API endpoints" \
  --body "## User Story

As a system, I want secure authentication endpoints so that users can log in safely.

## Component Focus
**Primary Component**: Backend/API
**Team Assignment**: Backend Team

## Acceptance Criteria
- [ ] POST /api/auth/login endpoint accepting username/password
- [ ] Secure password validation with bcrypt
- [ ] JWT token generation for authenticated sessions
- [ ] Rate limiting to prevent brute force attacks
- [ ] Comprehensive error responses

## BDD Scenarios
- auth-api.feature:successful_login
- auth-api.feature:invalid_credentials
- auth-api.feature:rate_limiting

## Integration Requirements
- **Database Contract**: User model with hashed passwords
- **Frontend Contract**: JSON response with token or error
- **Security Requirements**: GDPR-compliant session handling

## Dependencies
- **Related Stories**: US-00018 (Frontend UI), US-00020 (Database schema)
- **Blocked by**: US-00020 (Database schema must exist)

## Technical Notes
- Use FastAPI for endpoint implementation
- Implement proper password hashing
- Add comprehensive logging for security monitoring
- Follow OWASP authentication guidelines

## Definition of Done
- [ ] API endpoints implemented and tested
- [ ] Security measures in place
- [ ] Integration tests passing
- [ ] API documentation updated
- [ ] Performance testing completed

**Parent Epic**: EP-00007: User Authentication System
**Story Points**: 5
**Priority**: High - Core authentication functionality
**Related Issues**: US-00018 (Frontend), US-00020 (Database)" \
  --label "user-story,priority/high,epic/authentication,status/backlog,component/backend"

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

### **Component-Focused Issue Creation Workflow**

```bash
# Setup GitHub Project Integration
export GONOGO_PROJECT_ID=$(gh project list --owner QHuuT --json number,title | jq -r '.[] | select(.title=="GoNoGo") | .number')

# Check next available IDs
gh issue list --limit 50 --state all | grep -E "(EP-|US-|DEF-)" | tail -10

# Check available labels and components
gh label list | grep -E "(priority|epic|component|status)"

# 1. Create multi-component epic (spans teams)
ISSUE_URL=$(gh issue create \
  --title "EP-XXXXX: Authentication System" \
  --body "Multi-component epic involving Frontend, Backend, Database, Security teams" \
  --label "epic,priority/high,epic/authentication")
gh project item-add $GONOGO_PROJECT_ID --url $ISSUE_URL

# 2. Create component-focused user stories (team-specific)
# Frontend story
ISSUE_URL=$(gh issue create \
  --title "US-XXXXX: Design login UI components" \
  --body "**Parent Epic**: EP-XXXXX\n**Component**: Frontend/UI\n**Team**: Frontend" \
  --label "user-story,priority/high,component/frontend")
gh project item-add $GONOGO_PROJECT_ID --url $ISSUE_URL

# Backend story
ISSUE_URL=$(gh issue create \
  --title "US-XXXXX: Implement login API" \
  --body "**Parent Epic**: EP-XXXXX\n**Component**: Backend/API\n**Team**: Backend" \
  --label "user-story,priority/high,component/backend")
gh project item-add $GONOGO_PROJECT_ID --url $ISSUE_URL

# Database story
ISSUE_URL=$(gh issue create \
  --title "US-XXXXX: Create auth database schema" \
  --body "**Parent Epic**: EP-XXXXX\n**Component**: Database\n**Team**: Database" \
  --label "user-story,priority/high,component/database")
gh project item-add $GONOGO_PROJECT_ID --url $ISSUE_URL

# 3. Create component-focused defect (inherits from user story)
ISSUE_URL=$(gh issue create \
  --title "DEF-XXXXX: Login form validation error" \
  --body "**Parent User Story**: US-XXXXX\n**Component**: Frontend/UI (inherited)" \
  --label "defect,priority/high,component/frontend")
gh project item-add $GONOGO_PROJECT_ID --url $ISSUE_URL

# 4. Update RTM after creation
# Edit docs/traceability/requirements-matrix.md manually

# 5. Validate RTM
python tools/rtm-links-simple.py --validate
```

### **Component Label Reference**

```bash
# Standard component labels for user stories
component/frontend     # UI components, templates, client-side logic
component/backend      # API endpoints, business logic, server-side
component/database     # Schema, migrations, queries, data models
component/security     # Authentication, authorization, GDPR
component/testing      # Test infrastructure, quality assurance
component/cicd         # Build pipelines, deployment automation
component/documentation # User guides, API docs, technical documentation
```

### **Issue Creation Decision Matrix**

| Issue Type | Component Scope | Team Assignment | Example |
|------------|-----------------|-----------------|---------|
| **Epic** | Multi-component | Cross-team coordination | "Authentication System" (Frontend + Backend + Database + Security) |
| **User Story** | Single component | Single team | "Design login UI" (Frontend only) |
| **Defect** | Inherits from parent | Same as parent user story | "Login button styling bug" (Frontend - inherited) |

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
- [Development Workflow](development-workflow.md) - Complete development process with component-focused guidelines
- [Documentation Workflow](documentation-workflow.md) - RTM update requirements
- [Requirements Matrix](../traceability/requirements-matrix.md) - Current RTM status

**📖 Complete Workflow Context**: This guide provides detailed issue creation commands and examples. For the complete development workflow including BDD, testing, and quality gates, see [Development Workflow](development-workflow.md).