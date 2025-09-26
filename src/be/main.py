"""
FastAPI application entry point for GoNoGo blog.
GDPR-compliant blog with comment system and RTM database.
"""

import asyncio
from contextlib import suppress

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .api.rtm import router as rtm_router
from .api.epic_dependencies import router as epic_dependencies_router
from .api.capabilities import router as capabilities_router
from .database import check_database_health
from .services.epic_metrics_refresher import (
    get_refresh_interval,
    metrics_refresh_loop,
    should_enable_background_refresh,
)

app = FastAPI(
    title="GoNoGo Blog & RTM System",
    description="GDPR-compliant blog with Requirements Traceability Matrix database",
    version="0.1.0",
)

# Include API routes
app.include_router(rtm_router)
app.include_router(epic_dependencies_router)
app.include_router(capabilities_router)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="src/be/templates")


if should_enable_background_refresh():

    @app.on_event("startup")
    async def start_metric_refresh_loop():
        """Kick off the periodic metric refresh background task."""
        interval = get_refresh_interval()
        app.state.metric_refresh_task = asyncio.create_task(metrics_refresh_loop(interval))

    @app.on_event("shutdown")
    async def stop_metric_refresh_loop():
        """Ensure the background task is cleaned up on shutdown."""
        task = getattr(app.state, "metric_refresh_task", None)
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


@app.get("/")
async def home():
    """Home page route."""
    return {"message": "GoNoGo Blog & RTM System - Ready"}


@app.get("/health")
async def health_check():
    """Health check endpoint with database status."""
    db_health = check_database_health()
    return {"status": "healthy", "service": "gonogo-blog-rtm", "database": db_health}

# Force reload 1758799468.9461117

# Template refresh 1758799613.5726986
