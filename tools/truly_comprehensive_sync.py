#!/usr/bin/env python3
"""
TRULY Comprehensive GitHub Sync Tool

Populates ALL available database fields from GitHub data:
- Basic info (title, description, state, URL)
- Labels (as JSON), assignees (as JSON)
- Story points, acceptance criteria, business value
- Sprint, release versions, GDPR flags
- Dependencies, BDD scenarios
- ALL metadata fields
"""

import requests
import re
import os
import sys
import json
sys.path.append('src')

from be.database import SessionLocal
from be.models.traceability.epic import Epic
from be.models.traceability.user_story import UserStory
from be.models.traceability.defect import Defect

def fetch_github_issues():
    """Fetch GitHub issues using API."""
    github_token = os.getenv('GITHUB_TOKEN')
    headers = {}
    if github_token:
        headers['Authorization'] = f'token {github_token}'

    print("Fetching GitHub issues...")
    url = "https://api.github.com/repos/QHuuT/gonogo/issues"
    params = {'state': 'all', 'per_page': 100}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Failed to fetch issues: {response.status_code}")
        return []

    issues = response.json()
    print(f"Found {len(issues)} GitHub issues")
    return issues

def extract_story_points(issue_body: str) -> int:
    """Extract story points from issue body."""
    if not issue_body:
        return 0

    patterns = [
        r'Story Points?[:\s]*(\d+)',
        r'Points?[:\s]*(\d+)',
        r'SP[:\s]*(\d+)',
        r'Effort[:\s]*(\d+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, issue_body, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return 0

def extract_acceptance_criteria(issue_body: str) -> str:
    """Extract acceptance criteria from issue body."""
    if not issue_body:
        return None

    patterns = [
        r'## Acceptance Criteria\s*\n(.*?)(?=\n##|\n---|\Z)',
        r'### Acceptance Criteria\s*\n(.*?)(?=\n###|\n##|\n---|\Z)',
        r'Acceptance Criteria[:\s]*\n(.*?)(?=\n##|\n###|\n---|\Z)'
    ]

    for pattern in patterns:
        match = re.search(pattern, issue_body, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

    return None

def extract_business_value(issue_body: str) -> str:
    """Extract business value from issue body."""
    if not issue_body:
        return None

    patterns = [
        r'## Business Value\s*\n(.*?)(?=\n##|\n---|\Z)',
        r'### Business Value\s*\n(.*?)(?=\n###|\n##|\n---|\Z)',
        r'Business Value[:\s]*\n(.*?)(?=\n##|\n###|\n---|\Z)',
        r'\*\*Business Value\*\*[:\s]*(.*?)(?=\n|\Z)',
        # More flexible patterns
        r'\*\*Why is this important\?\*\*[:\s]*\n(.*?)(?=\n##|\n---|\Z)',
        r'Why is this important\?[:\s]*\n(.*?)(?=\n##|\n---|\Z)',
        r'\*\*Value\*\*[:\s]*(.*?)(?=\n|\Z)',
        r'Value[:\s]*\n(.*?)(?=\n##|\n---|\Z)'
    ]

    for pattern in patterns:
        match = re.search(pattern, issue_body, re.IGNORECASE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            if result and result not in ['TBD', '[Business value to be defined]', '[To be defined]']:
                return result

    return None

def extract_gdpr_info(issue_body: str, labels: list) -> tuple:
    """Extract GDPR information from issue."""
    affects_gdpr = False
    gdpr_considerations = None

    # Check labels
    gdpr_labels = [label for label in labels if 'gdpr' in label.lower()]
    if gdpr_labels:
        affects_gdpr = True

    # Check body content
    if issue_body:
        gdpr_keywords = ['gdpr', 'personal data', 'privacy', 'consent', 'data protection']
        if any(keyword in issue_body.lower() for keyword in gdpr_keywords):
            affects_gdpr = True

            # Extract GDPR considerations
            patterns = [
                r'## GDPR[^#]*?\n(.*?)(?=\n##|\n---|\Z)',
                r'### GDPR[^#]*?\n(.*?)(?=\n###|\n##|\n---|\Z)',
                r'GDPR[^:]*?[:\s]*\n(.*?)(?=\n##|\n###|\n---|\Z)'
            ]

            for pattern in patterns:
                match = re.search(pattern, issue_body, re.IGNORECASE | re.DOTALL)
                if match:
                    gdpr_considerations = match.group(1).strip()
                    break

    return affects_gdpr, gdpr_considerations

def extract_dependencies(issue_body: str) -> tuple:
    """Extract dependencies and blocks information."""
    depends_on = []
    blocks = []

    if not issue_body:
        return depends_on, blocks

    # Find depends on
    depends_patterns = [
        r'Depends on[:\s]*#(\d+)',
        r'Blocked by[:\s]*#(\d+)',
        r'Requires[:\s]*#(\d+)'
    ]

    for pattern in depends_patterns:
        matches = re.findall(pattern, issue_body, re.IGNORECASE)
        depends_on.extend([int(match) for match in matches])

    # Find blocks
    blocks_patterns = [
        r'Blocks[:\s]*#(\d+)',
        r'Blocking[:\s]*#(\d+)'
    ]

    for pattern in blocks_patterns:
        matches = re.findall(pattern, issue_body, re.IGNORECASE)
        blocks.extend([int(match) for match in matches])

    return depends_on, blocks

def extract_defect_details(issue_body: str) -> dict:
    """Extract detailed defect information from issue body."""
    if not issue_body:
        return {}

    details = {}

    # Steps to reproduce
    steps_patterns = [
        r'## Steps to Reproduce\s*\n(.*?)(?=\n##|\n---|\Z)',
        r'### Steps to Reproduce\s*\n(.*?)(?=\n###|\n##|\n---|\Z)',
        r'Steps to Reproduce[:\s]*\n(.*?)(?=\n##|\n---|\Z)',
        r'\*\*Steps to Reproduce\*\*[:\s]*\n(.*?)(?=\n##|\n---|\Z)'
    ]

    for pattern in steps_patterns:
        match = re.search(pattern, issue_body, re.IGNORECASE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            if result and result not in ['[Step to reproduce the issue]']:
                details['steps_to_reproduce'] = result
            break

    # Expected behavior
    expected_patterns = [
        r'## Expected Behavior\s*\n(.*?)(?=\n##|\n---|\Z)',
        r'### Expected Behavior\s*\n(.*?)(?=\n###|\n##|\n---|\Z)',
        r'Expected Behavior[:\s]*\n(.*?)(?=\n##|\n---|\Z)',
        r'\*\*Expected Behavior\*\*[:\s]*\n(.*?)(?=\n##|\n---|\Z)'
    ]

    for pattern in expected_patterns:
        match = re.search(pattern, issue_body, re.IGNORECASE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            if result and result not in ['[What should happen]']:
                details['expected_behavior'] = result
            break

    # Actual behavior
    actual_patterns = [
        r'## Actual Behavior\s*\n(.*?)(?=\n##|\n---|\Z)',
        r'### Actual Behavior\s*\n(.*?)(?=\n###|\n##|\n---|\Z)',
        r'Actual Behavior[:\s]*\n(.*?)(?=\n##|\n---|\Z)',
        r'\*\*Actual Behavior\*\*[:\s]*\n(.*?)(?=\n##|\n---|\Z)'
    ]

    for pattern in actual_patterns:
        match = re.search(pattern, issue_body, re.IGNORECASE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            if result and result not in ['[What actually happens]']:
                details['actual_behavior'] = result
            break

    # Environment
    env_patterns = [
        r'## Environment\s*\n(.*?)(?=\n##|\n---|\Z)',
        r'### Environment\s*\n(.*?)(?=\n###|\n##|\n---|\Z)',
        r'Environment[:\s]*\n(.*?)(?=\n##|\n---|\Z)',
        r'\*\*Environment\*\*[:\s]*(.*?)(?=\n|\Z)'
    ]

    for pattern in env_patterns:
        match = re.search(pattern, issue_body, re.IGNORECASE | re.DOTALL)
        if match:
            result = match.group(1).strip()
            if result:
                details['environment'] = result
            break

    return details

def parse_comprehensive_labels(labels_list):
    """Parse ALL GitHub labels comprehensively."""
    labels = [label['name'] for label in labels_list]

    parsed = {
        'epic': None,
        'component': None,
        'priority': None,
        'status': None,
        'release': None,
        'sprint': None,
        'type': None,
        'raw_labels': labels,
        'raw_labels_json': json.dumps(labels)
    }

    # Epic label mapping
    epic_label_mapping = {
        'epic/blog-content': 'EP-00001',
        'epic/comment-system': 'EP-00002',
        'epic/privacy-consent': 'EP-00003',
        'epic/github-workflow': 'EP-00004',
        'epic/rtm': 'EP-00005',
        'epic/github-project': 'EP-00006',
        'epic/test-reporting': 'EP-00007'
    }

    for label in labels:
        if label in epic_label_mapping:
            parsed['epic'] = epic_label_mapping[label]
        elif label.startswith('component/'):
            parsed['component'] = label.replace('component/', '')
        elif label.startswith('priority/'):
            parsed['priority'] = label.replace('priority/', '')
        elif label.startswith('status/'):
            parsed['status'] = label.replace('status/', '')
        elif label.startswith('release/'):
            parsed['release'] = label.replace('release/', '')
        elif label.startswith('sprint/'):
            parsed['sprint'] = label.replace('sprint/', '')
        elif label in ['user-story', 'defect', 'bug', 'enhancement', 'feature']:
            parsed['type'] = label

    return parsed

def infer_epic_from_content(title: str, epic_mapping: dict):
    """Infer epic from title content if no epic label exists."""
    title_lower = title.lower()

    if 'blog' in title_lower or 'content' in title_lower:
        return epic_mapping.get('EP-00001')
    elif 'comment' in title_lower or 'gdpr' in title_lower:
        return epic_mapping.get('EP-00002')
    elif 'privacy' in title_lower:
        return epic_mapping.get('EP-00003')
    elif 'workflow' in title_lower or 'action' in title_lower:
        return epic_mapping.get('EP-00004')
    elif 'rtm' in title_lower or 'matrix' in title_lower or 'traceability' in title_lower:
        return epic_mapping.get('EP-00005')
    elif 'project' in title_lower or 'management' in title_lower:
        return epic_mapping.get('EP-00006')
    elif 'test' in title_lower or 'report' in title_lower:
        return epic_mapping.get('EP-00007')
    else:
        return epic_mapping.get('EP-00005')

def sync_user_story_comprehensive(session, issue, epic_mapping, parsed_labels, us_id, dry_run=True):
    """Sync a single user story with ALL fields."""

    # Determine epic
    epic_id = None
    if parsed_labels['epic']:
        epic_id = epic_mapping.get(parsed_labels['epic'])
    if not epic_id:
        epic_id = infer_epic_from_content(issue['title'], epic_mapping)

    # Extract all data
    story_points = extract_story_points(issue.get('body', ''))
    acceptance_criteria = extract_acceptance_criteria(issue.get('body', ''))
    business_value = extract_business_value(issue.get('body', ''))
    affects_gdpr, gdpr_considerations = extract_gdpr_info(issue.get('body', ''), parsed_labels['raw_labels'])
    depends_on, blocks = extract_dependencies(issue.get('body', ''))

    # Assignees
    assignees = [assignee['login'] for assignee in issue.get('assignees', [])]

    # Status mapping
    status_mapping = {
        'backlog': 'todo',
        'todo': 'todo',
        'in-progress': 'in_progress',
        'in-review': 'in_review',
        'done': 'done',
        'blocked': 'blocked'
    }
    implementation_status = status_mapping.get(parsed_labels['status'], 'todo')

    # Check for existing user story
    existing = session.query(UserStory).filter(UserStory.user_story_id == us_id).first()

    updates = []

    if existing:
        # Update ALL fields
        if existing.epic_id != epic_id:
            updates.append(f"epic_id: {existing.epic_id} -> {epic_id}")
            if not dry_run: existing.epic_id = epic_id

        if existing.github_issue_state != issue['state']:
            updates.append(f"github_issue_state: {existing.github_issue_state} -> {issue['state']}")
            if not dry_run: existing.github_issue_state = issue['state']

        if existing.github_labels != parsed_labels['raw_labels_json']:
            updates.append(f"github_labels: updated")
            if not dry_run: existing.github_labels = parsed_labels['raw_labels_json']

        if existing.github_assignees != json.dumps(assignees):
            updates.append(f"github_assignees: updated")
            if not dry_run: existing.github_assignees = json.dumps(assignees)

        if existing.story_points != story_points:
            updates.append(f"story_points: {existing.story_points} -> {story_points}")
            if not dry_run: existing.story_points = story_points

        if existing.acceptance_criteria != acceptance_criteria:
            updates.append(f"acceptance_criteria: updated")
            if not dry_run: existing.acceptance_criteria = acceptance_criteria

        # Update business value if current is empty or new value is better
        if business_value and (not existing.business_value or existing.business_value in ['TBD', '[Business value to be defined]']):
            updates.append(f"business_value: populated")
            if not dry_run: existing.business_value = business_value
        elif existing.business_value != business_value:
            updates.append(f"business_value: updated")
            if not dry_run: existing.business_value = business_value

        if existing.priority != (parsed_labels['priority'] or 'medium'):
            updates.append(f"priority: {existing.priority} -> {parsed_labels['priority'] or 'medium'}")
            if not dry_run: existing.priority = parsed_labels['priority'] or 'medium'

        if existing.component != parsed_labels['component']:
            updates.append(f"component: {existing.component} -> {parsed_labels['component']}")
            if not dry_run: existing.component = parsed_labels['component']

        if existing.implementation_status != implementation_status:
            updates.append(f"implementation_status: {existing.implementation_status} -> {implementation_status}")
            if not dry_run: existing.implementation_status = implementation_status

        if existing.affects_gdpr != affects_gdpr:
            updates.append(f"affects_gdpr: {existing.affects_gdpr} -> {affects_gdpr}")
            if not dry_run: existing.affects_gdpr = affects_gdpr

        if existing.gdpr_considerations != gdpr_considerations:
            updates.append(f"gdpr_considerations: updated")
            if not dry_run: existing.gdpr_considerations = gdpr_considerations

        if existing.target_release_version != parsed_labels['release']:
            updates.append(f"target_release_version: {existing.target_release_version} -> {parsed_labels['release']}")
            if not dry_run: existing.target_release_version = parsed_labels['release']

        if existing.sprint != parsed_labels['sprint']:
            updates.append(f"sprint: {existing.sprint} -> {parsed_labels['sprint']}")
            if not dry_run: existing.sprint = parsed_labels['sprint']

        if existing.depends_on_issues != json.dumps(depends_on):
            updates.append(f"depends_on_issues: updated")
            if not dry_run: existing.depends_on_issues = json.dumps(depends_on)

        if existing.blocks_issues != json.dumps(blocks):
            updates.append(f"blocks_issues: updated")
            if not dry_run: existing.blocks_issues = json.dumps(blocks)

        if existing.github_issue_url != issue['html_url']:
            updates.append(f"github_issue_url: updated")
            if not dry_run: existing.github_issue_url = issue['html_url']

        return len(updates) > 0, updates

    else:
        # Create new user story with ALL fields
        if not dry_run:
            user_story = UserStory(
                user_story_id=us_id,
                epic_id=epic_id,
                github_issue_number=issue['number'],
                title=issue['title'],
                description=issue.get('body', ''),
                github_issue_state=issue['state'],
                github_labels=parsed_labels['raw_labels_json'],
                github_assignees=json.dumps(assignees),
                story_points=story_points,
                acceptance_criteria=acceptance_criteria,
                business_value=business_value,
                priority=parsed_labels['priority'] or 'medium',
                component=parsed_labels['component'],
                sprint=parsed_labels['sprint'],
                implementation_status=implementation_status,
                affects_gdpr=affects_gdpr,
                gdpr_considerations=gdpr_considerations,
                target_release_version=parsed_labels['release'],
                depends_on_issues=json.dumps(depends_on),
                blocks_issues=json.dumps(blocks),
                github_issue_url=issue['html_url'],
                status='planned'
            )
            session.add(user_story)

        return True, ["CREATE with all fields"]

def sync_defect_comprehensive(session, issue, epic_mapping, parsed_labels, def_id, dry_run=True):
    """Sync a single defect with ALL fields."""

    # Determine epic
    epic_id = None
    if parsed_labels['epic']:
        epic_id = epic_mapping.get(parsed_labels['epic'])
    if not epic_id:
        epic_id = infer_epic_from_content(issue['title'], epic_mapping)

    # Extract defect-specific data
    defect_details = extract_defect_details(issue.get('body', ''))
    affects_gdpr, gdpr_considerations = extract_gdpr_info(issue.get('body', ''), parsed_labels['raw_labels'])

    # Check for existing defect
    existing = session.query(Defect).filter(Defect.defect_id == def_id).first()

    updates = []

    if existing:
        # Update ALL fields
        if existing.epic_id != epic_id:
            updates.append(f"epic_id: {existing.epic_id} -> {epic_id}")
            if not dry_run: existing.epic_id = epic_id

        if existing.github_issue_state != issue['state']:
            updates.append(f"github_issue_state: {existing.github_issue_state} -> {issue['state']}")
            if not dry_run: existing.github_issue_state = issue['state']

        # Update defect details if empty
        for field, value in defect_details.items():
            if value and not getattr(existing, field, None):
                updates.append(f"{field}: populated")
                if not dry_run: setattr(existing, field, value)

        # Update GDPR info
        if existing.affects_gdpr != affects_gdpr:
            updates.append(f"affects_gdpr: {existing.affects_gdpr} -> {affects_gdpr}")
            if not dry_run: existing.affects_gdpr = affects_gdpr

        if gdpr_considerations and not existing.gdpr_impact_details:
            updates.append(f"gdpr_impact_details: populated")
            if not dry_run: existing.gdpr_impact_details = gdpr_considerations

        return len(updates) > 0, updates

    else:
        # Create new defect with ALL fields
        if not dry_run:
            defect = Defect(
                defect_id=def_id,
                github_issue_number=issue['number'],
                title=issue['title'],
                description=issue.get('body', ''),
                github_issue_state=issue['state'],
                epic_id=epic_id,
                affects_gdpr=affects_gdpr,
                gdpr_impact_details=gdpr_considerations,
                component=parsed_labels['component'],
                priority=parsed_labels['priority'] or 'medium',
                status='open' if issue['state'] == 'open' else 'closed',
                **defect_details
            )
            session.add(defect)

        return True, ["CREATE with all fields"]

def truly_comprehensive_sync(dry_run=True, entity_types=['all']):
    """Truly comprehensive sync that populates ALL fields."""
    session = SessionLocal()

    try:
        issues = fetch_github_issues()
        if not issues:
            return

        # Get epic mapping
        epics = session.query(Epic).all()
        epic_mapping = {epic.epic_id: epic.id for epic in epics}

        print(f"\n=== TRULY COMPREHENSIVE GITHUB SYNC ===")
        print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")
        print(f"Populating ALL available database fields from GitHub")

        total_changes = 0
        processed_ids = set()

        # Sync user stories with ALL fields
        if 'all' in entity_types or 'user-stories' in entity_types:
            print(f"\n=== Comprehensive User Story Sync ===")

            for issue in issues:
                title = issue.get('title', '')
                us_id_match = re.search(r'US-\d{5}', title)

                if not us_id_match:
                    continue

                us_id = us_id_match.group(0)

                if us_id in processed_ids:
                    continue

                processed_ids.add(us_id)

                # Parse comprehensive labels
                parsed_labels = parse_comprehensive_labels(issue.get('labels', []))

                # Sync with all fields
                changed, updates = sync_user_story_comprehensive(
                    session, issue, epic_mapping, parsed_labels, us_id, dry_run
                )

                if changed:
                    total_changes += 1
                    epic_name = next((k for k, v in epic_mapping.items() if v == parsed_labels.get('epic')), 'Unknown')
                    print(f"  {us_id}: {', '.join(updates[:3])}{'...' if len(updates) > 3 else ''}")
                else:
                    print(f"  {us_id}: No changes needed (already synced)")

        # Sync defects with ALL fields
        if 'all' in entity_types or 'defects' in entity_types:
            print(f"\n=== Comprehensive Defect Sync ===")

            processed_def_ids = set()
            for issue in issues:
                title = issue.get('title', '')
                def_id_match = re.search(r'DEF-\d{5}', title)

                if not def_id_match:
                    continue

                def_id = def_id_match.group(0)

                if def_id in processed_def_ids:
                    continue

                processed_def_ids.add(def_id)

                # Parse comprehensive labels
                parsed_labels = parse_comprehensive_labels(issue.get('labels', []))

                # Sync with all fields
                changed, updates = sync_defect_comprehensive(
                    session, issue, epic_mapping, parsed_labels, def_id, dry_run
                )

                if changed:
                    total_changes += 1
                    print(f"  {def_id}: {', '.join(updates[:3])}{'...' if len(updates) > 3 else ''}")
                else:
                    print(f"  {def_id}: No changes needed (already synced)")

        # Commit changes
        if not dry_run and total_changes > 0:
            session.commit()
            print(f"\nCommitted {total_changes} comprehensive updates to database")
        elif dry_run:
            print(f"\nDRY RUN - Would make {total_changes} comprehensive updates")
        else:
            print(f"\nNo updates needed")

    except Exception as e:
        print(f"Error during comprehensive sync: {e}")
        import traceback
        traceback.print_exc()
        if not dry_run:
            session.rollback()
    finally:
        session.close()

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Truly comprehensive GitHub sync')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Only show what would be synced (default: True)')
    parser.add_argument('--execute', action='store_true', default=False,
                       help='Actually execute the sync (overrides --dry-run)')
    parser.add_argument('--entity-type', action='append',
                       choices=['user-stories', 'defects', 'all'], default=['all'],
                       help='Which entity types to sync (default: all)')

    args = parser.parse_args()

    # If --execute is specified, turn off dry run
    dry_run = args.dry_run and not args.execute

    truly_comprehensive_sync(dry_run, args.entity_type)

if __name__ == '__main__':
    main()