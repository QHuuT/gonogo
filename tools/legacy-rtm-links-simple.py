#!/usr/bin/env python3
"""
Enhanced RTM Links CLI Tool with Database Support

Command-line interface for RTM link generation and validation.
Now supports both file-based and database-backed RTM operations.

Related Issues:
- US-00015 - Automated RTM link generation and validation
- US-00058 - Legacy script migration and deprecation
Epic: EP-00005 - RTM Automation
"""

import os
import sys
from pathlib import Path

# Add src to Python path to import our modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from shared.utils.rtm_hybrid_generator import (
        HybridRTMLinkGenerator as RTMLinkGenerator,
    )

    HYBRID_MODE_AVAILABLE = True
except ImportError:
    # Fallback to original generator if hybrid not available
    from shared.utils.rtm_link_generator import RTMLinkGenerator

    HYBRID_MODE_AVAILABLE = False


def main():
    """Enhanced CLI entry point with hybrid mode support."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced RTM Link Tool with Database Support"
    )
    parser.add_argument("--validate", action="store_true", help="Validate RTM links")
    parser.add_argument(
        "--update", action="store_true", help="Update RTM links (dry run)"
    )
    parser.add_argument(
        "--rtm-file",
        default="docs/traceability/requirements-matrix.md",
        help="RTM file path",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "file", "database"],
        default="auto",
        help="RTM operation mode (auto=detect best, file=file-based, database=database-backed)",
    )
    parser.add_argument(
        "--info", action="store_true", help="Show RTM system information and exit"
    )
    parser.add_argument(
        "--export-db",
        action="store_true",
        help="Export database RTM to file (if database available)",
    )

    args = parser.parse_args()

    # Initialize generator
    try:
        if HYBRID_MODE_AVAILABLE:
            generator = RTMLinkGenerator(mode=args.mode)
            print("Enhanced RTM Generator initialized (hybrid mode available)")
        else:
            generator = RTMLinkGenerator()
            print("RTM Generator initialized (file mode only)")

        print(f"GitHub: {generator.github_owner}/{generator.github_repo}")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    # Show system information if requested
    if args.info:
        if HYBRID_MODE_AVAILABLE:
            mode_info = generator.get_mode_info()
            print("System Information:")
            print(f"  Requested mode: {mode_info['requested_mode']}")
            print(f"  Effective mode: {mode_info['effective_mode']}")
            print(f"  Database available: {mode_info['database_available']}")
            print(f"  Fallback enabled: {mode_info['fallback_enabled']}")
            print(f"  Prefer database: {mode_info['prefer_database']}")
        else:
            print("System Information:")
            print("  Mode: file-based only (hybrid mode not available)")
        return 0

    # Export database to file if requested
    if args.export_db:
        if HYBRID_MODE_AVAILABLE and hasattr(generator, "export_database_to_rtm_file"):
            print(f"Exporting database RTM to {args.rtm_file}...")
            success = generator.export_database_to_rtm_file(args.rtm_file)
            if success:
                print(f"Successfully exported database RTM to {args.rtm_file}")
            else:
                print("Export failed - database may not be available")
                return 1
        else:
            print("Database export not available (database mode not supported)")
            return 1
        return 0

    if args.validate:
        # Show mode information for validation
        if HYBRID_MODE_AVAILABLE:
            mode_info = generator.get_mode_info()
            print(f"RTM Validation - Mode: {mode_info['effective_mode']}")
            if mode_info["effective_mode"] == "database":
                print("Using database as source of truth")
            else:
                print(f"Validating file: {args.rtm_file}")
        else:
            print(f"Validating {args.rtm_file}...")

        # Check file existence for file mode
        if not HYBRID_MODE_AVAILABLE or (
            hasattr(generator, "get_mode_info")
            and generator.get_mode_info()["effective_mode"] == "file"
        ):
            if not os.path.exists(args.rtm_file):
                print(f"Error: File not found: {args.rtm_file}")
                return 1

        try:
            result = generator.validate_rtm_links(args.rtm_file)

            # Enhanced output with mode context
            print("\nRTM Link Validation Report")
            print("=" * 30)
            print(f"Total Links: {result.total_links}")
            print(f"Valid Links: {result.valid_links}")
            print(f"Invalid Links: {len(result.invalid_links)}")

            if result.total_links > 0:
                health = (result.valid_links / result.total_links) * 100
                print(f"Health Score: {health:.1f}%")

            # Show warnings (mode information)
            if result.warnings:
                print("\nInformation:")
                for warning in result.warnings:
                    print(f"  - {warning}")

            # Show errors if any
            if result.errors:
                print("\nErrors:")
                for error in result.errors:
                    print(f"  - {error}")

            # Show invalid links
            if result.invalid_links:
                print("\nInvalid Links:")
                for link in result.invalid_links[:10]:  # Show first 10
                    print(
                        f"  - {link.text}: {link.error_message or 'Link validation failed'}"
                    )
                if len(result.invalid_links) > 10:
                    print(f"  ... and {len(result.invalid_links) - 10} more")

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


if __name__ == "__main__":
    sys.exit(main())
