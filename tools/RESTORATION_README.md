# GitHub Issues Restoration Guide

This guide covers the comprehensive restoration of all GitHub issues (epics, user stories, defects) to the RTM database.

## Scripts Overview

### 1. `restore_github_issues_comprehensive.py`
The main restoration script that:
- Fetches ALL GitHub issues using GitHub CLI
- Classifies issues as epics, user stories, or defects
- Maps GitHub labels to proper epic IDs
- Creates database records with correct foreign key relationships
- Handles all NOT NULL constraints and default values

### 2. `check_restoration_readiness.py`
Pre-flight check script that verifies:
- GitHub CLI installation and authentication
- Database connectivity
- Repository access permissions
- Required capabilities in database
- GitHub API rate limit status

## Prerequisites

### Required Software
- **GitHub CLI (gh)**: Install from https://cli.github.com/
- **Python 3.8+**: With required dependencies
- **Database**: SQLite (development) or PostgreSQL (production)

### Authentication Setup
```bash
# Authenticate with GitHub CLI
gh auth login

# Verify authentication
gh auth status
```

### Database Setup
```bash
# Ensure database is accessible
python -c "from src.be.database import check_database_health; print(check_database_health())"
```

## Usage Instructions

### Step 1: Check Readiness
Always run the readiness check first:

```bash
python tools/check_restoration_readiness.py --repo your-org/your-repo
```

### Step 2: Dry Run (Recommended)
See what would be created without making changes:

```bash
python tools/restore_github_issues_comprehensive.py --repo your-org/your-repo --dry-run
```

### Step 3: Full Restoration
Run the actual restoration:

```bash
python tools/restore_github_issues_comprehensive.py --repo your-org/your-repo
```

### Step 4: Verbose Output (if needed)
For debugging or detailed logging:

```bash
python tools/restore_github_issues_comprehensive.py --repo your-org/your-repo --verbose
```

## Expected Results

The script should restore:
- **8 Epics** (EP-00001 through EP-00010, excluding EP-00008 and EP-00009)
- **66 User Stories** (classified by epic labels)
- **10 Defects** (bugs and issues)
- **Total: 84 items**

### Epic Mapping
| Epic ID | GitHub Issue | Title | Capability |
|---------|--------------|-------|------------|
| EP-00010 | #88 | Dashboard de Traçabilité des Exigences Multi-Persona | CAP-00002 |
| EP-00003 | #64 | Privacy and Consent Management | CAP-00004 |
| EP-00002 | #63 | GDPR-Compliant Comment System | CAP-00004 |
| EP-00001 | #62 | Blog Content Management | CAP-00003 |
| EP-00007 | #17 | Test logging and reporting | CAP-00002 |
| EP-00006 | #13 | GitHub Project Management Integration | CAP-00001 |
| EP-00005 | #7 | Requirements Traceability Matrix Automation | CAP-00002 |
| EP-00004 | #1 | GitHub Workflow Integration | CAP-00001 |

### Capability Mapping
| Capability ID | Name | Description |
|---------------|------|-------------|
| CAP-00001 | GitHub Integration | Automations and integrations with GitHub workflows |
| CAP-00002 | Requirements Traceability | Traceability matrix, dashboards, and portfolio visibility |
| CAP-00003 | Blog Platform | Blog content experience and supporting platform capabilities |
| CAP-00004 | GDPR Compliance | Privacy, consent, and regulatory compliance capabilities |

## Issue Classification Logic

### Epic Classification
- Issues with `type/epic` label
- Issues with `epic/` prefix labels (e.g., `epic/multipersona-dashboard`)
- Known epic issue numbers (#88, #64, #63, #62, #17, #13, #7, #1)

### User Story Classification
- Issues with `type/user-story` label
- Issues with epic labels but not marked as epics
- Default classification for unlabeled issues

### Defect Classification
- Issues with `type/defect` or `type/bug` labels
- Issues with titles containing "defect", "bug", "fix", "error"

## Label Processing

### Component Extraction
Maps GitHub `component/` labels to database components:
- `component/frontend` → `frontend`
- `component/backend` → `backend`
- `component/security` → `security`
- etc.

### Priority Extraction
Maps GitHub `priority/` labels:
- `priority/critical` → `critical`
- `priority/high` → `high`
- `priority/medium` → `medium` (default)
- `priority/low` → `low`

### Story Points Extraction
Looks for patterns in issue body:
- "Story Points: 5"
- "SP: 3"
- "[5 pts]"
- "Points: 8"

## Database Schema Compliance

The script handles all NOT NULL constraints by providing defaults:

### Epic Defaults
- `total_story_points`: 0
- `completed_story_points`: 0
- `completion_percentage`: 0.0
- `priority`: "medium"
- `risk_level`: "medium"
- `component`: extracted from labels or "backend"
- All metric fields: 0 or appropriate defaults

### User Story Defaults
- `story_points`: extracted or 0
- `priority`: extracted or "medium"
- `implementation_status`: "completed" if closed, "todo" if open
- `has_bdd_scenarios`: false
- `affects_gdpr`: detected from labels

### Defect Defaults
- `severity`: extracted or "medium"
- `defect_type`: "bug"
- `found_in_phase`: "development"
- Boolean fields: detected from labels or false
- Numeric fields: 0.0

## Troubleshooting

### Common Issues

1. **GitHub CLI Authentication**
   ```bash
   gh auth login
   gh auth status
   ```

2. **Repository Access**
   ```bash
   gh repo view your-org/your-repo
   ```

3. **Database Connection**
   ```bash
   python -c "from src.be.database import get_db_session; print('DB OK')"
   ```

4. **Missing Capabilities**
   The script will auto-create missing capabilities (CAP-00001 through CAP-00004).

5. **API Rate Limits**
   Check remaining API calls:
   ```bash
   gh api /rate_limit
   ```

### Dry Run First
Always use `--dry-run` first to preview changes:
```bash
python tools/restore_github_issues_comprehensive.py --repo your-org/your-repo --dry-run
```

### Verbose Logging
Use `--verbose` for detailed debugging:
```bash
python tools/restore_github_issues_comprehensive.py --repo your-org/your-repo --verbose
```

## Success Criteria

After successful restoration, verify:

1. **Database counts match expectations**:
   - 8 epics in `epics` table
   - 66 user stories in `user_stories` table
   - 10 defects in `defects` table
   - 4 capabilities in `capabilities` table

2. **Foreign key relationships are correct**:
   - User stories link to correct epics
   - Epics link to correct capabilities
   - Defects optionally link to epics

3. **All NOT NULL constraints satisfied**:
   - No database integrity errors
   - All required fields have values

4. **GitHub data properly mapped**:
   - Issue numbers, titles, URLs preserved
   - Labels converted to appropriate database fields
   - Status reflects GitHub issue state

The restoration process should complete with a success message and statistics showing all 84 expected items were processed correctly.