# Developer Tooling API Design

**Last Updated**: 2025-09-20

## 🎯 API Overview

The Developer Tooling API provides GitHub integration patterns, automation interfaces, and RTM management endpoints. The design prioritizes GitHub-native integration, automation reliability, and documentation accuracy.

## 🌐 GitHub API Integration

### Issue Management Integration

#### GitHub Issues API Usage
```python
from github import Github

class GitHubIssueManager:
    def __init__(self, token: str, repo_name: str):
        self.github = Github(token)
        self.repo = self.github.get_repo(repo_name)

    async def create_epic_issue(self, epic_data: EpicData) -> Issue:
        """Create epic issue using GitHub API"""

        issue_body = self._format_epic_template(epic_data)

        issue = self.repo.create_issue(
            title=f"[EPIC] {epic_data.title}",
            body=issue_body,
            labels=['epic', 'needs-triage'],
            milestone=self._get_milestone(epic_data.milestone)
        )

        return issue

    async def update_issue_status(
        self,
        issue_number: int,
        new_status: str
    ) -> Issue:
        """Update issue status and labels"""

        issue = self.repo.get_issue(issue_number)

        # Update labels based on status
        status_labels = self._get_status_labels(new_status)
        issue.set_labels(*status_labels)

        # Add status comment
        issue.create_comment(f"Status updated to: {new_status}")

        return issue
```

### RTM API Endpoints

#### GitHub Actions Integration
```python
# Custom GitHub Action for RTM management
class RTMAction:
    def __init__(self, github_token: str):
        self.github = Github(github_token)

    async def sync_rtm_on_issue_change(
        self,
        issue_data: IssueChangeData
    ) -> RTMSyncResult:
        """Sync RTM when issues change"""

        # Extract issue information
        issue_info = self._parse_issue_data(issue_data)

        # Update RTM data structure
        rtm_update = await self._update_rtm_structure(issue_info)

        # Regenerate RTM files
        await self._regenerate_rtm_files(rtm_update)

        # Trigger documentation rebuild
        await self._trigger_docs_rebuild()

        return RTMSyncResult(
            success=True,
            updated_items=rtm_update.affected_items,
            processing_time=rtm_update.duration
        )

    async def generate_rtm_export(
        self,
        format_type: str = "json"
    ) -> RTMExport:
        """Generate RTM export in various formats"""

        rtm_data = await self._collect_current_rtm_data()

        if format_type == "json":
            export_data = json.dumps(rtm_data, indent=2)
        elif format_type == "csv":
            export_data = self._convert_to_csv(rtm_data)
        elif format_type == "html":
            export_data = self._generate_html_report(rtm_data)

        return RTMExport(
            format=format_type,
            data=export_data,
            generated_at=datetime.utcnow(),
            checksum=hashlib.sha256(export_data.encode()).hexdigest()
        )
```

## 📊 Data Models

### GitHub Integration Models

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict

class IssueTemplateData(BaseModel):
    """Structured data from GitHub issue templates"""
    epic_id: Optional[str] = Field(None, description="Epic identifier")
    user_story_id: Optional[str] = Field(None, description="User story identifier")
    parent_epic: Optional[str] = Field(None, description="Parent epic reference")
    description: str = Field(..., description="Issue description")
    acceptance_criteria: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)

class GitHubIssueData(BaseModel):
    """GitHub issue data structure"""
    number: int
    title: str
    body: str
    state: str
    labels: List[str]
    milestone: Optional[str]
    assignees: List[str]
    created_at: datetime
    updated_at: datetime
    html_url: str
    template_data: IssueTemplateData

class RTMEntry(BaseModel):
    """Requirements Traceability Matrix entry"""
    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="Item title")
    type: str = Field(..., description="Item type (epic, user-story, defect)")
    status: str = Field(..., description="Current status")
    github_issue_number: int = Field(..., description="GitHub issue number")
    github_url: str = Field(..., description="GitHub issue URL")
    parent_id: Optional[str] = Field(None, description="Parent item ID")
    children: List[str] = Field(default_factory=list, description="Child item IDs")
    created_at: datetime
    updated_at: datetime

class RTMMatrix(BaseModel):
    """Complete Requirements Traceability Matrix"""
    generated_at: datetime
    repository: str
    entries: Dict[str, RTMEntry]
    coverage_statistics: RTMCoverageStats
    validation_status: RTMValidationStatus
```

### Automation Models

```python
class WorkflowTriggerData(BaseModel):
    """GitHub Actions workflow trigger data"""
    event_type: str = Field(..., description="GitHub event type")
    repository: str = Field(..., description="Repository name")
    ref: str = Field(..., description="Git reference")
    payload: Dict = Field(..., description="Event payload")

class RTMSyncResult(BaseModel):
    """Result of RTM synchronization operation"""
    success: bool
    updated_items: List[str]
    processing_time: float
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class DocumentationBuildResult(BaseModel):
    """Result of documentation build operation"""
    success: bool
    build_time: float
    pages_generated: int
    static_files_copied: int
    errors: List[str] = Field(default_factory=list)
    deployment_url: Optional[str] = None

