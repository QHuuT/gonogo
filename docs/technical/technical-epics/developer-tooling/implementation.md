# Developer Tooling Implementation

**Last Updated**: 2025-09-20

## 🏗️ Implementation Overview

This document details the technical implementation of GitHub workflow integration, automation systems, and developer tooling infrastructure.

## 📁 Code Organization

### Repository Structure
```
.github/
├── ISSUE_TEMPLATE/
│   ├── epic.yml              # Epic issue template
│   ├── user-story.yml        # User story template
│   └── defect-report.yml     # Defect report template
├── workflows/
│   ├── rtm-sync.yml          # RTM synchronization
│   ├── deploy-docs.yml       # Documentation deployment
│   └── validate-issues.yml   # Issue validation
├── actions/
│   ├── extract-issue-data/   # Custom action for issue parsing
│   ├── update-rtm/           # RTM update action
│   └── build-docs/           # Documentation build action
└── scripts/
    ├── generate_rtm.py       # RTM generation script
    ├── build_site.py         # Site building script
    └── validate_templates.py # Template validation
```

## 🔧 Core Components

### 1. GitHub Issue Templates

#### Epic Template (`.github/ISSUE_TEMPLATE/epic.yml`)
```yaml
name: Epic
description: Create a new epic for major feature development
title: "[EPIC] "
labels: ["epic", "needs-triage"]
body:
  - type: input
    id: epic-id
    attributes:
      label: Epic ID
      description: Unique identifier for this epic
      placeholder: "EP-001"
    validations:
      required: true

  - type: textarea
    id: epic-description
    attributes:
      label: Epic Description
      description: Complete description using "As a... We want... So that..." format
    validations:
      required: true

  - type: checkboxes
    id: success-criteria
    attributes:
      label: Success Criteria
      options:
        - label: All user stories completed
        - label: Acceptance criteria met
        - label: Testing completed
```

#### User Story Template (`.github/ISSUE_TEMPLATE/user-story.yml`)
```yaml
name: User Story
description: Create a new user story
title: "[US] "
labels: ["user-story", "needs-triage"]
body:
  - type: input
    id: user-story-id
    attributes:
      label: User Story ID
      placeholder: "US-001"
    validations:
      required: true

  - type: input
    id: parent-epic
    attributes:
      label: Parent Epic
      description: Link to parent epic
      placeholder: "EP-001"

  - type: textarea
    id: story-description
    attributes:
      label: User Story
      description: "As a [user type], I want [functionality] so that [benefit]"
    validations:
      required: true
```

### 2. GitHub Actions Workflows

#### RTM Synchronization (`.github/workflows/rtm-sync.yml`)
```yaml
name: Sync Requirements Traceability Matrix

on:
  issues:
    types: [opened, edited, closed, labeled, unlabeled]
  pull_request:
    types: [opened, closed, merged]

jobs:
  sync-rtm:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: read
      pages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install PyGithub pyyaml jinja2

      - name: Extract issue data
        id: extract
        uses: ./.github/actions/extract-issue-data
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Update RTM
        uses: ./.github/actions/update-rtm
        with:
          issue-data: ${{ steps.extract.outputs.data }}
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Build documentation site
        uses: ./.github/actions/build-docs
        with:
          rtm-data: ${{ steps.update-rtm.outputs.rtm }}

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs-build
```

### 3. Custom GitHub Actions

