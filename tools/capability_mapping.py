"""
Canonical mapping between Epics and Capabilities.

This helps keep the RTM database, GitHub labels, and documentation aligned.

Related Task: US-00062 - Strategic Capability Grouping for Epics
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class CapabilityInfo:
    """Metadata for a capability."""

    capability_id: str
    name: str
    color: str  # Hex color (without leading #)
    description: str


# Strategic capabilities currently defined for GoNoGo
CAPABILITY_CATALOG: Dict[str, CapabilityInfo] = {
    "CAP-00001": CapabilityInfo(
        capability_id="CAP-00001",
        name="GitHub Integration",
        color="8e44ad",
        description="Automations and integrations with GitHub workflows",
    ),
    "CAP-00002": CapabilityInfo(
        capability_id="CAP-00002",
        name="Requirements Traceability",
        color="16a085",
        description="Traceability matrix, dashboards, and portfolio visibility",
    ),
    "CAP-00003": CapabilityInfo(
        capability_id="CAP-00003",
        name="Blog Platform",
        color="e67e22",
        description="Blog content experience and supporting platform capabilities",
    ),
    "CAP-00004": CapabilityInfo(
        capability_id="CAP-00004",
        name="GDPR Compliance",
        color="c0392b",
        description="Privacy, consent, and regulatory compliance capabilities",
    ),
}


# Default capability assignment for each Epic when GitHub label data is missing.
# These defaults mirror the original strategic mapping maintained in Notion/RTM.
EPIC_TO_CAPABILITY_MAP: Dict[str, str] = {
    "EP-00001": "CAP-00003",  # Blog Content Management -> Blog Platform
    "EP-00002": "CAP-00004",  # GDPR-Compliant Comment System -> GDPR Compliance
    "EP-00003": "CAP-00004",  # Privacy and Consent Management -> GDPR Compliance
    "EP-00004": "CAP-00001",  # GitHub Workflow Integration -> GitHub Integration
    "EP-00005": "CAP-00002",  # RTM Automation -> Requirements Traceability
    "EP-00006": "CAP-00001",  # GitHub Project Management Integration -> GitHub Integration
    "EP-00007": "CAP-00002",  # Test logging and reporting -> Supports RTM capabilities
    "EP-00010": "CAP-00002",  # Multi-persona dashboard -> Requirements Traceability
}


def capability_label_name(capability_id: str) -> str:
    """Return the GitHub label string for a capability."""

    return f"capability/{capability_id}"


__all__ = [
    "CapabilityInfo",
    "CAPABILITY_CATALOG",
    "EPIC_TO_CAPABILITY_MAP",
    "capability_label_name",
]
