"""
Database configuration and setup for GoNoGo RTM system.

Implements SQLite for development and PostgreSQL for production per ADR-001.
Supports the hybrid GitHub + Database RTM architecture per ADR-003.

Related Issue: US-00052 - Database schema design for traceability relationships
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import os
from typing import Generator

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models.traceability.base import Base

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///./gonogo.db"  # Default to SQLite for development
)

# SQLite-specific configuration for development
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    )
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        DATABASE_URL, echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
    )

# Session configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Metadata for migrations
metadata = MetaData()


def create_tables():
    """Create all database tables. Used for testing and initial setup."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables. Used for testing cleanup."""
    Base.metadata.drop_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session for FastAPI dependency injection.

    Usage in FastAPI routes:
        @app.get("/epics/")
        def get_epics(db: Session = Depends(get_db)):
            return db.query(Epic).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session for use outside of FastAPI dependency injection.
    Remember to close the session when done.

    Usage:
        db = get_db_session()
        try:
            # Database operations
            epic = Epic(epic_id="EP-00001", title="Test Epic")
            db.add(epic)
            db.commit()
        finally:
            db.close()
    """
    return SessionLocal()


# Database health check
def check_database_health() -> dict:
    """Check database connectivity and return health status."""
    try:
        db = get_db_session()
        try:
            # Simple query to test connectivity
            db.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "database_url": (
                    DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
                ),
                "engine": (
                    str(engine.url).split("@")[-1]
                    if "@" in str(engine.url)
                    else str(engine.url)
                ),
            }
        finally:
            db.close()
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_url": (
                DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
            ),
        }
