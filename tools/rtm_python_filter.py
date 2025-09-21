#!/usr/bin/env python3
"""
RTM Python-Based Filtering Tool

Demonstrates how to use Python for filtering RTM data instead of JavaScript.
This tool shows server-side filtering capabilities with command-line interface.

Usage:
    python tools/rtm_python_filter.py --us-status completed --test-type e2e --defect-priority critical
    python tools/rtm_python_filter.py --format html --output filtered_report.html
    python tools/rtm_python_filter.py --help

Related Issue: US-00001 - Enhanced RTM filtering system
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.be.database import get_db_session
from src.be.services.rtm_report_generator import RTMReportGenerator


def main():
    parser = argparse.ArgumentParser(
        description="Python-based RTM filtering tool - No JavaScript needed!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Filter user stories by status
  python tools/rtm_python_filter.py --us-status completed --format html

  # Show only E2E tests and critical defects
  python tools/rtm_python_filter.py --test-type e2e --defect-priority critical

  # Generate report with multiple filters
  python tools/rtm_python_filter.py --us-status in_progress --test-type unit --defect-status open

  # Export to specific file
  python tools/rtm_python_filter.py --format html --output quality/reports/filtered_rtm.html

Python-based filtering advantages:
  - Server-side processing (faster for large datasets)
  - No JavaScript dependencies
  - Better accessibility
  - Easier testing and automation
  - More secure (no client-side filtering)
        """
    )

    # Output format
    parser.add_argument('--format', choices=['html', 'json', 'markdown'], default='html',
                       help='Output format (default: html)')
    parser.add_argument('--output', type=str,
                       help='Output file path (default: quality/reports/rtm_python_filtered.{format})')

    # Epic filters
    parser.add_argument('--epic-filter', type=str,
                       help='Filter by epic ID (e.g., EP-00001)')
    parser.add_argument('--epic-status', type=str,
                       help='Filter by epic status (planned, in_progress, completed)')
    parser.add_argument('--epic-priority', type=str,
                       help='Filter by epic priority (low, medium, high, critical)')

    # User Story filters
    parser.add_argument('--us-status', choices=['all', 'planned', 'in_progress', 'completed', 'blocked'],
                       default='all', help='Filter user stories by status (default: all)')

    # Test filters
    parser.add_argument('--test-type', choices=['all', 'unit', 'integration', 'e2e', 'security', 'bdd'],
                       default='e2e', help='Filter tests by type (default: e2e - shows least clutter)')

    # Defect filters
    parser.add_argument('--defect-priority', choices=['all', 'critical', 'high', 'medium', 'low'],
                       default='all', help='Filter defects by priority (default: all)')
    parser.add_argument('--defect-status', choices=['all', 'open', 'in_progress', 'resolved', 'closed'],
                       default='all', help='Filter defects by status (default: all)')

    # Include/exclude sections
    parser.add_argument('--no-tests', action='store_true',
                       help='Exclude test coverage section')
    parser.add_argument('--no-defects', action='store_true',
                       help='Exclude defect tracking section')

    # Display options
    parser.add_argument('--show-stats', action='store_true',
                       help='Show filtering statistics before generating report')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed processing information')
    parser.add_argument('--include-demo-data', action='store_true',
                       help='Include demo epics (EP-DEMO-*) in the report')

    args = parser.parse_args()

    # Build filters dictionary
    filters = {
        'epic_id': args.epic_filter,
        'status': args.epic_status,
        'priority': args.epic_priority,
        'us_status_filter': args.us_status,
        'test_type_filter': args.test_type,
        'defect_priority_filter': args.defect_priority,
        'defect_status_filter': args.defect_status,
        'include_tests': not args.no_tests,
        'include_defects': not args.no_defects,
        'include_demo_data': args.include_demo_data,
    }

    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    if args.verbose:
        print("Python-based RTM Filtering Tool")
        print("=" * 50)
        print(f"Filters applied: {filters}")
        print()

    # Initialize database and generator
    try:
        db = get_db_session()
        generator = RTMReportGenerator(db)

        if args.show_stats:
            print("Filtering Statistics:")
            stats = get_filtering_stats(generator, filters)
            for key, value in stats.items():
                print(f"  {key}: {value}")
            print()

        # Generate report
        if args.verbose:
            print(f"Generating {args.format.upper()} report with Python filtering...")

        if args.format == 'html':
            content = generator.generate_html_matrix(filters)
        elif args.format == 'json':
            import json
            content = json.dumps(generator.generate_json_matrix(filters), indent=2)
        elif args.format == 'markdown':
            content = generator.generate_markdown_matrix(filters)

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            output_dir = Path("quality/reports/dynamic_rtm")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"rtm_python_filtered.{args.format}"

        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Python-filtered RTM report saved to: {output_path}")

        if args.verbose:
            file_size = output_path.stat().st_size
            print(f"Report size: {file_size:,} bytes")
            print(f"View report: file://{output_path.absolute()}")

    except Exception as e:
        print(f"Error generating report: {e}")
        return 1
    finally:
        if 'db' in locals():
            db.close()

    return 0


def get_filtering_stats(generator, filters: Dict[str, Any]) -> Dict[str, Any]:
    """Get statistics about the filtering operation."""
    # Get all data without filters
    all_filters = {'include_tests': True, 'include_defects': True}
    all_data = generator.generate_json_matrix(all_filters)

    # Get filtered data
    filtered_data = generator.generate_json_matrix(filters)

    return {
        'Total Epics': len(all_data['epics']),
        'Filtered Epics': len(filtered_data['epics']),
        'User Story Filter': filters.get('us_status_filter', 'all'),
        'Test Type Filter': filters.get('test_type_filter', 'e2e'),
        'Defect Priority Filter': filters.get('defect_priority_filter', 'all'),
        'Defect Status Filter': filters.get('defect_status_filter', 'all'),
        'Tests Included': filters.get('include_tests', True),
        'Defects Included': filters.get('include_defects', True),
    }


if __name__ == "__main__":
    sys.exit(main())