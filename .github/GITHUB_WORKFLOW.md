# GitHub Workflow Integration

**This is the PRIMARY project management system for GoNoGo.**

## 🎯 Philosophy: GitHub-First Project Management

### Why GitHub Issues (Not Separate Documentation)
- **Single Source of Truth**: GitHub Issues are the authoritative source for all project work
- **Live Status**: Real-time updates on what's being worked on
- **Integrated**: Same platform as code, PRs, and discussions
- **Collaborative**: Built-in assignment, commenting, and tracking

### Documentation Strategy
```
GitHub Issues (Primary)    →    Generated Documentation (Secondary)
├── Epics                 →    ├── Auto-generated RTM
├── User Stories          →    ├── Epic summaries
├── Defects               →    ├── Status reports
└── Live status           →    └── Archive/history
```

## 🏗️ Architecture Overview

### .github/ Directory Purpose
This directory contains **ALL project management infrastructure**:

```
.github/
├── ISSUE_TEMPLATE/           # 🎯 PRIMARY: Issue creation forms
│   ├── epic.yml             # Epic creation template
│   ├── user-story.yml       # User story template
│   ├── defect-report.yml    # Bug/defect reporting
│   └── config.yml           # Template configuration
├── workflows/               # 🤖 AUTOMATION: GitHub Actions
│   └── auto-label-issues.yml # Automatic issue label assignment
├── labels.yml              # 🏷️ Label definitions for organization
├── GITHUB_WORKFLOW.md      # 📚 This guide
└── *.md                    # 📋 Project management documentation
```

### vs docs/ Directory Purpose
The `docs/` directory serves a **different purpose**:
- **Manual documentation**: Architecture decisions, development guides
- **Generated content**: Auto-created from GitHub Issues (future)
- **Permanent records**: Technical specifications, compliance docs
- **Developer guides**: CLAUDE.md, setup instructions

## 🎯 The GitHub Workflow Integration provides:
- Standardized issue templates for epics, user stories, and defects
- **Automatic label assignment** based on template responses and traceability matrix
- Intelligent component mapping from epic associations
- GDPR compliance detection and labeling
- Release planning automation (MVP/v1.1/v1.2)
- Status management with smart initial assignment
- Traceability between issues and documentation
- Integration with Requirements Traceability Matrix (RTM)

## 📋 Issue Templates

### Epic Template
**When to use**: Creating a new epic (collection of related user stories)
**Template**: Epic template includes business value, success criteria, and user story planning
**Auto-assigned labels**:
- `epic` (issue type)
- `priority/*` (based on priority selection)
- `epic/*` and `component/*` (based on epic ID and traceability matrix)
- `release/*` (based on priority and business rules)
- `gdpr/*` (if GDPR considerations selected)
- `status/backlog` (initial status)

### User Story Template
**When to use**: Creating a specific user story within an epic
**Template**: Includes acceptance criteria, GDPR considerations, and traceability links
**Auto-assigned labels**:
- `user-story` (issue type)
- `priority/*` (based on priority selection)
- `epic/*` and `component/*` (inherited from parent epic via traceability matrix)
- `release/*` (based on priority and parent epic business rules)
- `gdpr/*` (if GDPR considerations selected)
- `status/backlog` or `status/ready` (based on content indicators)

### Defect Report Template
**When to use**: Reporting a bug or issue in existing functionality
**Template**: Includes reproduction steps, impact assessment, and affected requirements
**Auto-assigned labels**:
- `defect` (issue type)
- `priority/*` (based on priority/severity selection)
- `component/*` (based on affected components or linked epic)
- `release/*` (based on priority and affected epic)
- `status/backlog` (initial status)

## 🏷️ Label System

### Issue Types
- `epic` - Epic issues
- `user-story` - User story issues
- `defect` / `bug` - Defect reports

### Priority Levels
- `priority/critical` - Blocks other work
- `priority/high` - Important for current iteration
- `priority/medium` - Normal importance
- `priority/low` - Nice to have

