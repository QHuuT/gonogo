#!/usr/bin/env python3
"""
CLI helper to refresh cached epic metrics and append history snapshots.

Usage:
    python tools/update_epic_metrics.py [--force] [--no-history]

Related Issue: US-00071 - Extend Epic model for metrics
Parent Epic: EP-00010 - Multi-persona dashboard
"""

import argparse

from src.be.services.epic_metrics_refresher import refresh_all_epic_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh cached epic metrics")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recalculation even if the cache is fresh",
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Do not append snapshots to the metric history table",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    refreshed = refresh_all_epic_metrics(
        force=args.force, record_history=not args.no_history
    )
    print(f"Refreshed metrics for {refreshed} epic(s)")


if __name__ == "__main__":
    main()
