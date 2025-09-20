# GitHub Project Automation Configuration

## Recommended Automation Rules

### **Issue Status Automation**

1. **When issue is created** → Move to "📋 Backlog"
2. **When label "ready-for-dev" is added** → Move to "🔄 Ready"
3. **When label "status/in-progress" is added** → Move to "⏳ In Progress"
4. **When label "status/in-review" is added** → Move to "👀 In Review"
5. **When label "status/testing" is added** → Move to "🧪 Testing"
6. **When issue is closed** → Move to "✅ Done"
7. **When label "status/blocked" is added** → Move to "🚫 Blocked"

### **Pull Request Automation**

1. **When PR is created** → Move to "👀 In Review"
2. **When PR is merged** → Move to "✅ Done"
3. **When PR is closed without merge** → Move to "🚫 Blocked"

### **Epic/User Story Workflow**

1. **Epic created** → Auto-assign "epic" label and move to "📋 Backlog"
2. **User Story created** → Auto-assign "user-story" label and move to "📋 Backlog"
3. **Defect created** → Auto-assign "defect" label and move to "📋 Backlog"

## Custom Field Configuration

### **Priority Field**
- Critical (🔴)
- High (🟠)
- Medium (🟡)
- Low (🟢)

### **Story Points Field**
- 1, 2, 3, 5, 8, 13, 21 (Fibonacci sequence)

### **Epic Field**
- EP-00001: Blog Content Management
- EP-00002: GDPR-Compliant Comment System
- EP-00003: Privacy and Consent Management
- EP-00004: GitHub Workflow Integration

### **Component Field**
- Frontend
- Backend
- Database
- Security
- GDPR
- Documentation
- Testing
- CI/CD

## Views Configuration

### **Board View (Default)**
- Group by: Status
- Filter: All issues and PRs
- Sort: Priority (High to Low)

### **Epic Planning View**
- Group by: Epic
- Filter: Type = Epic or User Story
- Sort: Priority

### **Sprint View**
- Group by: Status
- Filter: Labels contains "ready-for-dev" OR "status/in-progress"
- Sort: Priority

### **GDPR Compliance View**
- Group by: Status
- Filter: Labels contains "gdpr" OR "component/gdpr"
- Sort: Priority

## Integration with Labels

Map project columns to your existing labels from `.github/labels.yml`:

```yaml
Kanban → Label Mapping:
📋 Backlog → status/backlog
🔄 Ready → status/ready, ready-for-dev
⏳ In Progress → status/in-progress
👀 In Review → status/in-review, ready-for-review
🧪 Testing → status/testing, ready-for-testing
✅ Done → status/done
🚫 Blocked → status/blocked
```

## Workflow Integration

### **Issue Template Integration**
Your issue templates already reference the project:
```yaml
projects: ["gonogo/1"]
```

This will automatically add new issues to the project board.

### **RTM Integration**
The kanban board will provide visual representation of:
- Epic progress (collection of user stories)
- User story status (individual features)
- Defect tracking (bugs and issues)
- Overall project health

## Setup Checklist

- [ ] Create GitHub Project "GoNoGo Development Board"
- [ ] Configure 7 kanban columns
- [ ] Set up automation rules for labels
- [ ] Add custom fields (Priority, Story Points, Epic, Component)
- [ ] Create different views (Board, Epic Planning, Sprint, GDPR)
- [ ] Test automation with a sample issue
- [ ] Update issue templates if needed
- [ ] Document workflow for team members

## Benefits

1. **Visual Project Management**: See all work in progress at a glance
2. **Automated Workflow**: Issues move automatically based on labels
3. **Epic Tracking**: Group user stories under epics
4. **GDPR Compliance**: Dedicated view for privacy-related work
5. **Sprint Planning**: Dedicated view for current iteration
6. **Metrics**: Track velocity and completion rates