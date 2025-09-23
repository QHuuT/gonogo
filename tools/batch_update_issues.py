#!/usr/bin/env python3
"""
Batch Update GitHub Issues with New Template Format

Updates multiple GitHub issues efficiently using the new template format.
"""

import subprocess
import json
import re
import sys
import time
sys.path.append('src')

from be.database import SessionLocal
from be.models.traceability.user_story import UserStory
from be.models.traceability.defect import Defect

def get_all_issues():
    """Get all GitHub issues."""
    result = subprocess.run(['gh', 'issue', 'list', '--limit', '200', '--json', 'number,title'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    return []

def get_issue_content(issue_number):
    """Get issue content."""
    result = subprocess.run(['gh', 'issue', 'view', str(issue_number), '--json', 'title,body'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None

def generate_user_story_template(title, body, db_data=None):
    """Generate user story template."""
    # Extract user story format from existing body
    us_match = re.search(r'\*\*As a\*\* (.+?)\n\*\*I want\*\* (.+?)\n\*\*So that\*\* (.+?)(?:\n|$)', body)

    if us_match:
        as_a = us_match.group(1).strip()
        i_want = us_match.group(2).strip()
        so_that = us_match.group(3).strip()
    else:
        as_a = "user"
        i_want = "[to be defined]"
        so_that = "[benefit to be defined]"

    # Extract business value
    bv_match = re.search(r'## Business Value\s*\n(.*?)(?=\n##|\n---|$)', body, re.DOTALL | re.IGNORECASE)
    business_value = bv_match.group(1).strip() if bv_match else "[Business value to be defined]"

    # Extract story points
    sp_match = re.search(r'(?:Story Points?|Points?|Estimate)[:\s]*(\d+)', body, re.IGNORECASE)
    story_points = sp_match.group(1) if sp_match else "0"

    # Extract priority
    priority_match = re.search(r'Priority.*?([Hh]igh|[Mm]edium|[Ll]ow|[Cc]ritical)', body, re.IGNORECASE)
    priority = priority_match.group(1).lower() if priority_match else "medium"

    # Extract component
    component_match = re.search(r'Component.*?([Ff]rontend|[Bb]ackend|[Dd]atabase|[Ss]ecurity|[Tt]esting|[Cc]i.?[Cc][Dd]|[Dd]ocumentation)', body, re.IGNORECASE)
    component = component_match.group(1) if component_match else "backend"

    # Extract acceptance criteria
    ac_match = re.search(r'## Acceptance Criteria[^#]*?\n(.*?)(?=\n##|\n---|$)', body, re.DOTALL | re.IGNORECASE)
    acceptance_criteria = ac_match.group(1).strip() if ac_match else "- [ ] **Given** [context], **When** [action], **Then** [expected result]"

    template = f"""## User Story
**As a** {as_a}
**I want** {i_want}
**So that** {so_that}

## Business Value
{business_value}

## Story Points
{story_points}

## Priority
{priority}

## Target Release Version
v1.2.0

## Component
{component}

## Acceptance Criteria - Functional Requirements
{acceptance_criteria}

## GDPR Considerations
- [ ] Involves personal data processing
- [ ] GDPR compliance review needed
- [x] Not applicable

## Dependencies
None

## Blocks
None

## BDD Scenarios
- [ ] Has BDD scenarios defined
- [x] BDD scenarios need to be created"""

    return template

def generate_defect_template(title, body, db_data=None):
    """Generate defect template."""
    # Extract steps to reproduce
    steps_match = re.search(r'## Steps to Reproduce\s*\n(.*?)(?=\n##|\n---|$)', body, re.DOTALL | re.IGNORECASE)
    steps = steps_match.group(1).strip() if steps_match else "1. [Step to reproduce the issue]"

    # Extract expected behavior
    expected_match = re.search(r'## Expected Behavior\s*\n(.*?)(?=\n##|\n---|$)', body, re.DOTALL | re.IGNORECASE)
    expected = expected_match.group(1).strip() if expected_match else "[What should happen]"

    # Extract actual behavior
    actual_match = re.search(r'## Actual Behavior\s*\n(.*?)(?=\n##|\n---|$)', body, re.DOTALL | re.IGNORECASE)
    actual = actual_match.group(1).strip() if actual_match else "[What actually happens]"

    # Extract business impact
    impact_match = re.search(r'## Business Impact\s*\n(.*?)(?=\n##|\n---|$)', body, re.DOTALL | re.IGNORECASE)
    impact = impact_match.group(1).strip() if impact_match else "[Impact on users and business]"

    template = f"""## Steps to Reproduce
{steps}

## Expected Behavior
{expected}

## Actual Behavior
{actual}

## Business Impact
{impact}

## Defect Type
bug

## Severity
medium

## Priority
medium

## Environment
Dev

## Component
Backend/API

## Quality Flags
- [ ] Escaped to production
- [ ] Security issue
- [ ] Regression from previous version
- [ ] Affects customers
- [ ] GDPR/Privacy impact"""

    return template

def update_issue(issue_number, new_body):
    """Update GitHub issue with new body."""
    with open(f'temp_issue_{issue_number}.md', 'w', encoding='utf-8') as f:
        f.write(new_body)

    result = subprocess.run(['gh', 'issue', 'edit', str(issue_number), '--body-file', f'temp_issue_{issue_number}.md'],
                          capture_output=True, text=True)

    # Clean up temp file
    import os
    try:
        os.remove(f'temp_issue_{issue_number}.md')
    except:
        pass

    return result.returncode == 0

def batch_update_issues():
    """Batch update all issues."""
    session = SessionLocal()

    try:
        issues = get_all_issues()
        print(f"Found {len(issues)} issues to process")

        updated_count = 0
        skipped_count = 0

        for issue in issues:
            issue_number = issue['number']
            title = issue['title']

            # Skip if already processed or not US/DEF
            if not (re.search(r'US-\d{5}', title) or re.search(r'DEF-\d{5}', title)):
                skipped_count += 1
                continue

            print(f"\nProcessing issue #{issue_number}: {title}")

            # Get issue content
            content = get_issue_content(issue_number)
            if not content:
                print(f"  Failed to get content for #{issue_number}")
                continue

            body = content.get('body', '')

            # Generate new template
            if 'US-' in title:
                new_body = generate_user_story_template(title, body)
            elif 'DEF-' in title:
                new_body = generate_defect_template(title, body)
            else:
                skipped_count += 1
                continue

            # Update issue
            if update_issue(issue_number, new_body):
                print(f"  ✓ Updated #{issue_number}")
                updated_count += 1
            else:
                print(f"  ✗ Failed to update #{issue_number}")

            # Rate limiting
            time.sleep(1)

        print(f"\n=== BATCH UPDATE COMPLETE ===")
        print(f"Updated: {updated_count}")
        print(f"Skipped: {skipped_count}")

    finally:
        session.close()

if __name__ == '__main__':
    batch_update_issues()