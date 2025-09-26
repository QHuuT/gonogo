"""Generate persona snapshot data from the curated demo dataset.

Run with:  python tools/demo/prepare_dashboard_demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.be.api.rtm import calculate_dashboard_summary

DEMO_INPUT = ROOT / "tests" / "demo" / "multipersona_dashboard_demo.json"
OUTPUT_PATH = ROOT / "tools" / "demo" / "dashboard_persona_snapshot.json"

PERSONAS = ("PM", "PO", "QA")


def load_demo_dataset() -> dict:
    with DEMO_INPUT.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_snapshot(epics: list[dict]) -> dict:
    snapshot = {}
    for persona in PERSONAS:
        summary = calculate_dashboard_summary(epics, persona)
        snapshot[persona] = {
            "persona": persona,
            "summary": summary,
            "epic_count": len(epics),
        }
    snapshot["epics"] = epics
    return snapshot


def main() -> None:
    dataset = load_demo_dataset()
    epics = dataset["epics"]
    snapshot = build_snapshot(epics)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Demo snapshot written to {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