#### Extract Issue Data Action
```javascript
// .github/actions/extract-issue-data/index.js
const core = require('@actions/core');
const github = require('@actions/github');

class IssueDataExtractor {
    constructor(githubToken) {
        this.octokit = github.getOctokit(githubToken);
        this.context = github.context;
    }

    async extractIssueData() {
        const { payload } = this.context;
        const issue = payload.issue || payload.pull_request;

        if (!issue) {
            core.info('No issue or PR data found');
            return null;
        }

        const issueData = {
            number: issue.number,
            title: issue.title,
            body: issue.body,
            state: issue.state,
            labels: issue.labels?.map(label => label.name) || [],
            milestone: issue.milestone?.title,
            assignees: issue.assignees?.map(assignee => assignee.login) || [],
            created_at: issue.created_at,
            updated_at: issue.updated_at,
            html_url: issue.html_url
        };

        // Parse structured data from issue template
        const templateData = this.parseIssueTemplate(issue.body);

        // Determine issue type and relationships
        const issueType = this.determineIssueType(issue.labels);
        const relationships = this.extractRelationships(templateData);

        const result = {
            ...issueData,
            type: issueType,
            template_data: templateData,
            relationships: relationships
        };

        core.setOutput('data', JSON.stringify(result));
        return result;
    }

    parseIssueTemplate(body) {
        if (!body) return {};

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

    determineIssueType(labels) {
        const labelNames = labels?.map(label =>
            typeof label === 'string' ? label : label.name
        ) || [];

        if (labelNames.includes('epic')) return 'epic';
        if (labelNames.includes('user-story')) return 'user-story';
        if (labelNames.includes('defect')) return 'defect';
        return 'unknown';
    }

    extractRelationships(templateData) {
        const relationships = {};

        // Extract parent epic reference
        if (templateData['Parent Epic']) {
            relationships.parent_epic = templateData['Parent Epic'].trim();
        }

        // Extract linked user story reference
        if (templateData['Related User Story']) {
            relationships.user_story = templateData['Related User Story'].trim();
        }

        return relationships;
    }
}

async function run() {
    try {
        const githubToken = core.getInput('github-token');
        const extractor = new IssueDataExtractor(githubToken);
        await extractor.extractIssueData();
    } catch (error) {
        core.setFailed(error.message);
    }
}

run();
```

### 4. RTM Generation System

#### RTM Generator (`.github/scripts/generate_rtm.py`)
```python
import json
import os
from datetime import datetime
from github import Github
from typing import Dict, List, Optional

class RTMGenerator:
    def __init__(self, github_token: str, repo_name: str):
        self.github = Github(github_token)
        self.repo = self.github.get_repo(repo_name)

    def generate_rtm(self) -> Dict:
        """Generate comprehensive requirements traceability matrix"""

        issues = list(self.repo.get_issues(state='all'))

        rtm_data = {
            'generated_at': datetime.utcnow().isoformat(),
            'repository': self.repo.full_name,
            'epics': {},
            'user_stories': {},
            'defects': {},
            'coverage_statistics': {}
        }

        # Categorize issues
        for issue in issues:
            labels = [label.name for label in issue.labels]

            if 'epic' in labels:
                rtm_data['epics'][f"EP-{issue.number:03d}"] = self._process_epic(issue)
            elif 'user-story' in labels:
                rtm_data['user_stories'][f"US-{issue.number:03d}"] = self._process_user_story(issue)
            elif 'defect' in labels:
                rtm_data['defects'][f"DF-{issue.number:03d}"] = self._process_defect(issue)

        # Calculate coverage statistics
        rtm_data['coverage_statistics'] = self._calculate_coverage(rtm_data)

        return rtm_data

    def _process_epic(self, issue) -> Dict:
        template_data = self._parse_issue_body(issue.body)

        return {
            'id': f"EP-{issue.number:03d}",
            'title': issue.title,
            'status': self._map_status(issue.state, issue.labels),
            'github_url': issue.html_url,
            'created_at': issue.created_at.isoformat(),
            'updated_at': issue.updated_at.isoformat(),
            'description': template_data.get('Epic Description', ''),
            'success_criteria': self._parse_checkboxes(template_data.get('Success Criteria', '')),
            'assignees': [assignee.login for assignee in issue.assignees],
            'milestone': issue.milestone.title if issue.milestone else None
        }

    def _process_user_story(self, issue) -> Dict:
        template_data = self._parse_issue_body(issue.body)

        return {
            'id': f"US-{issue.number:03d}",
            'title': issue.title,
            'status': self._map_status(issue.state, issue.labels),
            'github_url': issue.html_url,
            'parent_epic': template_data.get('Parent Epic', ''),
            'story_description': template_data.get('User Story', ''),
            'acceptance_criteria': self._parse_checkboxes(template_data.get('Acceptance Criteria', '')),
            'created_at': issue.created_at.isoformat(),
            'updated_at': issue.updated_at.isoformat()
        }

    def _parse_issue_body(self, body: str) -> Dict[str, str]:
        if not body:
            return {}

        sections = {}
        lines = body.split('\n')
        current_section = None
        current_content = []

        for line in lines:
            if line.startswith('### '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[4:].strip()
                current_content = []
            else:
                current_content.append(line)

        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def _calculate_coverage(self, rtm_data: Dict) -> Dict:
        total_epics = len(rtm_data['epics'])
        total_stories = len(rtm_data['user_stories'])

        # Count stories linked to epics
        linked_stories = 0
        for story in rtm_data['user_stories'].values():
            if story.get('parent_epic') and story['parent_epic'] in rtm_data['epics']:
                linked_stories += 1

        coverage_percentage = (linked_stories / total_stories * 100) if total_stories > 0 else 0

        return {
            'total_epics': total_epics,
            'total_user_stories': total_stories,
            'linked_stories': linked_stories,
            'epic_coverage_percentage': round(coverage_percentage, 2),
            'orphaned_stories': total_stories - linked_stories
        }
```