### Epic Categories
- `epic/blog-content` - EP-001: Blog Content Management
- `epic/comment-system` - EP-002: GDPR-Compliant Comment System
- `epic/privacy-consent` - EP-003: Privacy and Consent Management
- `epic/github-workflow` - EP-004: GitHub Workflow Integration

### Status Tracking
- `status/backlog` - Not yet started
- `status/ready` - Ready for development
- `status/in-progress` - Currently being worked on
- `status/in-review` - In code review
- `status/testing` - In testing phase
- `status/done` - Completed and verified
- `status/blocked` - Blocked by dependency

### Components
- `component/frontend` - UI/Frontend work
- `component/backend` - Backend/API work
- `component/database` - Database changes
- `component/security` - Security-related
- `component/gdpr` - GDPR compliance
- `component/documentation` - Documentation
- `component/testing` - Testing work
- `component/ci-cd` - CI/CD pipeline

### GDPR-Specific Labels
- `gdpr/personal-data` - Involves personal data processing
- `gdpr/consent-required` - Requires user consent
- `gdpr/privacy-review` - Needs privacy impact assessment
- `gdpr/data-retention` - Related to data retention policies

### Release Planning Labels
- `release/mvp` - Part of MVP release
- `release/v1.1` - Part of v1.1 release
- `release/v1.2` - Part of v1.2 release

## 🤖 Automatic Label Assignment System

### How It Works
When you create or edit an issue using the templates, the system automatically assigns relevant labels based on:

1. **Form Responses**: Priority, epic ID, GDPR checkboxes
2. **Traceability Matrix**: Epic-to-component mappings from `docs/traceability/requirements-matrix.md`
3. **Content Analysis**: Keywords in issue body for status and GDPR detection
4. **Business Rules**: Release planning logic based on priority and epic classification

### Label Assignment Rules

#### Priority Mapping
- Priority "Critical" → `priority/critical`
- Priority "High" → `priority/high`
- Priority "Medium" → `priority/medium`
- Priority "Low" → `priority/low`

#### Epic-to-Component Mapping
Based on the Requirements Traceability Matrix:
- EP-001 (Blog Content) → `component/frontend` + `epic/blog-content`
- EP-002 (Comment System) → `component/backend` + `epic/comment-system`
- EP-003 (Privacy/GDPR) → `component/gdpr` + `epic/privacy-consent`
- EP-004 (GitHub Workflow) → `component/ci-cd` + `epic/github-workflow`

#### GDPR Detection
Automatically assigns GDPR labels when issue contains:
- "personal data processing" → `gdpr/personal-data`
- "requires user consent" → `gdpr/consent-required`
- "privacy impact assessment" → `gdpr/privacy-review`
- "data retention" → `gdpr/data-retention`

#### Release Planning Logic
- **Critical priority** OR **EP-002/EP-003** → `release/mvp`
- **High priority** → `release/v1.1`
- **Medium/Low priority** → `release/v1.2`

#### Status Assignment
- Default: `status/backlog`
- Contains "ready for development" → `status/ready`
- Contains "in progress" → `status/in-progress`
- Contains "blocked by" → `status/blocked`

### Automation Trigger
The labeling system runs automatically:
- **When**: Issues are opened or edited
- **Processing Time**: Within 30 seconds
- **Error Handling**: Graceful fallbacks if traceability matrix unavailable
- **Logging**: All label assignments logged for transparency

## 🔄 Workflow Process

### 1. Creating an Epic
1. Click "New Issue" in GitHub
2. Select "Epic" template
3. Fill in all required fields:
   - Epic ID (EP-XXX)
   - Business value and success criteria
   - User stories planning
   - Risk assessment
4. Submit issue
5. Epic will be automatically added to project board

### 2. Creating a User Story
1. Click "New Issue" in GitHub
2. Select "User Story" template
3. Fill in all required fields:
   - User story ID (US-XXX)
   - Link to parent epic
   - Acceptance criteria (functional and non-functional)
   - GDPR considerations if applicable
4. Submit issue
5. Story will be linked to epic and added to project board

