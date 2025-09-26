
"""
Metric threshold utilities for persona dashboards.

Loads configurable warning/danger thresholds from JSON so metric evaluation can
be tuned without touching application code.

Related Issue: US-00071 - Extend Epic model for metrics
Parent Epic: EP-00010 - Multi-persona dashboard
"""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

DEFAULT_THRESHOLDS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "epic": {
        "schedule_variance_days": {"warning": 2, "danger": 7, "direction": "high"},
        "success_probability": {"warning": 70, "danger": 50, "direction": "low"},
        "test_coverage_percentage": {"warning": 75, "danger": 60, "direction": "low"},
        "defect_density": {"warning": 0.4, "danger": 0.7, "direction": "high"},
    },
    "pm": {
        "scope_creep_percentage": {"warning": 15, "danger": 25, "direction": "high"},
        "average_velocity_per_member": {"warning": 6, "danger": 4, "direction": "low"},
        "overall_risk_score": {"warning": 30, "danger": 50, "direction": "high"},
        "average_schedule_variance": {"warning": 2, "danger": 7, "direction": "high"},
        "risk_percentage": {"warning": 25, "danger": 50, "direction": "high"},
        "average_success_probability": {"warning": 70, "danger": 50, "direction": "low"},
    },
    "po": {
        "average_scope_creep_percentage": {"warning": 15, "danger": 25, "direction": "high"},
        "average_adoption": {"warning": 60, "danger": 40, "direction": "low"},
        "average_satisfaction": {"warning": 7, "danger": 5, "direction": "low"},
    },
    "qa": {
        "average_test_coverage": {"warning": 75, "danger": 60, "direction": "low"},
        "average_defect_density": {"warning": 0.4, "danger": 0.7, "direction": "high"},
        "average_technical_debt": {"warning": 60, "danger": 120, "direction": "high"},
    },
}

CONFIG_PATH = Path(os.getenv("METRIC_THRESHOLDS_PATH", "config/metrics_thresholds.json"))


class MetricThresholdService:
    """Evaluate metric values against configured thresholds."""

    def __init__(self, config: Dict[str, Dict[str, Dict[str, Any]]]):
        self.config = config or {}

    def evaluate(self, scope: str, metric_key: str, value: Any) -> str:
        """Return ok/warning/danger/unknown based on configured thresholds."""
        scope_config = self.config.get(scope, {})
        metric_config = scope_config.get(metric_key)
        if metric_config is None:
            return "ok"

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return "unknown"

        warning = metric_config.get("warning")
        danger = metric_config.get("danger")
        direction = metric_config.get("direction", "high")

        if direction == "low":
            if danger is not None and numeric_value <= danger:
                return "danger"
            if warning is not None and numeric_value <= warning:
                return "warning"
        else:  # direction == "high"
            if danger is not None and numeric_value >= danger:
                return "danger"
            if warning is not None and numeric_value >= warning:
                return "warning"

        return "ok"


@lru_cache(maxsize=1)
def _load_threshold_config() -> Dict[str, Dict[str, Dict[str, Any]]]:
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_THRESHOLDS


@lru_cache(maxsize=1)
def get_threshold_service() -> MetricThresholdService:
    """Return a cached threshold evaluation service."""
    return MetricThresholdService(_load_threshold_config())
