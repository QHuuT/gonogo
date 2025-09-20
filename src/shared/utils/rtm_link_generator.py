"""
Requirements Traceability Matrix (RTM) Link Generator

Core engine for automating RTM link generation and validation.
Supports plugin architecture for extensibility.

Related Issue: US-00015 - Automated RTM link generation and validation
Epic: EP-00005 - RTM Automation
"""

import re
import os
import yaml
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import quote


@dataclass
class RTMLink:
    """Represents a link in the RTM."""
    text: str
    url: str
    type: str
    valid: bool = True
    error_message: Optional[str] = None


@dataclass
class RTMValidationResult:
    """Results of RTM validation."""
    total_links: int
    valid_links: int
    invalid_links: List[RTMLink]
    errors: List[str]
    warnings: List[str]


class RTMLinkGenerator:
    """Core RTM link generator with plugin support."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the RTM link generator."""
        self.config = self._load_config(config_path)
        self.github_owner = self.config.get('github', {}).get('owner', 'QHuuT')
        self.github_repo = self.config.get('github', {}).get('repo', 'gonogo')

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = "config/rtm-automation.yml"

        if not os.path.exists(config_path):
            # Return default configuration
            return {
                'github': {
                    'owner': 'QHuuT',
                    'repo': 'gonogo'
                },
                'link_patterns': {
                    'epic': 'https://github.com/{owner}/{repo}/issues?q=is%3Aissue+{id}',
                    'user_story': 'https://github.com/{owner}/{repo}/issues?q=is%3Aissue+{id}',
                    'defect': 'https://github.com/{owner}/{repo}/issues?q=is%3Aissue+{id}'
                }
            }

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def generate_github_issue_link(self, issue_id: str, bold: bool = False) -> str:
        """Generate GitHub issue search link."""
        pattern = self.config['link_patterns']['epic']  # Same pattern for all issue types
        url = pattern.format(
            owner=self.github_owner,
            repo=self.github_repo,
            id=quote(issue_id)
        )

        if bold:
            return f"[**{issue_id}**]({url})"
        else:
            return f"[{issue_id}]({url})"

    def generate_file_link(self, file_path: str, rtm_file_path: str, display_text: Optional[str] = None) -> str:
        """Generate relative file link from RTM location."""
        rtm_dir = Path(rtm_file_path).parent
        target_path = Path(file_path)

        try:
            relative_path = os.path.relpath(target_path, rtm_dir)
            # Normalize path separators for markdown
            relative_path = relative_path.replace('\\', '/')
        except ValueError:
            # Cannot create relative path, use absolute
            relative_path = str(target_path).replace('\\', '/')

        display = display_text or target_path.name
        return f"[{display}]({relative_path})"

    def generate_bdd_scenario_link(self, feature_file: str, scenario_name: str, rtm_file_path: str) -> str:
        """Generate BDD scenario link."""
        file_link = self.generate_file_link(feature_file, rtm_file_path)
        display_text = f"{Path(feature_file).name}:{scenario_name}"

        # Extract just the relative path from the generated link
        link_match = re.search(r'\]\(([^)]+)\)', file_link)
        if link_match:
            relative_path = link_match.group(1)
            return f"[{display_text}]({relative_path})"

        return f"[{display_text}]({feature_file})"

    def extract_references_from_rtm(self, rtm_content: str) -> List[Tuple[str, str]]:
        """Extract all references from RTM content."""
        references = []

        # Pattern to match markdown links: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(link_pattern, rtm_content)

        for text, url in matches:
            # Determine reference type
            if text.startswith('**EP-') and text.endswith('**'):
                ref_type = 'epic'
            elif text.startswith('US-'):
                ref_type = 'user_story'
            elif text.startswith('DEF-'):
                ref_type = 'defect'
            elif '.feature:' in text:
                ref_type = 'bdd_scenario'
            elif text.endswith('.py') or text.endswith('.md'):
                ref_type = 'file'
            else:
                ref_type = 'unknown'

            references.append((text, url, ref_type))

        return references

    def validate_github_link(self, issue_id: str) -> bool:
        """Validate GitHub issue link (placeholder for future GitHub API integration)."""
        # For now, just validate format
        pattern = r'^(EP|US|DEF)-\d{5}$'
        return bool(re.match(pattern, issue_id))

    def validate_file_link(self, file_path: str, rtm_file_path: str) -> bool:
        """Validate that file exists relative to RTM location."""
        if file_path.startswith('http'):
            return True  # External links assumed valid for now

        rtm_dir = Path(rtm_file_path).parent

        # Handle relative paths
        if not os.path.isabs(file_path):
            full_path = rtm_dir / file_path
        else:
            full_path = Path(file_path)

        return full_path.exists()

    def validate_rtm_links(self, rtm_file_path: str) -> RTMValidationResult:
        """Validate all links in RTM file."""
        with open(rtm_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        references = self.extract_references_from_rtm(content)

        valid_links = []
        invalid_links = []
        errors = []
        warnings = []

        for text, url, ref_type in references:
            rtm_link = RTMLink(text=text, url=url, type=ref_type)

            try:
                if ref_type in ['epic', 'user_story', 'defect']:
                    # Extract issue ID from text
                    issue_id = text.replace('**', '').strip()
                    if self.validate_github_link(issue_id):
                        valid_links.append(rtm_link)
                    else:
                        rtm_link.valid = False
                        rtm_link.error_message = f"Invalid GitHub issue format: {issue_id}"
                        invalid_links.append(rtm_link)

                elif ref_type == 'file' or ref_type == 'bdd_scenario':
                    if self.validate_file_link(url, rtm_file_path):
                        valid_links.append(rtm_link)
                    else:
                        rtm_link.valid = False
                        rtm_link.error_message = f"File not found: {url}"
                        invalid_links.append(rtm_link)

                else:
                    # Unknown type - add warning
                    warnings.append(f"Unknown link type for: {text}")
                    valid_links.append(rtm_link)

            except Exception as e:
                rtm_link.valid = False
                rtm_link.error_message = str(e)
                invalid_links.append(rtm_link)
                errors.append(f"Error validating {text}: {e}")

        return RTMValidationResult(
            total_links=len(references),
            valid_links=len(valid_links),
            invalid_links=invalid_links,
            errors=errors,
            warnings=warnings
        )

    def update_rtm_links(self, rtm_file_path: str, dry_run: bool = True) -> Dict[str, int]:
        """Update RTM links to current format."""
        with open(rtm_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        updates = {
            'epic_links': 0,
            'user_story_links': 0,
            'defect_links': 0,
            'file_links': 0
        }

        # Update epic links: [**EP-XXXXX**](old_url) -> [**EP-XXXXX**](new_url)
        epic_pattern = r'\[\*\*(EP-\d{5})\*\*\]\([^)]+\)'
        def update_epic_link(match):
            issue_id = match.group(1)
            new_link = self.generate_github_issue_link(issue_id, bold=True)
            updates['epic_links'] += 1
            return new_link

        content = re.sub(epic_pattern, update_epic_link, content)

        # Update user story links: [US-XXXXX](old_url) -> [US-XXXXX](new_url)
        us_pattern = r'\[(US-\d{5})\]\([^)]+\)'
        def update_us_link(match):
            issue_id = match.group(1)
            new_link = self.generate_github_issue_link(issue_id, bold=False)
            updates['user_story_links'] += 1
            return new_link

        content = re.sub(us_pattern, update_us_link, content)

        # Update defect links: [DEF-XXXXX](old_url) -> [DEF-XXXXX](new_url)
        def_pattern = r'\[(DEF-\d{5})\]\([^)]+\)'
        def update_def_link(match):
            issue_id = match.group(1)
            new_link = self.generate_github_issue_link(issue_id, bold=False)
            updates['defect_links'] += 1
            return new_link

        content = re.sub(def_pattern, update_def_link, content)

        if not dry_run and content != original_content:
            with open(rtm_file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return updates

    def generate_validation_report(self, validation_result: RTMValidationResult) -> str:
        """Generate human-readable validation report."""
        report = []
        report.append("# RTM Link Validation Report")
        report.append("")
        report.append(f"**Total Links**: {validation_result.total_links}")
        report.append(f"**Valid Links**: {validation_result.valid_links}")
        report.append(f"**Invalid Links**: {len(validation_result.invalid_links)}")
        report.append("")

        if validation_result.invalid_links:
            report.append("## Invalid Links")
            report.append("")
            for link in validation_result.invalid_links:
                report.append(f"- **{link.text}**: {link.error_message}")
            report.append("")

        if validation_result.warnings:
            report.append("## Warnings")
            report.append("")
            for warning in validation_result.warnings:
                report.append(f"- {warning}")
            report.append("")

        if validation_result.errors:
            report.append("## Errors")
            report.append("")
            for error in validation_result.errors:
                report.append(f"- {error}")
            report.append("")

        # Health score
        if validation_result.total_links > 0:
            health_score = (validation_result.valid_links / validation_result.total_links) * 100
            report.append(f"**Health Score**: {health_score:.1f}%")

        return "\n".join(report)


def main():
    """CLI entry point for RTM link generator."""
    import argparse

    parser = argparse.ArgumentParser(description='RTM Link Generator and Validator')
    parser.add_argument('--rtm-file',
                       default='docs/traceability/requirements-matrix.md',
                       help='Path to RTM file')
    parser.add_argument('--config',
                       help='Path to configuration file')
    parser.add_argument('--validate', action='store_true',
                       help='Validate RTM links')
    parser.add_argument('--update', action='store_true',
                       help='Update RTM links to current format')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be updated without making changes')
    parser.add_argument('--report',
                       help='Generate validation report to file')

    args = parser.parse_args()

    # Initialize generator
    generator = RTMLinkGenerator(args.config)

    if args.validate:
        print(f"Validating RTM links in {args.rtm_file}...")
        result = generator.validate_rtm_links(args.rtm_file)

        print(f"Total links: {result.total_links}")
        print(f"Valid links: {result.valid_links}")
        print(f"Invalid links: {len(result.invalid_links)}")

        if result.invalid_links:
            print("\nInvalid links:")
            for link in result.invalid_links:
                print(f"  - {link.text}: {link.error_message}")

        if args.report:
            report = generator.generate_validation_report(result)
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"Validation report saved to {args.report}")

    if args.update:
        print(f"Updating RTM links in {args.rtm_file}...")
        updates = generator.update_rtm_links(args.rtm_file, dry_run=args.dry_run)

        print("Updates:")
        for link_type, count in updates.items():
            if count > 0:
                print(f"  - {link_type}: {count}")

        if args.dry_run:
            print("(Dry run - no changes made)")


if __name__ == '__main__':
    main()