### 3. Reporting a Defect
1. Click "New Issue" in GitHub
2. Select "Defect Report" template
3. Fill in all required fields:
   - Defect ID (DEF-XXX)
   - Reproduction steps
   - Expected vs actual behavior
   - Business impact assessment
   - Link to affected epic/user story
4. Submit issue
5. Defect will be triaged and prioritized

## 🎯 Project Management

### Project Board
- **Backlog**: New issues, needs triage
- **Ready**: Refined and ready for development
- **In Progress**: Currently being worked on
- **Review**: In code review
- **Testing**: In testing phase
- **Done**: Completed and verified

### Issue Lifecycle
1. **Created** → Automatically added to "Backlog" column
2. **Triaged** → Priority and labels assigned
3. **Refined** → Details clarified, moved to "Ready"
4. **Started** → Assigned to developer, moved to "In Progress"
5. **Code Review** → PR created, moved to "Review"
6. **Testing** → Tests passing, moved to "Testing"
7. **Done** → Verified complete, moved to "Done"

## 🔗 Traceability Integration

### Automatic RTM Updates
- Issue creation triggers RTM update (when US-010 is implemented)
- Status changes automatically reflected in documentation
- Links between epics, stories, and defects maintained
- Label assignments driven by current RTM epic mappings

### Documentation Links
- Issues link back to repository documentation
- BDD scenarios reference GitHub issues
- Code commits reference issue numbers

## 📊 Metrics and Reporting

### Available Metrics
- Epic progress tracking
- User story completion rates
- Defect resolution time
- Sprint velocity
- Component-wise workload

### Project Insights
- Use GitHub Insights for velocity tracking
- Project board provides visual progress
- Label filtering for focused views

## 🛠️ Setup Instructions

### Repository Setup
1. Ensure GitHub Issues are enabled
2. Create GitHub Project for the repository
3. Import labels from `.github/labels.yml`
4. Configure project automation rules

### Label Configuration
```bash
# Using github-label-sync (optional)
npm install -g github-label-sync
github-label-sync --access-token YOUR_TOKEN YourUsername/gonogo
```

### Project Automation Rules
- New `epic` issues → Add to project, automatically assign labels, set status "Backlog"
- New `user-story` issues → Add to project, automatically assign labels, set status "Backlog"
- New `defect` issues → Add to project, automatically assign labels, set status "Backlog"
- Issue assigned → Move to "In Progress"
- PR linked → Move to "Review"
- PR merged → Move to "Testing"
- Issue closed → Move to "Done"

### Automatic Label Assignment (Active)
- **GitHub Action**: `.github/workflows/auto-label-issues.yml`
- **Python Implementation**: `src/shared/utils/github_label_mapper.py`
- **Triggers**: Issue opened/edited events
- **Logic**: Based on form responses, traceability matrix, and business rules

## 🔧 Troubleshooting

### Common Issues
- **Templates not appearing**: Check `.github/ISSUE_TEMPLATE/` directory structure
- **Labels not automatically applied**:
  - Check GitHub Actions tab for workflow execution
  - Verify labels exist in repository (import from `labels.yml`)
  - Check workflow logs in Actions tab
- **Wrong component labels**: Update epic mappings in `docs/traceability/requirements-matrix.md`
- **Project not updated**: Check project automation rules
- **GDPR labels not assigned**: Ensure GDPR checkboxes are selected in templates

### Support
- Check [project documentation](../docs/README.md)
- Review [BDD + RTM workflow](../CLAUDE.md#bdd--rtm-development-workflow)
- Create issue with `question` label for help

---

**Completed Features**:
- ✅ **US-009**: GitHub Issue Template Integration with automatic labeling
- ✅ **Automatic Label Assignment**: Production-ready GitHub Action
- ✅ **Traceability Matrix Integration**: Epic-to-component mapping

**Next Steps**:
- **US-010**: Automated RTM updates from GitHub Issues
- **US-011**: GitHub Pages documentation site
- **Enhanced automation**: Status transitions and project board management