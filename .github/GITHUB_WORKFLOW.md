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
├── workflows/               # 🤖 FUTURE: Automation
│   └── (future automation)  # Auto-generate docs from issues
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
- Automatic labeling and project assignment
- Traceability between issues and documentation
- Integration with Requirements Traceability Matrix (RTM)

## 📋 Issue Templates

### Epic Template
**When to use**: Creating a new epic (collection of related user stories)
**Template**: Epic template includes business value, success criteria, and user story planning
**Labels**: Automatically tagged with `epic`, `needs-triage`

### User Story Template
**When to use**: Creating a specific user story within an epic
**Template**: Includes acceptance criteria, GDPR considerations, and traceability links
**Labels**: Automatically tagged with `user-story`, `needs-triage`

### Defect Report Template
**When to use**: Reporting a bug or issue in existing functionality
**Template**: Includes reproduction steps, impact assessment, and affected requirements
**Labels**: Automatically tagged with `defect`, `bug`, `needs-triage`

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
- New `epic` issues → Add to project, set status "Backlog"
- New `user-story` issues → Add to project, set status "Backlog"
- New `defect` issues → Add to project, set status "Backlog"
- Issue assigned → Move to "In Progress"
- PR linked → Move to "Review"
- PR merged → Move to "Testing"
- Issue closed → Move to "Done"

## 🔧 Troubleshooting

### Common Issues
- **Templates not appearing**: Check `.github/ISSUE_TEMPLATE/` directory structure
- **Labels not applied**: Verify label names match template configuration
- **Project not updated**: Check project automation rules

### Support
- Check [project documentation](../docs/README.md)
- Review [BDD + RTM workflow](../CLAUDE.md#bdd--rtm-development-workflow)
- Create issue with `question` label for help

---

**Next Steps**: After setting up templates, implement US-010 for automated RTM updates and US-011 for GitHub Pages documentation site.