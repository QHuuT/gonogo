#!/usr/bin/env python3
"""
Validation script for GitHub issue templates
Ensures all templates are properly formatted and contain required fields
"""

import os
import yaml
from pathlib import Path

def validate_template(template_path):
    """Validate a single GitHub issue template"""
    print(f"Validating {template_path.name}...")

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"  ERROR: YAML parsing error: {e}")
        return False
    except Exception as e:
        print(f"  ERROR: Error reading file: {e}")
        return False

    # Required fields
    required_fields = ['name', 'description', 'title', 'labels', 'body']
    missing_fields = []

    for field in required_fields:
        if field not in template:
            missing_fields.append(field)

    if missing_fields:
        print(f"  ERROR: Missing required fields: {', '.join(missing_fields)}")
        return False

    # Validate body structure
    if not isinstance(template['body'], list):
        print(f"  ERROR: 'body' must be a list")
        return False

    # Check for required input fields based on template type
    template_name = template_path.stem
    required_inputs = {
        'epic': ['epic-id', 'epic-name', 'priority', 'epic-description'],
        'user-story': ['story-id', 'epic-link', 'priority', 'complexity'],
        'defect-report': ['defect-id', 'related-epic', 'related-user-story', 'priority', 'severity']
    }

    if template_name in required_inputs:
        body_ids = []
        for item in template['body']:
            if item.get('type') in ['input', 'textarea', 'dropdown'] and 'id' in item:
                body_ids.append(item['id'])

        missing_inputs = []
        for required_input in required_inputs[template_name]:
            if required_input not in body_ids:
                missing_inputs.append(required_input)

        if missing_inputs:
            print(f"  ERROR: Missing required input fields: {', '.join(missing_inputs)}")
            return False

    print(f"  OK: Valid template")
    return True

def validate_config(config_path):
    """Validate issue template config"""
    print(f"Validating {config_path.name}...")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"  ERROR: YAML parsing error: {e}")
        return False
    except Exception as e:
        print(f"  ERROR: Error reading file: {e}")
        return False

    # Check if blank issues are properly configured
    if 'blank_issues_enabled' in config:
        print(f"  OK: Blank issues configured: {config['blank_issues_enabled']}")

    # Check contact links
    if 'contact_links' in config and isinstance(config['contact_links'], list):
        print(f"  OK: Contact links configured: {len(config['contact_links'])} links")

    print(f"  OK: Valid config")
    return True

def validate_labels(labels_path):
    """Validate labels configuration"""
    print(f"Validating {labels_path.name}...")

    try:
        with open(labels_path, 'r', encoding='utf-8') as f:
            labels = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"  ERROR: YAML parsing error: {e}")
        return False
    except Exception as e:
        print(f"  ERROR: Error reading file: {e}")
        return False

    if not isinstance(labels, list):
        print(f"  ERROR: Labels file must contain a list")
        return False

    # Check each label has required fields
    for i, label in enumerate(labels):
        if not isinstance(label, dict):
            print(f"  ERROR: Label {i} is not a dictionary")
            return False

        if 'name' not in label or 'color' not in label:
            print(f"  ERROR: Label {i} missing required fields (name, color)")
            return False

    print(f"  OK: Valid labels file with {len(labels)} labels")
    return True

def main():
    """Main validation function"""
    print("Validating GitHub issue templates and configuration...")
    print()

    github_dir = Path(__file__).parent
    template_dir = github_dir / 'ISSUE_TEMPLATE'

    all_valid = True

    # Validate issue templates
    template_files = list(template_dir.glob('*.yml'))
    template_files = [f for f in template_files if f.name != 'config.yml']

    for template_file in template_files:
        if not validate_template(template_file):
            all_valid = False
        print()

    # Validate config
    config_file = template_dir / 'config.yml'
    if config_file.exists():
        if not validate_config(config_file):
            all_valid = False
        print()

    # Validate labels
    labels_file = github_dir / 'labels.yml'
    if labels_file.exists():
        if not validate_labels(labels_file):
            all_valid = False
        print()

    # Summary
    if all_valid:
        print("SUCCESS: All templates and configurations are valid!")
        print()
        print("Summary:")
        print(f"  - {len(template_files)} issue templates")
        print(f"  - 1 configuration file")
        print(f"  - 1 labels file")
        print()
        print("Ready to use GitHub issue templates!")
        return 0
    else:
        print("ERROR: Some templates or configurations have errors.")
        print("Please fix the issues above and run validation again.")
        return 1

if __name__ == '__main__':
    exit(main())