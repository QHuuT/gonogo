"""
FastAPI routes for RTM (Requirements Traceability Matrix) operations.

Provides CRUD operations for all traceability entities in the hybrid GitHub +
Database architecture.

Related Issue: US-00054 - Database models and migration foundation
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Architecture Decision: ADR-003 - Hybrid GitHub + Database RTM Architecture
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.traceability import Defect, Epic, Test, UserStory
from ..services.rtm_report_generator import RTMReportGenerator
from ...shared.metrics.thresholds import get_threshold_service

router = APIRouter(prefix="/api/rtm", tags=["RTM"])
templates = Jinja2Templates(directory="src/be/templates")

DEMO_DATASET_PATH = Path(__file__).resolve().parents[3] / "tests" / "demo" / "multipersona_dashboard_demo.json"


def load_demo_dataset() -> dict:
    """Load curated demo dashboard data."""
    if not DEMO_DATASET_PATH.exists():
        raise HTTPException(status_code=500, detail="Demo dataset not available")
    with DEMO_DATASET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def filter_demo_epics(
    epics: List[dict], epic_filter: Optional[str], status_filter: Optional[str], component_filter: Optional[str]
) -> List[dict]:
    """Apply basic filtering logic to the demo epics collection."""
    filtered = epics

    if epic_filter:
        filtered = [epic for epic in filtered if epic.get("epic_id") == epic_filter]

    if status_filter:
        status_lower = status_filter.lower()
        filtered = [epic for epic in filtered if str(epic.get("status", "")).lower() == status_lower]

    if component_filter:
        components = [component.strip().lower() for component in component_filter.split(",") if component.strip()]
        if components:
            filtered = [epic for epic in filtered if str(epic.get("component", "")).lower() in components]

    return filtered


# Dashboard and Web Interface
@router.get("/dashboard", response_class=HTMLResponse)
def rtm_dashboard(request: Request):
    """Serve the RTM Dashboard web interface."""
    return templates.TemplateResponse("rtm_dashboard.html", {"request": request})


@router.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request):
    """Dashboard home page with navigation to different dashboards."""
    return templates.TemplateResponse("multipersona_dashboard.html", {"request": request})


@router.get("/dashboard/multipersona", response_class=HTMLResponse)
def multipersona_dashboard(request: Request):
    """Serve the Multi-Persona Dashboard web interface (US-00072)."""
    return templates.TemplateResponse("multipersona_dashboard.html", {"request": request})


@router.get("/dashboard/multipersona/demo", response_class=HTMLResponse)
def multipersona_dashboard_demo(request: Request):
    """Serve the Multi-Persona Dashboard in demo mode (uses curated data)."""
    return templates.TemplateResponse("multipersona_dashboard.html", {"request": request})


@router.get("/dashboard/dependencies", response_class=HTMLResponse)
def dependency_visualizer(request: Request):
    """Serve the Epic Dependencies Visualizer web interface with D3.js
    (US-00030)."""
    return templates.TemplateResponse("dependency_visualizer.html", {"request": request})


@router.get("/dashboard/capabilities", response_class=HTMLResponse)
def capability_portfolio_dashboard(request: Request):
    """Serve the Capability Portfolio Dashboard web interface (US-00063)."""
    return templates.TemplateResponse("capability_portfolio.html", {"request": request})


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
    component: Optional[str] = Query(None, description="Filter by component (supports comma-separated values)"),
    exclude_component: Optional[str] = Query(None, description="Exclude components (supports comma-separated values)"),
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

    # Component filtering
    if component:
        components = [c.strip() for c in component.split(",")]
        # For epics, component can contain multiple values separated by comma
        # So we need to check if ANY of the requested components are in the
        # epic's component field
        component_filters = []
        for comp in components:
            component_filters.append(Epic.component.like(f"%{comp}%"))
        query = query.filter(or_(*component_filters))

    if exclude_component:
        exclude_components = [c.strip() for c in exclude_component.split(",")]
        for comp in exclude_components:
            query = query.filter(~Epic.component.like(f"%{comp}%"))

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
    component: Optional[str] = Query(None, description="Filter by component (supports comma-separated values)"),
    exclude_component: Optional[str] = Query(None, description="Exclude components (supports comma-separated values)"),
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

    # Component filtering
    if component:
        components = [c.strip() for c in component.split(",")]
        # For user stories, component is a single value field
        query = query.filter(UserStory.component.in_(components))

    if exclude_component:
        exclude_components = [c.strip() for c in exclude_component.split(",")]
        query = query.filter(~UserStory.component.in_(exclude_components))

    user_stories = query.offset(offset).limit(limit).all()
    return [us.to_dict() for us in user_stories]


@router.get("/user-stories/{user_story_id}", response_model=dict)
def get_user_story(user_story_id: str, db: Session = Depends(get_db)):
    """Get a User Story by user_story_id."""
    user_story = db.query(UserStory).filter(UserStory.user_story_id == user_story_id).first()
    if not user_story:
        raise HTTPException(status_code=404, detail=f"User Story {user_story_id} not found")
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
    execution_status: Optional[str] = Query(None, description="Filter by execution status"),
    component: Optional[str] = Query(None, description="Filter by component (supports comma-separated values)"),
    exclude_component: Optional[str] = Query(None, description="Exclude components (supports comma-separated values)"),
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

    # Component filtering
    if component:
        components = [c.strip() for c in component.split(",")]
        query = query.filter(Test.component.in_(components))

    if exclude_component:
        exclude_components = [c.strip() for c in exclude_component.split(",")]
        query = query.filter(~Test.component.in_(exclude_components))

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
    is_security_issue: Optional[bool] = Query(None, description="Filter by security issues"),
    component: Optional[str] = Query(None, description="Filter by component (supports comma-separated values)"),
    exclude_component: Optional[str] = Query(None, description="Exclude components (supports comma-separated values)"),
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

    # Component filtering
    if component:
        components = [c.strip() for c in component.split(",")]
        query = query.filter(Defect.component.in_(components))

    if exclude_component:
        exclude_components = [c.strip() for c in exclude_component.split(",")]
        query = query.filter(~Defect.component.in_(exclude_components))

    defects = query.offset(offset).limit(limit).all()
    return [defect.to_dict() for defect in defects]


# Component Analysis Endpoints
@router.get("/components/", response_model=List[str])
def list_components(db: Session = Depends(get_db)):
    """Get list of all unique components across all entities."""
    epic_components = db.query(Epic.component).filter(Epic.component.isnot(None)).distinct().all()
    us_components = db.query(UserStory.component).filter(UserStory.component.isnot(None)).distinct().all()
    test_components = db.query(Test.component).filter(Test.component.isnot(None)).distinct().all()
    defect_components = db.query(Defect.component).filter(Defect.component.isnot(None)).distinct().all()

    # Flatten epic components (they can be comma-separated)
    all_components = set()
    for (comp,) in epic_components:
        if comp:
            all_components.update([c.strip() for c in comp.split(",")])

    # Add single-value components
    for (comp,) in us_components + test_components + defect_components:
        if comp:
            all_components.add(comp.strip())

    return sorted(list(all_components))


@router.get("/components/statistics", response_model=dict)
def get_component_statistics(db: Session = Depends(get_db)):
    """Get comprehensive statistics for each component."""
    components = list_components(db)

    stats = {}
    for component in components:
        # Epic count (need to check for component in comma-separated values)
        epic_count = db.query(Epic).filter(Epic.component.like(f"%{component}%")).count()

        # User story count
        us_count = db.query(UserStory).filter(UserStory.component == component).count()

        # Test count
        test_count = db.query(Test).filter(Test.component == component).count()

        # Defect count
        defect_count = db.query(Defect).filter(Defect.component == component).count()

        # Test pass rate for this component
        total_tests = db.query(Test).filter(Test.component == component).count()
        passed_tests = (
            db.query(Test).filter(Test.component == component, Test.last_execution_status == "passed").count()
        )
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Critical defects for this component
        critical_defects = db.query(Defect).filter(Defect.component == component, Defect.severity == "critical").count()

        stats[component] = {
            "epic_count": epic_count,
            "user_story_count": us_count,
            "test_count": test_count,
            "defect_count": defect_count,
            "test_pass_rate": round(pass_rate, 2),
            "critical_defects": critical_defects,
            "total_items": (epic_count + us_count + test_count + defect_count),
        }

    return {
        "components": stats,
        "summary": {
            "total_components": len(components),
            "total_epics": sum(stat["epic_count"] for stat in stats.values()),
            "total_user_stories": sum(stat["user_story_count"] for stat in stats.values()),
            "total_tests": sum(stat["test_count"] for stat in stats.values()),
            "total_defects": sum(stat["defect_count"] for stat in stats.values()),
        },
    }


@router.get("/components/{component_name}/items", response_model=dict)
def get_component_items(
    component_name: str,
    include_epics: bool = Query(True, description="Include epics with this component"),
    include_user_stories: bool = Query(True, description="Include user stories with this component"),
    include_tests: bool = Query(True, description="Include tests with this component"),
    include_defects: bool = Query(True, description="Include defects with this component"),
    limit: int = Query(50, le=100, description="Limit results per entity type"),
    db: Session = Depends(get_db),
):
    """Get all items (epics, user stories, tests, defects) for a
    specific component."""
    result = {"component": component_name, "epics": [], "user_stories": [], "tests": [], "defects": []}

    if include_epics:
        epics = db.query(Epic).filter(Epic.component.like(f"%{component_name}%")).limit(limit).all()
        result["epics"] = [epic.to_dict() for epic in epics]

    if include_user_stories:
        user_stories = db.query(UserStory).filter(UserStory.component == component_name).limit(limit).all()
        result["user_stories"] = [us.to_dict() for us in user_stories]

    if include_tests:
        tests = db.query(Test).filter(Test.component == component_name).limit(limit).all()
        result["tests"] = [test.to_dict() for test in tests]

    if include_defects:
        defects = db.query(Defect).filter(Defect.component == component_name).limit(limit).all()
        result["defects"] = [defect.to_dict() for defect in defects]

    return result


@router.get("/components/distribution", response_model=dict)
def get_component_distribution(db: Session = Depends(get_db)):
    """Get component distribution analytics."""
    stats = get_component_statistics(db)
    components_data = stats["components"]

    # Sort components by total items
    sorted_components = sorted(components_data.items(), key=lambda x: x[1]["total_items"], reverse=True)

    # Calculate percentages
    total_items = sum(data["total_items"] for data in components_data.values())

    distribution = []
    for component, data in sorted_components:
        percentage = (data["total_items"] / total_items * 100) if total_items > 0 else 0
        distribution.append(
            {
                "component": component,
                "count": data["total_items"],
                "percentage": round(percentage, 2),
                "breakdown": {
                    "epics": data["epic_count"],
                    "user_stories": data["user_story_count"],
                    "tests": data["test_count"],
                    "defects": data["defect_count"],
                },
            }
        )

    return {"distribution": distribution, "total_items": total_items, "total_components": len(components_data)}


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
        us.story_points for us in user_stories if us.implementation_status in ["done", "completed"]
    )

    test_pass_rate = 0.0
    if tests:
        passed_tests = sum(1 for test in tests if test.last_execution_status == "passed")
        test_pass_rate = (passed_tests / len(tests)) * 100

    critical_defects = sum(1 for defect in defects if defect.severity == "critical")
    open_defects = sum(1 for defect in defects if defect.status in ["open", "in_progress"])

    return {
        "epic": epic.to_dict(),
        "metrics": {
            "total_story_points": total_story_points,
            "completed_story_points": completed_story_points,
            "completion_percentage": (
                (completed_story_points / total_story_points * 100) if total_story_points > 0 else 0
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
        us.story_points for us in user_stories if us.implementation_status in ["done", "completed"]
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
                "completion_rate": ((completed_epics / total_epics * 100) if total_epics > 0 else 0),
            },
            "user_stories": {
                "total": len(user_stories),
                "story_points": {
                    "total": total_story_points,
                    "completed": completed_story_points,
                    "completion_rate": (
                        (completed_story_points / total_story_points * 100) if total_story_points > 0 else 0
                    ),
                },
            },
            "tests": {
                "total": total_tests,
                "passed": passed_tests,
                "pass_rate": ((passed_tests / total_tests * 100) if total_tests > 0 else 0),
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
        description=("Filter user stories by status: all, planned, in_progress, completed, blocked"),
    ),
    test_type_filter: Optional[str] = Query(
        "all", description=("Filter tests by type: all, unit, integration, e2e, security")
    ),
    defect_priority_filter: Optional[str] = Query(
        "all",
        description=("Filter defects by priority: all, critical, high, medium, low"),
    ),
    defect_status_filter: Optional[str] = Query(
        "all",
        description=("Filter defects by status: all, open, in_progress, resolved, closed"),
    ),
    include_tests: bool = Query(True, description="Include test coverage"),
    include_defects: bool = Query(True, description="Include defect tracking"),
    db: Session = Depends(get_db),
):
    """Generate dynamic RTM matrix with real-time data and
    Python-based filtering."""
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
    epic_status_query = db.query(Epic.status, func.count(Epic.id).label("count")).group_by(Epic.status).all()

    epic_status = {status: count for status, count in epic_status_query}

    # User story progress
    us_status_query = (
        db.query(UserStory.implementation_status, func.count(UserStory.id).label("count"))
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
        db.query(Defect.severity, func.count(Defect.id).label("count")).group_by(Defect.severity).all()
    )

    defect_severity = {severity: count for severity, count in defect_severity_query}

    # Recent activity (last 7 days)
    from datetime import datetime, timedelta

    recent_date = datetime.now(datetime.UTC) - timedelta(days=7)

    recent_tests = db.query(Test).filter(Test.last_execution_time >= recent_date).count()

    recent_defects = db.query(Defect).filter(Defect.created_at >= recent_date).count()

    return {
        "timestamp": datetime.now(datetime.UTC).isoformat(),
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
        raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# Epic Advanced Metrics Endpoints (US-00071) - Multi-persona dashboard


@router.get("/epics/{epic_id}/metrics")
def get_epic_metrics(
    epic_id: str,
    persona: Optional[str] = Query(None, description="Dashboard persona: PM, PO, QA"),
    force_refresh: bool = Query(False, description="Force metrics recalculation"),
    db: Session = Depends(get_db),
):
    """Get comprehensive metrics for an Epic, optionally filtered by persona."""
    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")

    if persona:
        metrics = epic.get_persona_specific_metrics(persona)
        return {
            "epic_id": epic_id,
            "persona": persona.upper(),
            "metrics": metrics,
            "last_updated": epic.last_metrics_update.isoformat() if epic.last_metrics_update else None,
        }
    else:
        metrics = epic.update_metrics(force_recalculate=force_refresh)
        return {
            "epic_id": epic_id,
            "metrics": metrics,
            "last_updated": epic.last_metrics_update.isoformat() if epic.last_metrics_update else None,
        }


@router.post("/epics/{epic_id}/metrics/update")
def update_epic_metrics(
    epic_id: str,
    velocity_points_per_sprint: Optional[float] = None,
    team_size: Optional[int] = None,
    test_coverage_percentage: Optional[float] = None,
    code_review_score: Optional[float] = None,
    stakeholder_satisfaction_score: Optional[float] = None,
    business_impact_score: Optional[float] = None,
    roi_percentage: Optional[float] = None,
    user_adoption_rate: Optional[float] = None,
    technical_debt_hours: Optional[int] = None,
    planned_start_date: Optional[str] = None,
    planned_end_date: Optional[str] = None,
    actual_start_date: Optional[str] = None,
    actual_end_date: Optional[str] = None,
    estimated_duration_days: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Update Epic metrics values and recalculate derived metrics."""
    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")

    # Update provided metrics
    if velocity_points_per_sprint is not None:
        epic.velocity_points_per_sprint = velocity_points_per_sprint
    if team_size is not None:
        epic.team_size = team_size
    if test_coverage_percentage is not None:
        epic.test_coverage_percentage = test_coverage_percentage
    if code_review_score is not None:
        epic.code_review_score = code_review_score
    if stakeholder_satisfaction_score is not None:
        epic.stakeholder_satisfaction_score = stakeholder_satisfaction_score
    if business_impact_score is not None:
        epic.business_impact_score = business_impact_score
    if roi_percentage is not None:
        epic.roi_percentage = roi_percentage
    if user_adoption_rate is not None:
        epic.user_adoption_rate = user_adoption_rate
    if technical_debt_hours is not None:
        epic.technical_debt_hours = technical_debt_hours
    if estimated_duration_days is not None:
        epic.estimated_duration_days = estimated_duration_days

    # Update date fields
    if planned_start_date:
        try:
            epic.planned_start_date = datetime.fromisoformat(planned_start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid planned_start_date format. Use ISO format.")

    if planned_end_date:
        try:
            epic.planned_end_date = datetime.fromisoformat(planned_end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid planned_end_date format. Use ISO format.")

    if actual_start_date:
        try:
            epic.actual_start_date = datetime.fromisoformat(actual_start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid actual_start_date format. Use ISO format.")

    if actual_end_date:
        try:
            epic.actual_end_date = datetime.fromisoformat(actual_end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid actual_end_date format. Use ISO format.")

    # Save changes and recalculate metrics
    db.commit()
    metrics = epic.update_metrics(force_recalculate=True)

    return {
        "epic_id": epic_id,
        "message": "Epic metrics updated successfully",
        "updated_metrics": metrics,
        "last_updated": epic.last_metrics_update.isoformat(),
    }


@router.get("/epics/{epic_id}/metrics/timeline")
def get_epic_timeline_metrics(epic_id: str, db: Session = Depends(get_db)):
    """Get timeline and schedule metrics for an Epic."""
    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")

    timeline_metrics = epic.calculate_timeline_metrics()
    return {"epic_id": epic_id, "timeline_metrics": timeline_metrics}


@router.get("/epics/{epic_id}/metrics/velocity")
def get_epic_velocity_metrics(epic_id: str, db: Session = Depends(get_db)):
    """Get velocity and productivity metrics for an Epic."""
    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")

    velocity_metrics = epic.calculate_velocity_metrics()
    return {"epic_id": epic_id, "velocity_metrics": velocity_metrics}


@router.get("/epics/{epic_id}/metrics/quality")
def get_epic_quality_metrics(epic_id: str, db: Session = Depends(get_db)):
    """Get quality and technical debt metrics for an Epic."""
    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")

    quality_metrics = epic.calculate_quality_metrics()
    return {"epic_id": epic_id, "quality_metrics": quality_metrics}


@router.get("/epics/{epic_id}/metrics/business")
def get_epic_business_metrics(epic_id: str, db: Session = Depends(get_db)):
    """Get business value and stakeholder metrics for an Epic."""
    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")

    business_metrics = epic.calculate_business_metrics()
    return {"epic_id": epic_id, "business_metrics": business_metrics}


@router.get("/epics/{epic_id}/metrics/predictions")
def get_epic_predictive_metrics(epic_id: str, db: Session = Depends(get_db)):
    """Get predictive analytics and risk assessment for an Epic."""
    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")

    predictive_metrics = epic.calculate_predictive_metrics()
    return {"epic_id": epic_id, "predictive_metrics": predictive_metrics}


@router.get("/dashboard/metrics")
def get_dashboard_metrics(
    persona: str = Query(..., description="Dashboard persona: PM, PO, QA"),
    epic_filter: Optional[str] = Query(None, description="Filter by epic_id"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    component_filter: Optional[str] = Query(None, description="Filter by component"),
    db: Session = Depends(get_db),
):
    """Get aggregated metrics for the multi-persona dashboard."""

    # Build query with filters
    query = db.query(Epic)

    if epic_filter:
        query = query.filter(Epic.epic_id == epic_filter)
    if status_filter:
        query = query.filter(Epic.status == status_filter)
    if component_filter:
        query = query.filter(Epic.component == component_filter)

    epics = query.all()

    if not epics:
        return {
            "persona": persona.upper(),
            "message": "No epics found matching the criteria",
            "epics": [],
            "summary": {},
        }

    thresholds = get_threshold_service()

    # Collect persona-specific metrics for all epics
    epic_metrics = []
    for epic in epics:
        metrics = epic.get_persona_specific_metrics(persona, session=db, thresholds=thresholds)
        epic_metrics.append(
            {
                "epic_id": epic.epic_id,
                "title": epic.title,
                "status": epic.status,
                "completion_percentage": epic.completion_percentage,
                "priority": epic.priority,
                "metrics": metrics,
            }
        )

    # Calculate aggregated summary based on persona
    summary = calculate_dashboard_summary(epic_metrics, persona)

    return {
        "persona": persona.upper(),
        "epics": epic_metrics,
        "summary": summary,
        "filters_applied": {
            "epic_filter": epic_filter,
            "status_filter": status_filter,
            "component_filter": component_filter,
        },
    }


@router.get("/dashboard/metrics/demo")
def get_dashboard_metrics_demo(
    persona: str = Query(..., description="Dashboard persona: PM, PO, QA"),
    epic_filter: Optional[str] = Query(None, description="Filter by epic_id"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    component_filter: Optional[str] = Query(None, description="Filter by component"),
):
    """Get aggregated metrics for the multi-persona dashboard (demo dataset)."""
    dataset = load_demo_dataset()
    all_epics = dataset.get("epics", [])
    epics = filter_demo_epics(all_epics, epic_filter, status_filter, component_filter)

    if not epics:
        return {
            "persona": persona.upper(),
            "message": "No epics found matching the criteria (demo)",
            "epics": [],
            "summary": {},
        }

    epic_metrics = []
    for epic in epics:
        epic_metrics.append(
            {
                "epic_id": epic.get("epic_id"),
                "title": epic.get("title", ""),
                "status": epic.get("status", ""),
                "completion_percentage": epic.get("completion_percentage", 0),
                "priority": epic.get("priority", ""),
                "metrics": epic.get("metrics", {}),
            }
        )

    summary = calculate_dashboard_summary(epic_metrics, persona)

    return {
        "persona": persona.upper(),
        "epics": epic_metrics,
        "summary": summary,
        "filters_applied": {
            "epic_filter": epic_filter,
            "status_filter": status_filter,
            "component_filter": component_filter,
        },
        "mode": "demo",
    }


def _extract_metric_value(metric_data, default=0):
    """Extract numeric value from threshold-evaluated metric data."""
    if isinstance(metric_data, dict) and "value" in metric_data:
        return metric_data["value"] or default
    return metric_data if metric_data is not None else default


def calculate_dashboard_summary(epic_metrics: List[dict], persona: str) -> dict:
    """Calculate aggregated summary metrics for dashboard personas."""
    if not epic_metrics:
        return {}

    total_epics = len(epic_metrics)

    persona_key = persona.lower()

    if persona_key == "pm":
        at_risk_count = sum(
            1
            for epic in epic_metrics
            if _extract_metric_value(epic["metrics"].get("risk", {}).get("overall_risk_score", 0)) > 30
        )
        avg_velocity = (
            sum(
                _extract_metric_value(epic["metrics"].get("velocity", {}).get("velocity_points_per_sprint", 0))
                for epic in epic_metrics
            )
            / total_epics
        )
        avg_schedule_variance = (
            sum(
                _extract_metric_value(epic["metrics"].get("timeline", {}).get("schedule_variance_days", 0))
                for epic in epic_metrics
            )
            / total_epics
        )
        avg_velocity_per_member = (
            sum(
                _extract_metric_value(epic["metrics"].get("team_productivity", {}).get("velocity_per_team_member", 0))
                for epic in epic_metrics
            )
            / total_epics
        )
        avg_success_probability = (
            sum(
                _extract_metric_value(epic["metrics"].get("risk", {}).get("success_probability", 0))
                for epic in epic_metrics
            )
            / total_epics
        )

        return {
            "total_epics": total_epics,
            "at_risk_epics": at_risk_count,
            "risk_percentage": (at_risk_count / total_epics) * 100,
            "average_velocity": round(avg_velocity, 2),
            "average_velocity_per_member": round(avg_velocity_per_member, 2),
            "average_schedule_variance": round(avg_schedule_variance, 1),
            "average_success_probability": round(avg_success_probability, 1),
            "schedule_health": "Good" if at_risk_count < total_epics * 0.3 else "Needs Attention",
        }

    elif persona_key == "po":
        avg_satisfaction = (
            sum(
                _extract_metric_value(epic["metrics"].get("stakeholder", {}).get("satisfaction_score", 0))
                for epic in epic_metrics
            )
            / total_epics
        )
        high_scope_creep = sum(
            1
            for epic in epic_metrics
            if _extract_metric_value(epic["metrics"].get("scope", {}).get("scope_creep_percentage", 0)) > 20
        )
        avg_roi = (
            sum(
                _extract_metric_value(epic["metrics"].get("business_value", {}).get("roi_percentage", 0))
                for epic in epic_metrics
            )
            / total_epics
        )
        avg_adoption = (
            sum(
                _extract_metric_value(epic["metrics"].get("adoption", {}).get("user_adoption_rate", 0))
                for epic in epic_metrics
            )
            / total_epics
        )
        avg_scope_creep_percentage = (
            sum(
                _extract_metric_value(epic["metrics"].get("scope", {}).get("scope_creep_percentage", 0))
                for epic in epic_metrics
            )
            / total_epics
        )

        return {
            "total_epics": total_epics,
            "average_satisfaction": round(avg_satisfaction, 1),
            "average_roi": round(avg_roi, 1),
            "average_adoption": round(avg_adoption, 1),
            "average_scope_creep_percentage": round(avg_scope_creep_percentage, 1),
            "scope_creep_issues": high_scope_creep,
            "satisfaction_grade": "Good" if avg_satisfaction >= 7 else "Needs Improvement",
            "business_health": "Healthy" if high_scope_creep < total_epics * 0.3 else "Monitor",
        }

    elif persona_key == "qa":
        avg_coverage = (
            sum(
                _extract_metric_value(epic["metrics"].get("testing", {}).get("test_coverage", 0))
                for epic in epic_metrics
            )
            / total_epics
        )
        high_defect_density = sum(
            1
            for epic in epic_metrics
            if _extract_metric_value(epic["metrics"].get("defects", {}).get("defect_density", 0)) > 0.5
        )
        avg_defect_density = (
            sum(
                _extract_metric_value(epic["metrics"].get("defects", {}).get("defect_density", 0))
                for epic in epic_metrics
            )
            / total_epics
        )
        avg_technical_debt = (
            sum(
                _extract_metric_value(epic["metrics"].get("technical_debt", {}).get("debt_hours", 0))
                for epic in epic_metrics
            )
            / total_epics
        )

        return {
            "total_epics": total_epics,
            "average_test_coverage": round(avg_coverage, 1),
            "average_defect_density": round(avg_defect_density, 2),
            "average_technical_debt": round(avg_technical_debt, 1),
            "high_defect_epics": high_defect_density,
            "coverage_grade": "Good" if avg_coverage >= 80 else "Needs Improvement",
            "quality_health": "Good" if high_defect_density < total_epics * 0.2 else "Attention Required",
        }

    else:
        return {"total_epics": total_epics}


# Temporary dependency endpoints for visualizer (US-00073)
# TODO: Move to epic_dependencies.py when server import issues resolved


@router.get("/dependencies")
def get_dependencies(db: Session = Depends(get_db)):
    """Temporary endpoint for dependency visualization."""
    try:
        from ..models.traceability.epic_dependency import EpicDependency

        dependencies = db.query(EpicDependency).filter(EpicDependency.is_active == True).all()

        result = []
        for dep in dependencies:
            result.append(
                {
                    "id": dep.id,
                    "parent_epic_id": dep.parent_epic_id,
                    "dependent_epic_id": dep.dependent_epic_id,
                    "dependency_type": dep.dependency_type,
                    "priority": dep.priority,
                    "reason": dep.reason,
                    "estimated_impact_days": dep.estimated_impact_days,
                    "is_active": dep.is_active,
                    "created_at": dep.created_at.isoformat() if dep.created_at else None,
                }
            )

        return result
    except Exception as e:
        # Return empty list if dependencies not set up yet
        return []


@router.get("/dependencies/analysis/critical-path")
def get_critical_path(db: Session = Depends(get_db)):
    """Get critical path analysis for dependencies."""
    try:
        from ..models.traceability.epic_dependency import DependencyGraph

        epics = db.query(Epic).all()
        graph = DependencyGraph()

        # Add epics to graph
        for epic in epics:
            graph.add_epic(epic.id, epic.epic_id, epic.title)

        # Add dependencies
        from ..models.traceability.epic_dependency import EpicDependency

        dependencies = db.query(EpicDependency).filter(EpicDependency.is_active == True).all()
        for dep in dependencies:
            graph.add_dependency(dep.parent_epic_id, dep.dependent_epic_id, dep.dependency_type, dep.priority)

        critical_path = graph.find_critical_path()

        return {
            "critical_path": critical_path,
            "path_length": len(critical_path),
            "total_impact": sum(dep.get("impact_days", 0) for dep in critical_path),
        }
    except Exception:
        return {"critical_path": [], "path_length": 0, "total_impact": 0}


@router.get("/dependencies/analysis/cycles")
def detect_cycles(db: Session = Depends(get_db)):
    """Detect circular dependencies."""
    try:
        from ..models.traceability.epic_dependency import DependencyGraph

        epics = db.query(Epic).all()
        graph = DependencyGraph()

        # Add epics to graph
        for epic in epics:
            graph.add_epic(epic.id, epic.epic_id, epic.title)

        # Add dependencies
        from ..models.traceability.epic_dependency import EpicDependency

        dependencies = db.query(EpicDependency).filter(EpicDependency.is_active == True).all()
        for dep in dependencies:
            graph.add_dependency(dep.parent_epic_id, dep.dependent_epic_id, dep.dependency_type, dep.priority)

        cycles = graph.detect_cycles()

        return {"has_cycles": len(cycles) > 0, "cycles": cycles, "cycle_count": len(cycles)}
    except Exception:
        return {"has_cycles": False, "cycles": [], "cycle_count": 0}
