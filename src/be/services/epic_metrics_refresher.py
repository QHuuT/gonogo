"""
Utility helpers for refreshing Epic metrics in batch.

Provides both a synchronous refresh helper (used by CLI tools) and an async
loop that can be scheduled by the FastAPI app for background updates.

Related Issue: US-00071 - Extend Epic model for metrics
Parent Epic: EP-00010 - Multi-persona dashboard
"""

import asyncio
import os

from ..database import get_db_session
from ..models.traceability.epic import Epic


def refresh_all_epic_metrics(
    session=None, force: bool = False, record_history: bool = True
) -> int:
    """Recalculate metrics for every Epic and return the number refreshed."""
    created_session = False
    if session is None:
        session = get_db_session()
        created_session = True

    refreshed = 0
    try:
        for epic in session.query(Epic).yield_per(50):
            if force or epic.is_metrics_cache_stale():
                epic.update_metrics(
    force_recalculate=True,
    session=session,
    record_history=record_history,
    
)
                refreshed += 1
        if created_session:
            session.commit()
    finally:
        if created_session:
            session.close()
    return refreshed


async def metrics_refresh_loop(interval_seconds: int = 900) -> None:
    """Background loop that periodically refreshes Epic metrics."""
    while True:
        session = get_db_session()
        try:
            refresh_all_epic_metrics(
                session=session, force=False, record_history=True
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        await asyncio.sleep(interval_seconds)


def should_enable_background_refresh() -> bool:
    """Return True if the background refresh loop should run."""
    return os.getenv("ENABLE_METRIC_REFRESH", "true").lower() not in {
        "0",
        "false",
        "no",
    }


def get_refresh_interval() -> int:
    """Return the configured refresh interval in seconds (default 15
    minutes).
    """
    try:
        return int(os.getenv("METRIC_REFRESH_INTERVAL_SECONDS", "900"))
    except ValueError:
        return 900
