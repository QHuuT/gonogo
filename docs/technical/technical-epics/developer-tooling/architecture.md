# Developer Tooling Architecture

**Last Updated**: 2025-09-20

## 🏗️ Architecture Decisions

### ADR-001: GitHub-First Project Management

**Status**: Approved
**Date**: 2025-09-20

#### Context
Need unified project management approach that reduces tool complexity and improves collaboration.

#### Decision
Use GitHub Issues, Projects, and Actions as the primary project management infrastructure.

#### Rationale
- **Consolidation**: Single platform for code, issues, and documentation
- **Native Integration**: Built-in GitHub features reduce external dependencies
- **Collaboration**: GitHub's social features enhance team collaboration
- **Automation**: GitHub Actions provide powerful automation capabilities

#### Consequences
- Enhanced team collaboration within single platform
- Reduced tool switching and context switching overhead
- Increased dependency on GitHub platform availability
- Potential vendor lock-in (mitigated by data export capabilities)

### ADR-002: Automated Documentation Publishing

**Status**: Approved
**Date**: 2025-09-20

#### Context
Need automatic documentation publishing that maintains freshness and accessibility.

#### Decision
Use GitHub Pages with automated builds from repository content.

#### Rationale
- **Automation**: Automatic publishing on repository changes
- **Integration**: Native GitHub integration with repository
- **Accessibility**: Public documentation without additional hosting
- **Versioning**: Git-based versioning for documentation

#### Consequences
- Always up-to-date public documentation
- Reduced manual documentation maintenance
- GitHub Pages limitations on dynamic content
- Public visibility requires careful content curation

### ADR-003: Bi-directional Issue-Documentation Sync

**Status**: Approved
**Date**: 2025-09-20

#### Context
Need synchronization between detailed repository documentation and GitHub Issues status.

#### Decision
Implement GitHub Actions for automated sync with GitHub Issues as source of truth for status.

#### Rationale
- **Single Source of Truth**: GitHub Issues for status and workflow state
- **Detail Preservation**: Repository for detailed technical documentation
- **Automation**: Reduce manual synchronization overhead
- **Traceability**: Maintain requirements traceability automatically

#### Consequences
- Accurate real-time status tracking
- Complex synchronization logic requirements
- Potential sync conflicts requiring resolution strategies
- Enhanced traceability matrix accuracy

## 🏛️ GitHub Integration Architecture

### Overall System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Platform                          │
│                                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ GitHub Issues   │ │ GitHub Actions  │ │ GitHub Pages    │ │
│ │                 │ │                 │ │                 │ │
│ │ - Epics         │ │ - RTM Sync      │ │ - Documentation │ │
│ │ - User Stories  │ │ - Status Update │ │ - Public Site   │ │
│ │ - Defects       │ │ - Page Build    │ │ - Traceability  │ │
│ │ - Templates     │ │ - Validation    │ │ - Search        │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│           │                   │                   │         │
│           └───────────────────┼───────────────────┘         │
│                               │                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              Repository Content                         │ │
│ │                                                         │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │ │
│ │ │ Technical   │ │ Templates   │ │ Automation Scripts  │ │ │
│ │ │ Documentation│ │ & Workflows │ │ & Configurations    │ │ │
│ │ └─────────────┘ └─────────────┘ └─────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Issue Management Architecture
```
GitHub Issue Templates
├── Epic Template (.github/ISSUE_TEMPLATE/epic.yml)
├── User Story Template (.github/ISSUE_TEMPLATE/user-story.yml)
└── Defect Report Template (.github/ISSUE_TEMPLATE/defect-report.yml)
         │
         ├── Auto-Labels Assignment
         ├── Milestone Association
         └── Project Board Integration
                  │
                  ├── GitHub Projects Board
                  ├── Automated Status Updates
                  └── Cross-Reference Generation
```

## 🔄 Automation Architecture

### GitHub Actions Workflow Design

