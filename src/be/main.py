"""
FastAPI application entry point for GoNoGo blog.
GDPR-compliant blog with comment system and RTM database.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .api.rtm import router as rtm_router
from .database import check_database_health

app = FastAPI(
    title="GoNoGo Blog & RTM System",
    description="GDPR-compliant blog with Requirements Traceability Matrix database",
    version="0.1.0",
)

# Include API routes
app.include_router(rtm_router)

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
