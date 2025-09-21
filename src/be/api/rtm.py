"""
FastAPI routes for RTM (Requirements Traceability Matrix) operations.

Provides CRUD operations for all traceability entities in the hybrid GitHub + Database architecture.

Related Issue: US-00054 - Database models and migration foundation
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Architecture Decision: ADR-003 - Hybrid GitHub + Database RTM Architecture
"""

import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.traceability import Defect, Epic, GitHubSync, Test, UserStory
from ..services.rtm_report_generator import RTMReportGenerator

router = APIRouter(prefix="/api/rtm", tags=["RTM"])
templates = Jinja2Templates(directory="src/be/templates")


# Dashboard and Web Interface
@router.get("/dashboard", response_class=HTMLResponse)
def rtm_dashboard(request: Request):
    """Serve the RTM Dashboard web interface."""
    return templates.TemplateResponse("rtm_dashboard.html", {"request": request})


# Epic CRUD Operations
@router.post("/epics/", response_model=dict)
def create_epic(
    epic_id: str,
    title: str,
    description: Optional[str] = None,
    business_value: Optional[str] = None,
    priority: str = "medium",
    db: Session = Depends(get_db),
):
    """Create a new Epic."""
    epic = Epic(
        epic_id=epic_id,
        title=title,
        description=description,
        business_value=business_value,
        priority=priority,
    )
    db.add(epic)
    db.commit()
    db.refresh(epic)
    return epic.to_dict()


