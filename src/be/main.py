"""
FastAPI application entry point for GoNoGo blog.
GDPR-compliant blog with comment system.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="GoNoGo Blog",
    description="GDPR-compliant blog with comment system",
    version="0.1.0",
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="src/be/templates")


@app.get("/")
async def home():
    """Home page route."""
    return {"message": "GoNoGo Blog - Coming Soon"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "gonogo-blog"}