#### RTM Synchronization Workflow
```yaml
name: Sync Requirements Traceability Matrix
on:
  issues:
    types: [opened, edited, closed, labeled]
  pull_request:
    types: [opened, closed, merged]

jobs:
  sync-rtm:
    runs-on: ubuntu-latest
    steps:
      - name: Extract Issue Data
        uses: ./.github/actions/extract-issue-data

      - name: Update RTM
        uses: ./.github/actions/update-rtm
        with:
          issue-data: ${{ steps.extract.outputs.data }}

      - name: Generate Documentation
        uses: ./.github/actions/generate-docs

      - name: Deploy to Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./generated-docs
```

#### Documentation Publishing Workflow
```yaml
name: Deploy Documentation
on:
  push:
    branches: [main]
    paths: ['docs/**', '.github/workflows/**']

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Build Documentation Site
        uses: ./.github/actions/build-docs

      - name: Generate RTM
        uses: ./.github/actions/generate-rtm

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs-build
```

### Custom GitHub Actions

#### Extract Issue Data Action
```javascript
// .github/actions/extract-issue-data/index.js
const core = require('@actions/core');
const github = require('@actions/github');

async function extractIssueData() {
    const context = github.context;
    const issue = context.payload.issue;

    // Parse issue template data
    const issueData = {
        id: issue.number,
        title: issue.title,
        body: issue.body,
        labels: issue.labels.map(label => label.name),
        milestone: issue.milestone?.title,
        state: issue.state,
        created_at: issue.created_at,
        updated_at: issue.updated_at
    };

    // Extract structured data from issue body
    const structuredData = parseIssueTemplate(issue.body);

    // Determine issue type from labels
    const issueType = determineIssueType(issue.labels);

    const output = {
        ...issueData,
        type: issueType,
        structured: structuredData,
        epic_id: extractEpicId(structuredData),
        user_story_id: extractUserStoryId(structuredData)
    };

    core.setOutput('data', JSON.stringify(output));
}

function parseIssueTemplate(body) {
    // Parse GitHub issue template format
    const sections = {};
    const lines = body.split('\n');

    let currentSection = null;
    let currentContent = [];

    for (const line of lines) {
        if (line.startsWith('### ')) {
            if (currentSection) {
                sections[currentSection] = currentContent.join('\n').trim();
            }
            currentSection = line.substring(4).trim();
            currentContent = [];
        } else {
            currentContent.push(line);
        }
    }

    if (currentSection) {
        sections[currentSection] = currentContent.join('\n').trim();
    }

    return sections;
}

extractIssueData().catch(error => {
    core.setFailed(error.message);
});
```

## 📊 Traceability Matrix Architecture

### RTM Generation System
```python
# .github/scripts/generate_rtm.py
import json
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass
from github import Github

@dataclass
class TraceabilityItem:
    id: str
    title: str
    type: str
    status: str
    epic_id: Optional[str]
    user_story_id: Optional[str]
    github_issue_url: str
    last_updated: str

class RTMGenerator:
    def __init__(self, github_token: str, repo_name: str):
        self.github = Github(github_token)
        self.repo = self.github.get_repo(repo_name)

    async def generate_rtm(self) -> Dict:
        """Generate comprehensive requirements traceability matrix"""

        # Fetch all issues with epic/story/defect labels
        epics = await self._fetch_issues_by_label('epic')
        user_stories = await self._fetch_issues_by_label('user-story')
        defects = await self._fetch_issues_by_label('defect')

        # Build traceability relationships
        traceability_matrix = {
            'generated_at': datetime.utcnow().isoformat(),
            'repository': self.repo.full_name,
            'epics': {},
            'user_stories': {},
            'defects': {},
            'orphaned_items': [],
            'coverage_statistics': {}
        }

        # Process epics
        for epic in epics:
            epic_data = self._process_epic(epic)
            traceability_matrix['epics'][epic_data.id] = epic_data

        # Process user stories and link to epics
        for story in user_stories:
            story_data = self._process_user_story(story)
            traceability_matrix['user_stories'][story_data.id] = story_data

        # Process defects and link to stories/epics
        for defect in defects:
            defect_data = self._process_defect(defect)
            traceability_matrix['defects'][defect_data.id] = defect_data

        # Calculate coverage statistics
        traceability_matrix['coverage_statistics'] = self._calculate_coverage(
            traceability_matrix
        )

        return traceability_matrix

    def _process_epic(self, issue) -> TraceabilityItem:
        """Process epic issue into traceability item"""

        # Extract epic ID from issue body
        epic_id = self._extract_epic_id(issue.body)

        return TraceabilityItem(
            id=epic_id or f"EP-{issue.number:03d}",
            title=issue.title,
            type="epic",
            status=self._map_issue_state(issue.state, issue.labels),
            epic_id=None,  # Epics are top-level
            user_story_id=None,
            github_issue_url=issue.html_url,
            last_updated=issue.updated_at.isoformat()
        )

    def _calculate_coverage(self, rtm: Dict) -> Dict:
        """Calculate traceability coverage statistics"""

        total_epics = len(rtm['epics'])
        total_stories = len(rtm['user_stories'])
        total_defects = len(rtm['defects'])

        # Count stories linked to epics
        linked_stories = sum(
            1 for story in rtm['user_stories'].values()
            if story.epic_id and story.epic_id in rtm['epics']
        )

        # Count defects linked to stories
        linked_defects = sum(
            1 for defect in rtm['defects'].values()
            if defect.user_story_id and defect.user_story_id in rtm['user_stories']
        )

        return {
            'total_epics': total_epics,
            'total_user_stories': total_stories,
            'total_defects': total_defects,
            'epic_to_story_coverage': (linked_stories / total_stories * 100) if total_stories > 0 else 0,
            'story_to_defect_coverage': (linked_defects / total_defects * 100) if total_defects > 0 else 0,
            'orphaned_stories': total_stories - linked_stories,
            'orphaned_defects': total_defects - linked_defects
        }
```