class RTMCoverageStats(BaseModel):
    """RTM coverage statistics"""
    total_epics: int
    total_user_stories: int
    total_defects: int
    linked_stories: int
    linked_defects: int
    epic_coverage_percentage: float
    story_coverage_percentage: float
    orphaned_items: int
```

## 🔧 GitHub Actions Interface

### Custom Actions API

#### Extract Issue Data Action
```yaml
# action.yml for extract-issue-data
name: 'Extract Issue Data'
description: 'Extract structured data from GitHub issue templates'
inputs:
  github-token:
    description: 'GitHub token for API access'
    required: true
  issue-number:
    description: 'Issue number to process'
    required: false
outputs:
  issue-data:
    description: 'Extracted issue data as JSON'
  issue-type:
    description: 'Detected issue type'
  relationships:
    description: 'Issue relationships as JSON'
runs:
  using: 'node16'
  main: 'index.js'
```

#### Update RTM Action
```yaml
# action.yml for update-rtm
name: 'Update RTM'
description: 'Update Requirements Traceability Matrix'
inputs:
  issue-data:
    description: 'Issue data JSON from extract action'
    required: true
  rtm-path:
    description: 'Path to RTM data file'
    required: false
    default: 'docs/rtm/rtm-data.json'
outputs:
  rtm-updated:
    description: 'Whether RTM was updated'
  affected-items:
    description: 'List of affected RTM items'
runs:
  using: 'python'
  main: 'update_rtm.py'
```

### Workflow APIs

#### RTM Synchronization Endpoint
```python
class RTMSynchronizationAPI:
    async def handle_issue_webhook(
        self,
        webhook_data: GitHubWebhookData
    ) -> RTMSyncResponse:
        """Handle GitHub issue webhook for RTM sync"""

        # Parse webhook data
        issue_data = self._parse_webhook_payload(webhook_data)

        # Determine if RTM update needed
        if not self._should_update_rtm(issue_data):
            return RTMSyncResponse(
                action="skipped",
                reason="No RTM impact"
            )

        # Update RTM
        sync_result = await self._perform_rtm_sync(issue_data)

        # Trigger documentation rebuild if needed
        if sync_result.success:
            await self._trigger_docs_rebuild()

        return RTMSyncResponse(
            action="updated",
            result=sync_result,
            next_steps=["docs_rebuild", "pages_deploy"]
        )

    async def generate_rtm_report(
        self,
        report_format: str = "html"
    ) -> RTMReportResponse:
        """Generate comprehensive RTM report"""

        rtm_data = await self._load_current_rtm()
        coverage_stats = await self._calculate_coverage(rtm_data)

        if report_format == "html":
            report_content = await self._generate_html_report(
                rtm_data, coverage_stats
            )
        elif report_format == "json":
            report_content = json.dumps({
                "rtm": rtm_data,
                "coverage": coverage_stats
            }, indent=2)

        return RTMReportResponse(
            format=report_format,
            content=report_content,
            coverage_stats=coverage_stats
        )
```

## 🚀 Performance Optimizations

### GitHub API Optimization

```python
class OptimizedGitHubAPI:
    def __init__(self, token: str, repo_name: str):
        self.github = Github(token, per_page=100)
        self.repo = self.github.get_repo(repo_name)
        self._issue_cache = {}

    async def batch_fetch_issues(
        self,
        issue_numbers: List[int]
    ) -> List[Issue]:
        """Fetch multiple issues efficiently"""

        # Check cache first
        cached_issues = []
        uncached_numbers = []

        for number in issue_numbers:
            if number in self._issue_cache:
                cached_issues.append(self._issue_cache[number])
            else:
                uncached_numbers.append(number)

        # Fetch uncached issues in batch
        if uncached_numbers:
            # Use GraphQL for batch fetching
            query = self._build_batch_issue_query(uncached_numbers)
            result = await self._execute_graphql_query(query)

            for issue_data in result['data']['repository']['issues']['nodes']:
                issue = self._parse_graphql_issue(issue_data)
                self._issue_cache[issue.number] = issue
                cached_issues.append(issue)

        return cached_issues

    def _build_batch_issue_query(self, issue_numbers: List[int]) -> str:
        """Build GraphQL query for batch issue fetching"""

        issue_queries = []
        for i, number in enumerate(issue_numbers):
            issue_queries.append(f'''
                issue{i}: issue(number: {number}) {{
                    number
                    title
                    body
                    state
                    labels(first: 20) {{ nodes {{ name }} }}
                    milestone {{ title }}
                    assignees(first: 10) {{ nodes {{ login }} }}
                    createdAt
                    updatedAt
                    url
                }}
            ''')\n        \n        return f'''\n        query {{\n            repository(owner: \"{self.repo.owner.login}\", name: \"{self.repo.name}\") {{\n                {''.join(issue_queries)}\n            }}\n        }}\n        '''\n```\n\n---\n\n**Related Documentation**:\n- [Architecture Decisions](architecture.md)\n- [Implementation Details](implementation.md)\n- [Performance Optimization](performance.md)"