@router.get("/epics/", response_model=List[dict])
def list_epics(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(50, le=100, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """List all Epics with optional filtering."""
    query = db.query(Epic)

    if status:
        query = query.filter(Epic.status == status)
    if priority:
        query = query.filter(Epic.priority == priority)

    epics = query.offset(offset).limit(limit).all()
    return [epic.to_dict() for epic in epics]


@router.get("/epics/{epic_id}", response_model=dict)
def get_epic(epic_id: str, db: Session = Depends(get_db)):
    """Get an Epic by epic_id."""
    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")
    return epic.to_dict()


@router.put("/epics/{epic_id}", response_model=dict)
def update_epic(
    epic_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    business_value: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Update an Epic."""
    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")

    if title is not None:
        epic.title = title
    if description is not None:
        epic.description = description
    if business_value is not None:
        epic.business_value = business_value
    if priority is not None:
        epic.priority = priority
    if status is not None:
        epic.status = status

    db.commit()
    db.refresh(epic)
    return epic.to_dict()


@router.delete("/epics/{epic_id}")
def delete_epic(epic_id: str, db: Session = Depends(get_db)):
    """Delete an Epic."""
    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")

    db.delete(epic)
    db.commit()
    return {"message": f"Epic {epic_id} deleted successfully"}


# User Story CRUD Operations
@router.post("/user-stories/", response_model=dict)
def create_user_story(
    user_story_id: str,
    epic_id: int,
    github_issue_number: int,
    title: str,
    description: Optional[str] = None,
    story_points: int = 0,
    priority: str = "medium",
    db: Session = Depends(get_db),
):
    """Create a new User Story."""
    user_story = UserStory(
        user_story_id=user_story_id,
        epic_id=epic_id,
        github_issue_number=github_issue_number,
        title=title,
        description=description,
        story_points=story_points,
        priority=priority,
    )
    db.add(user_story)
    db.commit()
    db.refresh(user_story)
    return user_story.to_dict()


@router.get("/user-stories/", response_model=List[dict])
def list_user_stories(
    epic_id: Optional[int] = Query(None, description="Filter by Epic ID"),
    status: Optional[str] = Query(None, description="Filter by implementation status"),
    limit: int = Query(50, le=100, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """List all User Stories with optional filtering."""
    query = db.query(UserStory)

    if epic_id:
        query = query.filter(UserStory.epic_id == epic_id)
    if status:
        query = query.filter(UserStory.implementation_status == status)

    user_stories = query.offset(offset).limit(limit).all()
    return [us.to_dict() for us in user_stories]


@router.get("/user-stories/{user_story_id}", response_model=dict)
def get_user_story(user_story_id: str, db: Session = Depends(get_db)):
    """Get a User Story by user_story_id."""
    user_story = (
        db.query(UserStory).filter(UserStory.user_story_id == user_story_id).first()
    )
    if not user_story:
        raise HTTPException(
            status_code=404, detail=f"User Story {user_story_id} not found"
        )
    return user_story.to_dict()


# Test CRUD Operations
@router.post("/tests/", response_model=dict)
def create_test(
    test_type: str,
    test_file_path: str,
    title: str,
    epic_id: Optional[int] = None,
    test_function_name: Optional[str] = None,
    bdd_scenario_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Create a new Test."""
    test = Test(
        test_type=test_type,
        test_file_path=test_file_path,
        title=title,
        epic_id=epic_id,
        test_function_name=test_function_name,
        bdd_scenario_name=bdd_scenario_name,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return test.to_dict()


@router.get("/tests/", response_model=List[dict])
def list_tests(
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    epic_id: Optional[int] = Query(None, description="Filter by Epic ID"),
    execution_status: Optional[str] = Query(
        None, description="Filter by execution status"
    ),
    limit: int = Query(50, le=100, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """List all Tests with optional filtering."""
    query = db.query(Test)

    if test_type:
        query = query.filter(Test.test_type == test_type)
    if epic_id:
        query = query.filter(Test.epic_id == epic_id)
    if execution_status:
        query = query.filter(Test.last_execution_status == execution_status)

    tests = query.offset(offset).limit(limit).all()
    return [test.to_dict() for test in tests]


@router.put("/tests/{test_id}/execution", response_model=dict)
def update_test_execution(
    test_id: int,
    status: str,
    duration_ms: Optional[float] = None,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Update test execution results."""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail=f"Test {test_id} not found")

    test.update_execution_result(status, duration_ms, error_message)
    db.commit()
    db.refresh(test)
    return test.to_dict()


# Defect CRUD Operations
@router.post("/defects/", response_model=dict)
def create_defect(
    defect_id: str,
    github_issue_number: int,
    title: str,
    severity: str = "medium",
    priority: str = "medium",
    epic_id: Optional[int] = None,
    test_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Create a new Defect."""
    defect = Defect(
        defect_id=defect_id,
        github_issue_number=github_issue_number,
        title=title,
        severity=severity,
        priority=priority,
        epic_id=epic_id,
        test_id=test_id,
    )
    db.add(defect)
    db.commit()
    db.refresh(defect)
    return defect.to_dict()


@router.get("/defects/", response_model=List[dict])
def list_defects(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_security_issue: Optional[bool] = Query(
        None, description="Filter by security issues"
    ),
    limit: int = Query(50, le=100, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """List all Defects with optional filtering."""
    query = db.query(Defect)

    if severity:
        query = query.filter(Defect.severity == severity)
    if status:
        query = query.filter(Defect.status == status)
    if is_security_issue is not None:
        query = query.filter(Defect.is_security_issue == is_security_issue)

    defects = query.offset(offset).limit(limit).all()
    return [defect.to_dict() for defect in defects]


# Analytics and Reporting Endpoints
@router.get("/analytics/epic/{epic_id}/progress", response_model=dict)
def get_epic_progress(epic_id: str, db: Session = Depends(get_db)):
    """Get detailed progress analytics for an Epic."""
    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")

    user_stories = db.query(UserStory).filter(UserStory.epic_id == epic.id).all()
    tests = db.query(Test).filter(Test.epic_id == epic.id).all()
    defects = db.query(Defect).filter(Defect.epic_id == epic.id).all()

    # Calculate progress metrics
    total_story_points = sum(us.story_points for us in user_stories)
    completed_story_points = sum(
        us.story_points
        for us in user_stories
        if us.implementation_status in ["done", "completed"]
    )

    test_pass_rate = 0.0
    if tests:
        passed_tests = sum(
            1 for test in tests if test.last_execution_status == "passed"
        )
        test_pass_rate = (passed_tests / len(tests)) * 100

    critical_defects = sum(1 for defect in defects if defect.severity == "critical")
    open_defects = sum(
        1 for defect in defects if defect.status in ["open", "in_progress"]
    )

    return {
        "epic": epic.to_dict(),
        "metrics": {
            "total_story_points": total_story_points,
            "completed_story_points": completed_story_points,
            "completion_percentage": (
                (completed_story_points / total_story_points * 100)
                if total_story_points > 0
                else 0
            ),
            "user_stories_count": len(user_stories),
            "tests_count": len(tests),
            "test_pass_rate": test_pass_rate,
            "defects_count": len(defects),
            "critical_defects": critical_defects,
            "open_defects": open_defects,
        },
    }


@router.get("/analytics/overview", response_model=dict)
def get_rtm_overview(db: Session = Depends(get_db)):
    """Get overall RTM analytics and metrics."""
    epics = db.query(Epic).all()
    user_stories = db.query(UserStory).all()
    tests = db.query(Test).all()
    defects = db.query(Defect).all()

    # Overall metrics
    total_epics = len(epics)
    completed_epics = sum(1 for epic in epics if epic.status == "completed")

    total_story_points = sum(us.story_points for us in user_stories)
    completed_story_points = sum(
        us.story_points
        for us in user_stories
        if us.implementation_status in ["done", "completed"]
    )

    total_tests = len(tests)
    passed_tests = sum(1 for test in tests if test.last_execution_status == "passed")

    critical_defects = sum(1 for defect in defects if defect.severity == "critical")
    security_issues = sum(1 for defect in defects if defect.is_security_issue)

    return {
        "summary": {
            "epics": {
                "total": total_epics,
                "completed": completed_epics,
                "completion_rate": (
                    (completed_epics / total_epics * 100) if total_epics > 0 else 0
                ),
            },
            "user_stories": {
                "total": len(user_stories),
                "story_points": {
                    "total": total_story_points,
                    "completed": completed_story_points,
                    "completion_rate": (
                        (completed_story_points / total_story_points * 100)
                        if total_story_points > 0
                        else 0
                    ),
                },
            },
            "tests": {
                "total": total_tests,
                "passed": passed_tests,
                "pass_rate": (
                    (passed_tests / total_tests * 100) if total_tests > 0 else 0
                ),
            },
            "defects": {
                "total": len(defects),
                "critical": critical_defects,
                "security_issues": security_issues,
            },
        }
    }


# Dynamic Report Generation Endpoints
@router.get("/reports/matrix", response_model=dict)
def generate_dynamic_rtm_matrix(
    format: str = Query("json", description="Output format: json, markdown, html"),
    epic_filter: Optional[str] = Query(None, description="Filter by epic ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    priority_filter: Optional[str] = Query(None, description="Filter by priority"),
    us_status_filter: Optional[str] = Query(
        "all",
        description="Filter user stories by status: all, planned, in_progress, completed, blocked",
    ),
    test_type_filter: Optional[str] = Query(
        "all", description="Filter tests by type: all, unit, integration, e2e, security"
    ),
    defect_priority_filter: Optional[str] = Query(
        "all",
        description="Filter defects by priority: all, critical, high, medium, low",
    ),
    defect_status_filter: Optional[str] = Query(
        "all",
        description="Filter defects by status: all, open, in_progress, resolved, closed",
    ),
    include_tests: bool = Query(True, description="Include test coverage"),
    include_defects: bool = Query(True, description="Include defect tracking"),
    db: Session = Depends(get_db),
):
    """Generate dynamic RTM matrix with real-time data and Python-based filtering."""
    generator = RTMReportGenerator(db)

    filters = {
        "epic_id": epic_filter,
        "status": status_filter,
        "priority": priority_filter,
        "us_status_filter": us_status_filter,
        "test_type_filter": test_type_filter,
        "defect_priority_filter": defect_priority_filter,
        "defect_status_filter": defect_status_filter,
        "include_tests": include_tests,
        "include_defects": include_defects,
    }

    if format == "html":
        content = generator.generate_html_matrix(filters)
        return HTMLResponse(content=content)
    elif format == "markdown":
        content = generator.generate_markdown_matrix(filters)
        return Response(content=content, media_type="text/markdown")
    else:  # json
        return generator.generate_json_matrix(filters)


@router.get("/reports/epic-progress", response_model=dict)
def generate_epic_progress_report(
    format: str = Query("json", description="Output format: json, html"),
    include_charts: bool = Query(True, description="Include progress charts"),
    db: Session = Depends(get_db),
):
    """Generate comprehensive epic progress report."""
    generator = RTMReportGenerator(db)

    if format == "html":
        content = generator.generate_epic_progress_html(include_charts)
        return HTMLResponse(content=content)
    else:
        return generator.generate_epic_progress_json(include_charts)


@router.get("/reports/test-coverage", response_model=dict)
def generate_test_coverage_report(
    format: str = Query("json", description="Output format: json, html"),
    epic_id: Optional[str] = Query(None, description="Filter by epic ID"),
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    db: Session = Depends(get_db),
):
    """Generate test coverage and execution report."""
    generator = RTMReportGenerator(db)

    filters = {
        "epic_id": epic_id,
        "test_type": test_type,
    }

    if format == "html":
        content = generator.generate_test_coverage_html(filters)
        return HTMLResponse(content=content)
    else:
        return generator.generate_test_coverage_json(filters)


@router.get("/reports/defect-analysis", response_model=dict)
def generate_defect_analysis_report(
    format: str = Query("json", description="Output format: json, html"),
    severity_filter: Optional[str] = Query(None, description="Filter by severity"),
    days_back: int = Query(30, description="Days to look back for trends"),
    db: Session = Depends(get_db),
):
    """Generate defect analysis and trend report."""
    generator = RTMReportGenerator(db)

    filters = {
        "severity": severity_filter,
        "days_back": days_back,
    }

    if format == "html":
        content = generator.generate_defect_analysis_html(filters)
        return HTMLResponse(content=content)
    else:
        return generator.generate_defect_analysis_json(filters)


@router.get("/reports/dashboard-data", response_model=dict)
def get_dashboard_data(db: Session = Depends(get_db)):
    """Get real-time data for RTM dashboard widgets."""
    # Epic status distribution
    epic_status_query = (
        db.query(Epic.status, func.count(Epic.id).label("count"))
        .group_by(Epic.status)
        .all()
    )

    epic_status = {status: count for status, count in epic_status_query}

    # User story progress
    us_status_query = (
        db.query(
            UserStory.implementation_status, func.count(UserStory.id).label("count")
        )
        .group_by(UserStory.implementation_status)
        .all()
    )

    us_status = {status: count for status, count in us_status_query}

    # Test execution summary
    test_status_query = (
        db.query(Test.last_execution_status, func.count(Test.id).label("count"))
        .group_by(Test.last_execution_status)
        .all()
    )

    test_status = {status: count for status, count in test_status_query}

    # Defect severity distribution
    defect_severity_query = (
        db.query(Defect.severity, func.count(Defect.id).label("count"))
        .group_by(Defect.severity)
        .all()
    )

    defect_severity = {severity: count for severity, count in defect_severity_query}

    # Recent activity (last 7 days)
    from datetime import datetime, timedelta

    recent_date = datetime.utcnow() - timedelta(days=7)

    recent_tests = (
        db.query(Test).filter(Test.last_execution_timestamp >= recent_date).count()
    )

    recent_defects = db.query(Defect).filter(Defect.created_at >= recent_date).count()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "epic_status": epic_status,
        "user_story_status": us_status,
        "test_execution": test_status,
        "defect_severity": defect_severity,
        "recent_activity": {
            "test_executions": recent_tests,
            "new_defects": recent_defects,
        },
        "summary": {
            "total_epics": db.query(Epic).count(),
            "total_user_stories": db.query(UserStory).count(),
            "total_tests": db.query(Test).count(),
            "total_defects": db.query(Defect).count(),
        },
    }


@router.get("/reports/export/{report_type}")
def export_report(
    report_type: str,
    format: str = Query("pdf", description="Export format: pdf, csv, xlsx"),
    db: Session = Depends(get_db),
):
    """Export reports in various formats for external use."""
    generator = RTMReportGenerator(db)

    if report_type == "full-matrix":
        content, media_type, filename = generator.export_full_matrix(format)
    elif report_type == "epic-progress":
        content, media_type, filename = generator.export_epic_progress(format)
    elif report_type == "test-summary":
        content, media_type, filename = generator.export_test_summary(format)
    else:
        raise HTTPException(
            status_code=400, detail=f"Unknown report type: {report_type}"
        )

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
