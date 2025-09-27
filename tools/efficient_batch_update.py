#!/usr/bin/env python3
"""
Efficient Batch Update for GitHub Issues

Updates all remaining GitHub issues with new template format efficiently.
Run this script to update all remaining issues in batch.
"""

import subprocess
import json
import re
import time
import os

def run_gh_command(cmd):
    """Run GitHub CLI command safely."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Error running command {' '.join(cmd)}: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {' '.join(cmd)}")
        return None
    except Exception as e:
        print(f"Exception running command: {e}")
        return None

def get_all_issues():
    """Get all GitHub issues efficiently."""
    output = \
        run_gh_command(['gh', 'issue', 'list', '--limit', '200', '--json', 'number,title'])
    if output:
        return json.loads(output)
    return []

def get_issue_body(issue_number):
    """Get issue body efficiently."""
    output = \
        run_gh_command(['gh', 'issue', 'view', str(issue_number), '--json', 'body'])
    if output:
        data = json.loads(output)
        return data.get('body', '')
    return ''

def extract_user_story_content(body):
    """Extract key content from user story body."""
    content = {
        'as_a': 'user',
        'i_want': '[to be defined]',
        'so_that': '[benefit to be defined]',
        'business_value': '[Business value to be defined]',
        'story_points': '0',
        'priority': 'medium',
        'component': 'backend',
        'acceptance_criteria': '- [ ] **Given** [context], **When** [action], **Then** [expected result]'
    }

    # Extract user story format
    us_match = \
        re.search(r'\*\*As a\*\* (.+?)\n\*\*I want\*\* (.+?)\n\*\*So that\*\* (.+?)(?:\n|$)', body, re.DOTALL)
    if us_match:
        content['as_a'] = us_match.group(1).strip()
        content['i_want'] = us_match.group(2).strip()
        content['so_that'] = us_match.group(3).strip()

    # Extract business value
    bv_match = \
        re.search(r'## Business Value[^#]*?\n(.*?)(?=\n##|\n---|$)', body, re.DOTALL | re.IGNORECASE)
    if bv_match:
        bv = bv_match.group(1).strip()
        if bv and bv not in ['TBD', '[Business value to be defined]']:
            content['business_value'] = bv

    # Extract story points
    sp_match = \
        re.search(r'(?:Story Points?|Points?|Estimate)[:\s]*(\d+)', body, re.IGNORECASE)
    if sp_match:
        content['story_points'] = sp_match.group(1)

    # Extract priority
    priority_match = \
        re.search(r'Priority.*?([Hh]igh|[Mm]edium|[Ll]ow|[Cc]ritical)', body, re.IGNORECASE)
    if priority_match:
        content['priority'] = priority_match.group(1).lower()

    # Extract component
    component_match = \
        re.search(r'Component.*?([Ff]rontend|[Bb]ackend|[Dd]atabase|[Ss]ecurity|[Tt]esting|CI.?CD|[Dd]ocumentation)', body, re.IGNORECASE)
    if component_match:
        comp = component_match.group(1).lower()
        component_map = {
            'frontend': 'Frontend/UI',
            'backend': 'Backend/API',
            'database': 'Database',
            'security': 'Security/GDPR',
            'testing': 'Testing',
            'documentation': 'Documentation'
        }
        if 'ci' in comp or 'cd' in comp:
            content['component'] = 'CI/CD'
        else:
            content['component'] = component_map.get(comp, 'Backend/API')

    # Extract acceptance criteria
    ac_match = \
        re.search(r'## Acceptance Criteria[^#]*?\n(.*?)(?=\n##|\n---|$)', body, re.DOTALL | re.IGNORECASE)
    if ac_match:
        ac = ac_match.group(1).strip()
        if ac:
            content['acceptance_criteria'] = ac

    return content

def extract_defect_content(body):
    """Extract key content from defect body."""
    content = {
        'steps': '1. [Step to reproduce the issue]',
        'expected': '[What should happen]',
        'actual': '[What actually happens]',
        'impact': '[Impact on users and business]'
    }

    # Extract steps to reproduce
    steps_match = \
        re.search(r'## Steps to Reproduce[^#]*?\n(.*?)(?=\n##|\n---|$)', body, re.DOTALL | re.IGNORECASE)
    if steps_match:
        steps = steps_match.group(1).strip()
        if steps:
            content['steps'] = steps

    # Extract expected behavior
    expected_match = \
        re.search(r'## Expected Behavior[^#]*?\n(.*?)(?=\n##|\n---|$)', body, re.DOTALL | re.IGNORECASE)
    if expected_match:
        expected = expected_match.group(1).strip()
        if expected:
            content['expected'] = expected

    # Extract actual behavior
    actual_match = \
        re.search(r'## Actual Behavior[^#]*?\n(.*?)(?=\n##|\n---|$)', body, re.DOTALL | re.IGNORECASE)
    if actual_match:
        actual = actual_match.group(1).strip()
        if actual:
            content['actual'] = actual

    # Extract business impact
    impact_match = \
        re.search(r'## Business Impact[^#]*?\n(.*?)(?=\n##|\n---|$)', body, re.DOTALL | re.IGNORECASE)
    if impact_match:
        impact = impact_match.group(1).strip()
        if impact:
            content['impact'] = impact

    return content

def create_user_story_template(content):
    """Create new user story template."""
    return f"""## User Story
