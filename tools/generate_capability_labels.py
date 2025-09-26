#!/usr/bin/env python3
"""Capability label helper for epics.

Generates the GitHub label names needed to keep epics aligned with their
strategic capabilities.

Related Task: US-00062 - Strategic Capability Grouping for Epics
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import argparse
import sys
from pathlib import Path
from typing import List

# Add src to Python path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    from be.database import get_db_session
    from be.models.traceability import Capability, Epic
except ImportError as exc:  # pragma: no cover - handled in CLI diagnostics
    print(f"Failed to import database modules: {exc}")
    sys.exit(1)

from tools.capability_mapping import (
    CAPABILITY_CATALOG,
    EPIC_TO_CAPABILITY_MAP,
    capability_label_name,
)


def ensure_capability_record(session, capability_id: str) -> Capability:
    """Ensure a Capability record exists for the given identifier."""

    capability = (
        session.query(Capability)
        .filter(Capability.capability_id == capability_id)
        .first()
    )
    if capability:
        return capability

    catalog_entry = CAPABILITY_CATALOG.get(capability_id)
    capability = Capability(
        capability_id=capability_id,
        name=catalog_entry.name if catalog_entry else capability_id,
        description=(catalog_entry.description if catalog_entry else capability_id),
    )
    session.add(capability)
    session.flush()
    return capability


def format_summary(epic: Epic, capability: Capability, label: str, add_command: bool, status: str) -> List[str]:
    """Build display lines for a single epic."""

    header = f"{epic.epic_id} -> {capability.capability_id} ({capability.name})"
    lines = [header, f"  DB capability: {status}"]

    if epic.github_issue_number:
        lines.append(f"  GitHub issue: #{epic.github_issue_number}")
        if add_command:
            lines.append(
                f"  Command: gh issue edit {epic.github_issue_number} --add-label \"{label}\""
            )
    else:
        lines.append("  GitHub issue: <missing number>")

    lines.append(f"  Suggested label: {label}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Suggest capability labels for epics to keep RTM in sync"
    )
    parser.add_argument(
        "--print-gh",
        action="store_true",
        help="Also print gh issue edit commands for quick copy/paste",
    )
    args = parser.parse_args()

    session = get_db_session()

    try:
        epics = (
            session.query(Epic)
            .order_by(Epic.epic_id)
            .all()
        )

        if not epics:
            print("No epics found in the database.")
            return 0

        for epic in epics:
            desired_capability_id = EPIC_TO_CAPABILITY_MAP.get(epic.epic_id)
            if not desired_capability_id:
                continue

            capability = ensure_capability_record(session, desired_capability_id)
            label = capability_label_name(desired_capability_id)

            db_state = "OK"
            if epic.capability_id != capability.id:
                epic.capability_id = capability.id
                session.flush()
                db_state = "UPDATED"

            for line in format_summary(epic, capability, label, args.print_gh, db_state):
                print(line)
            print()

        session.commit()
    finally:
        session.close()

    print("Next step: add any missing labels above, then run the sync manager to persist them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
