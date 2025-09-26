"""
FastAPI application entry point for GoNoGo blog.
GDPR-compliant blog with comment system and RTM database.
"""

import asyncio
from contextlib import asynccontextmanager, suppress

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan event handler for startup and shutdown tasks.

    Replaces the deprecated @app.on_event() decorators with the new
    lifespan context manager approach recommended by FastAPI.
    """
    # Startup
    if should_enable_background_refresh():
        interval = get_refresh_interval()
        app.state.metric_refresh_task = asyncio.create_task(metrics_refresh_loop(interval))

    yield

    # Shutdown
    if should_enable_background_refresh():
        task = getattr(app.state, "metric_refresh_task", None)
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(
    title="GoNoGo Blog & RTM System",
    description="GDPR-compliant blog with Requirements Traceability Matrix database",
    version="0.1.0",
    lifespan=lifespan,
)

# Include API routes
app.include_router(rtm_router)
app.include_router(epic_dependencies_router)
app.include_router(capabilities_router)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="src/be/templates")


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
