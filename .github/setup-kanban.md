# GitHub CLI Commands for Kanban Setup

## Step 1: Authentication
```bash
gh auth login
# Choose: GitHub.com
# Choose: HTTPS
# Choose: Yes (authenticate Git)
# Choose: Login with a web browser
# Follow the web authentication flow
```

## Step 2: Create Project
```bash
# Create a new project board
gh project create --title "GoNoGo Development Board" --body "Kanban board for managing GoNoGo development workflow"
```

## Step 3: Get Project Details
```bash
# List projects to get the project number
gh project list --owner QHuuT
```

## Step 4: Configure Fields (Manual via Web)
After creating the project, you'll need to manually add these custom fields via the web interface:

1. **Priority**: Single select
   - Critical (🔴)
   - High (🟠)
   - Medium (🟡)
   - Low (🟢)

2. **Story Points**: Number field

3. **Epic**: Single select
   - EP-00001: Blog Content Management
   - EP-00002: GDPR-Compliant Comment System
   - EP-00003: Privacy and Consent Management
   - EP-00004: GitHub Workflow Integration

4. **Component**: Single select
   - Frontend, Backend, Database, Security, GDPR, Documentation, Testing, CI/CD

## Step 5: Add Issues to Project
```bash
# Add existing issues to the project (replace PROJECT_NUMBER with actual number)
gh project item-add PROJECT_NUMBER --owner QHuuT --url https://github.com/QHuuT/gonogo/issues/1

# For future issues, they'll be automatically added due to the project reference in templates
```

## Step 6: Test with US-00009
```bash
# Create the US-00009 issue using the template
gh issue create --title "US-00009: GitHub Issue Template Integration" --body-file us-00009-content.md --label "user-story,needs-triage"
```

## Alternative: Project CLI Commands (if supported)
```bash
# These might work depending on GitHub CLI version:
gh project field-create PROJECT_NUMBER --name "Priority" --type "single_select" --options "Critical,High,Medium,Low"
gh project field-create PROJECT_NUMBER --name "Story Points" --type "number"
gh project field-create PROJECT_NUMBER --name "Epic" --type "single_select" --options "EP-00001,EP-00002,EP-00003,EP-00004"
```

## Step 7: Configure Automation (Web Interface)
Go to your project → Settings → Workflows and add:

1. **When issues are opened** → Set status to "📋 Backlog"
2. **When "ready-for-dev" label added** → Set status to "🔄 Ready"
3. **When "status/in-progress" label added** → Set status to "⏳ In Progress"
4. **When "status/in-review" label added** → Set status to "👀 In Review"
5. **When "status/testing" label added** → Set status to "🧪 Testing"
6. **When issues are closed** → Set status to "✅ Done"
7. **When "status/blocked" label added** → Set status to "🚫 Blocked"

## Verification Commands
```bash
# Check project exists
gh project list --owner QHuuT

# List project items
gh project item-list PROJECT_NUMBER --owner QHuuT

# Check repository issues
gh issue list --repo QHuuT/gonogo
```