**As a** {content['as_a']}
**I want** {content['i_want']}
**So that** {content['so_that']}

## Business Value
{content['business_value']}

## Story Points
{content['story_points']}

## Priority
{content['priority']}

## Target Release Version
v1.2.0

## Component
{content['component']}

## Acceptance Criteria - Functional Requirements
{content['acceptance_criteria']}

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

def create_defect_template(content):
    """Create new defect template."""
    return f"""## Steps to Reproduce
{content['steps']}

## Expected Behavior
{content['expected']}

## Actual Behavior
{content['actual']}

## Business Impact
{content['impact']}

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

def update_issue(issue_number, new_body):
    """Update GitHub issue."""
    temp_file = f'temp_issue_{issue_number}.md'
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(new_body)

        result = \
            run_gh_command(['gh', 'issue', 'edit', str(issue_number), '--body-file', temp_file])
        return result is not None
    except Exception as e:
        print(f"Error updating issue {issue_number}: {e}")
        return False
    finally:
        try:
            os.remove(temp_file)
        except:
            pass

def main():
    """Main batch update function."""
    print("Starting efficient batch update of GitHub issues...")

    issues = get_all_issues()
    print(f"Found {len(issues)} total issues")

    # Filter for US/DEF issues only
    us_def_issues = \
        [issue for issue in issues if re.search(r'(US-\d{5}|DEF-\d{5})', issue['title'])]
    print(f"Found {len(us_def_issues)} US/DEF issues to update")

    updated_count = 0
    failed_count = 0

    for i, issue in enumerate(us_def_issues, 1):
        issue_number = issue['number']
        title = issue['title']

        print(
            f"\n[{i}/{len(us_def_issues)}]"
            f"Processing #{issue_number}: {title[:60]}..."
        )

        # Get issue body
        body = get_issue_body(issue_number)
        if not body:
            print(f"  Failed to get body for #{issue_number}")
            failed_count += 1
            continue

        # Generate template based on issue type
        if 'US-' in title:
            content = extract_user_story_content(body)
            new_body = create_user_story_template(content)
        elif 'DEF-' in title:
            content = extract_defect_content(body)
            new_body = create_defect_template(content)
        else:
            print(f"  Skipping #{issue_number} - not US or DEF")
            continue

        # Update issue
        if update_issue(issue_number, new_body):
            print(f"  Updated #{issue_number}")
            updated_count += 1
        else:
            print(f"  Failed to update #{issue_number}")
            failed_count += 1

        # Rate limiting to avoid API limits
        time.sleep(0.5)

    print(f"\nBATCH UPDATE COMPLETE!")
    print(f"Successfully updated: {updated_count}")
    print(f"Failed to update: {failed_count}")
    if updated_count + failed_count > 0:
        print(f"Success rate: {(updated_count/(updated_count+failed_count)*100):.1f}%")

if __name__ == '__main__':
    main()