### 5. Documentation Site Builder

#### Site Builder (`.github/scripts/build_site.py`)
```python
import os
import json
from jinja2 import Environment, FileSystemLoader

class DocumentationSiteBuilder:
    def __init__(self, rtm_data: Dict, output_dir: str):
        self.rtm_data = rtm_data
        self.output_dir = output_dir
        self.env = Environment(loader=FileSystemLoader('.github/templates'))

    def build_site(self):
        """Build complete documentation site"""

        os.makedirs(self.output_dir, exist_ok=True)

        # Build main pages
        self._build_index_page()
        self._build_rtm_pages()
        self._copy_static_assets()

    def _build_index_page(self):
        template = self.env.get_template('index.html')
        html = template.render(
            rtm=self.rtm_data,
            title="Project Documentation",
            generated_at=self.rtm_data['generated_at']
        )

        with open(os.path.join(self.output_dir, 'index.html'), 'w') as f:
            f.write(html)

    def _build_rtm_pages(self):
        rtm_dir = os.path.join(self.output_dir, 'rtm')
        os.makedirs(rtm_dir, exist_ok=True)

        # Main RTM page
        template = self.env.get_template('rtm.html')
        html = template.render(rtm=self.rtm_data)

        with open(os.path.join(rtm_dir, 'index.html'), 'w') as f:
            f.write(html)

        # Individual epic pages
        epic_template = self.env.get_template('epic.html')
        for epic_id, epic_data in self.rtm_data['epics'].items():
            related_stories = self._get_epic_stories(epic_id)
            html = epic_template.render(
                epic=epic_data,
                stories=related_stories
            )

            with open(os.path.join(rtm_dir, f'{epic_id}.html'), 'w') as f:
                f.write(html)

    def _get_epic_stories(self, epic_id: str) -> List[Dict]:
        return [
            story for story in self.rtm_data['user_stories'].values()
            if story.get('parent_epic') == epic_id
        ]
```

## 🧪 Testing and Validation

### Template Validation
```python
# .github/scripts/validate_templates.py
import yaml
import os
from typing import List, Dict

class TemplateValidator:
    def validate_all_templates(self) -> bool:
        template_dir = '.github/ISSUE_TEMPLATE'
        templates = [f for f in os.listdir(template_dir) if f.endswith('.yml')]

        all_valid = True
        for template in templates:
            if not self.validate_template(os.path.join(template_dir, template)):
                all_valid = False

        return all_valid

    def validate_template(self, template_path: str) -> bool:
        try:
            with open(template_path, 'r') as f:
                template_data = yaml.safe_load(f)

            # Validate required fields
            required_fields = ['name', 'description', 'body']
            for field in required_fields:
                if field not in template_data:
                    print(f"ERROR: Missing required field '{field}' in {template_path}")
                    return False

            # Validate body structure
            if not self.validate_body_structure(template_data['body']):
                print(f"ERROR: Invalid body structure in {template_path}")
                return False

            print(f"OK: {template_path} is valid")
            return True

        except yaml.YAMLError as e:
            print(f"ERROR: YAML parsing error in {template_path}: {e}")
            return False
        except Exception as e:
            print(f"ERROR: Validation error in {template_path}: {e}")
            return False

    def validate_body_structure(self, body: List[Dict]) -> bool:
        for item in body:
            if 'type' not in item:
                return False
            if item['type'] not in ['input', 'textarea', 'dropdown', 'checkboxes']:
                return False

        return True
```

---

**Related Documentation**:
- [Architecture Decisions](architecture.md)
- [Performance Optimization](performance.md)
- [API Design](api-design.md)