#!/usr/bin/env python3
"""
Simple RTM Links CLI Tool (without emojis for Windows compatibility)

Command-line interface for RTM link generation and validation.

Related Issue: US-00015 - Automated RTM link generation and validation
Epic: EP-00005 - RTM Automation
"""

import sys
import os
from pathlib import Path

# Add src to Python path to import our modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from shared.utils.rtm_link_generator import RTMLinkGenerator


def main():
    """Simple CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Simple RTM Link Tool')
    parser.add_argument('--validate', action='store_true',
                       help='Validate RTM links')
    parser.add_argument('--update', action='store_true',
                       help='Update RTM links (dry run)')
    parser.add_argument('--rtm-file',
                       default='docs/traceability/requirements-matrix.md',
                       help='RTM file path')

    args = parser.parse_args()

    # Initialize generator
    try:
        generator = RTMLinkGenerator()
        print(f"RTM Generator initialized")
        print(f"GitHub: {generator.github_owner}/{generator.github_repo}")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    if args.validate:
        print(f"Validating {args.rtm_file}...")
        if not os.path.exists(args.rtm_file):
            print(f"Error: File not found: {args.rtm_file}")
            return 1

        try:
            result = generator.validate_rtm_links(args.rtm_file)
            print(f"Total links: {result.total_links}")
            print(f"Valid links: {result.valid_links}")
            print(f"Invalid links: {len(result.invalid_links)}")

            if result.invalid_links:
                print("Invalid links found:")
                for link in result.invalid_links[:5]:  # Show first 5
                    print(f"  - {link.text}: {link.error_message}")

            if result.total_links > 0:
                health = (result.valid_links / result.total_links) * 100
                print(f"Health score: {health:.1f}%")

        except Exception as e:
            print(f"Validation error: {e}")
            return 1

    if args.update:
        print(f"Updating {args.rtm_file} (dry run)...")
        if not os.path.exists(args.rtm_file):
            print(f"Error: File not found: {args.rtm_file}")
            return 1

        try:
            updates = generator.update_rtm_links(args.rtm_file, dry_run=True)
            print("Updates that would be made:")
            for link_type, count in updates.items():
                if count > 0:
                    print(f"  - {link_type}: {count}")

        except Exception as e:
            print(f"Update error: {e}")
            return 1

    if not args.validate and not args.update:
        print("Use --validate or --update")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())