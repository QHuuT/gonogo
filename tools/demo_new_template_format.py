#!/usr/bin/env python3
"""
Demonstrate New Template Format

Shows how GitHub issues would look with the updated templates based on user feedback.
"""

import sys
sys.path.append('src')

from be.database import SessionLocal
from be.models.traceability.user_story import UserStory
from be.models.traceability.defect import Defect

def demo_user_story_template():
    """Show what a user story would look like with the new template."""
    session = SessionLocal()
    try:
        # Get a sample user story
        us = session.query(UserStory).filter(UserStory.user_story_id == 'US-00006').first()

        print("=== UPDATED USER STORY TEMPLATE EXAMPLE ===")
        print("Issue: US-00006: Implement Automated Epic Label Management and Inheritance System")
        print("\n--- NEW TEMPLATE FORMAT ---")

        template_body = f"""## User Story
**As a** project manager
**I want** automated epic label management and inheritance system
**So that** all child entities automatically inherit epic labels for better traceability

## Business Value
Eliminates manual label management and ensures consistent epic assignment across all entities.

## Story Points
{us.story_points if us else 0}

## Priority
{us.priority if us else 'medium'}

## Target Release Version
v1.2.0

## Component
{us.component if us else 'backend'}

## Acceptance Criteria - Functional Requirements
{us.acceptance_criteria if us and us.acceptance_criteria else '- [ ] **Given** epic is created, **When** child entities are added, **Then** they inherit epic labels'}

## GDPR Considerations
{'- [x] Involves personal data processing' if us and us.affects_gdpr else '- [ ] Involves personal data processing'}
- [ ] GDPR compliance review needed
- [ ] Not applicable

{'## GDPR Details' if us and us.gdpr_considerations else ''}
{us.gdpr_considerations if us and us.gdpr_considerations else ''}

## Dependencies
None

## Blocks
None

## BDD Scenarios
{'- [x] Has BDD scenarios defined' if us and us.has_bdd_scenarios else '- [ ] Has BDD scenarios defined'}
{'- [ ] BDD scenarios need to be created' if not (us and us.has_bdd_scenarios) else '- [x] BDD scenarios need to be created'}"""

        print(template_body)

    finally:
        session.close()

def demo_defect_template():
    """Show what a defect would look like with the new template."""
    session = SessionLocal()
    try:
        # Get a sample defect
        defect = session.query(Defect).filter(Defect.defect_id == 'DEF-00002').first()

        print("\n\n=== UPDATED DEFECT TEMPLATE EXAMPLE ===")
        print("Issue: DEF-00002: Form templates are too heavy")
        print("\n--- NEW TEMPLATE FORMAT ---")

        template_body = f"""## Steps to Reproduce
{defect.steps_to_reproduce if defect and defect.steps_to_reproduce else '1. Create a ticket'}

## Expected Behavior
{defect.expected_behavior if defect and defect.expected_behavior else 'Form templates are updated and easier'}

## Actual Behavior
{defect.actual_behavior if defect and defect.actual_behavior else 'Forms are too heavy'}

## Business Impact
{defect.customer_impact_details if defect and defect.customer_impact_details else 'No one will fill tickets'}

## Defect Type
{defect.defect_type if defect and defect.defect_type else 'bug'}

## Severity
{defect.severity if defect and defect.severity else 'medium'}

## Priority
{defect.priority if defect and defect.priority else 'medium'}

## Environment
{'Prod' if defect and defect.environment else 'Dev'}

## Component
{defect.component if defect and defect.component else 'Frontend/UI'}

## Quality Flags
- [ ] Escaped to production
- [ ] Security issue
- [ ] Regression from previous version
- [x] Affects customers
- [ ] GDPR/Privacy impact"""

        print(template_body)

    finally:
        session.close()

def main():
    """Main demo."""
    print("DEMO: Updated GitHub Issue Templates Following User Feedback")
    print("=" * 70)

    print("\nKey Changes Made:")
    print("1. REMOVED implementation-status from User Stories (synced via labels)")
    print("2. CHANGED target-release-version to dropdown with predefined versions")
    print("3. ADDED 'blocking' option to defect severity")
    print("4. CHANGED environment to dropdown: Prod/Demo/Staging/Dev")
    print()

    demo_user_story_template()
    demo_defect_template()

    print("\n" + "=" * 70)
    print("Template updates complete! Issues can now be updated using:")
    print("python tools/update_github_issues_templates.py --execute")
    print("(Requires GITHUB_TOKEN environment variable)")

if __name__ == '__main__':
    main()