## 🌐 GitHub Pages Architecture

### Documentation Site Structure
```
GitHub Pages Site (https://username.github.io/repo)
├── index.html (Documentation Home)
├── rtm/
│   ├── index.html (Requirements Traceability Matrix)
│   ├── epics/ (Epic Details)
│   ├── user-stories/ (User Story Details)
│   └── defects/ (Defect Reports)
├── technical/
│   ├── architecture/ (Technical Architecture)
│   ├── implementation/ (Implementation Guides)
│   └── api/ (API Documentation)
└── search/
    ├── index.html (Documentation Search)
    └── search-index.json (Search Data)
```

### Static Site Generation
```python
# .github/scripts/build_documentation_site.py
class DocumentationSiteBuilder:
    def __init__(self, rtm_data: Dict, repo_content: Dict):
        self.rtm = rtm_data
        self.content = repo_content

    async def build_site(self, output_dir: str):
        """Build complete documentation site"""

        # Generate main index page
        await self._generate_index_page(output_dir)

        # Generate RTM pages
        await self._generate_rtm_pages(output_dir)

        # Generate technical documentation pages
        await self._generate_technical_pages(output_dir)

        # Generate search functionality
        await self._generate_search_index(output_dir)

        # Copy static assets
        await self._copy_static_assets(output_dir)

    async def _generate_rtm_pages(self, output_dir: str):
        """Generate RTM-specific pages"""

        rtm_dir = os.path.join(output_dir, 'rtm')
        os.makedirs(rtm_dir, exist_ok=True)

        # Main RTM overview
        rtm_html = self._render_template('rtm_overview.html', {
            'rtm': self.rtm,
            'coverage_stats': self.rtm['coverage_statistics']
        })

        with open(os.path.join(rtm_dir, 'index.html'), 'w') as f:
            f.write(rtm_html)

        # Individual epic pages
        epics_dir = os.path.join(rtm_dir, 'epics')
        os.makedirs(epics_dir, exist_ok=True)

        for epic_id, epic_data in self.rtm['epics'].items():
            epic_html = self._render_template('epic_detail.html', {
                'epic': epic_data,
                'user_stories': self._get_epic_user_stories(epic_id),
                'defects': self._get_epic_defects(epic_id)
            })

            with open(os.path.join(epics_dir, f'{epic_id}.html'), 'w') as f:
                f.write(epic_html)
```

---

**Related Documentation**:
- [Implementation Details](implementation.md)
- [Performance Optimization](performance.md)
- [API Design](api-design.md)