"""
FastAPI routes for RTM (Requirements Traceability Matrix) operations.

Provides CRUD operations for all traceability entities in the hybrid GitHub + Database architecture.

Related Issue: US-00054 - Database models and migration foundation
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
Architecture Decision: ADR-003 - Hybrid GitHub + Database RTM Architecture
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database import get_db
from ..models.traceability import Epic, UserStory, Defect, Test, GitHubSync

router = APIRouter(prefix="/api/rtm", tags=["RTM"])


# Epic CRUD Operations
@router.post("/epics/", response_model=dict)
def create_epic(
    epic_id: str,
    title: str,
    description: Optional[str] = None,
    business_value: Optional[str] = None,
    priority: str = "medium",
    db: Session = Depends(get_db)
):
    """Create a new Epic."""
    epic = Epic(
        epic_id=epic_id,
        title=title,
        description=description,
        business_value=business_value,
        priority=priority
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    """Create a new User Story."""
    user_story = UserStory(
        user_story_id=user_story_id,
        epic_id=epic_id,
        github_issue_number=github_issue_number,
        title=title,
        description=description,
        story_points=story_points,
        priority=priority
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    """Create a new Test."""
    test = Test(
        test_type=test_type,
        test_file_path=test_file_path,
        title=title,
        epic_id=epic_id,
        test_function_name=test_function_name,
        bdd_scenario_name=bdd_scenario_name
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
    limit: int = Query(50, le=100, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    """Create a new Defect."""
    defect = Defect(
        defect_id=defect_id,
        github_issue_number=github_issue_number,
        title=title,
        severity=severity,
        priority=priority,
        epic_id=epic_id,
        test_id=test_id
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
    limit: int = Query(50, le=100, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
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
        us.story_points for us in user_stories
        if us.implementation_status in ['done', 'completed']
    )

    test_pass_rate = 0.0
    if tests:
        passed_tests = sum(1 for test in tests if test.last_execution_status == 'passed')
        test_pass_rate = (passed_tests / len(tests)) * 100

    critical_defects = sum(1 for defect in defects if defect.severity == 'critical')
    open_defects = sum(1 for defect in defects if defect.status in ['open', 'in_progress'])

    return {
        "epic": epic.to_dict(),
        "metrics": {
            "total_story_points": total_story_points,
            "completed_story_points": completed_story_points,
            "completion_percentage": (completed_story_points / total_story_points * 100) if total_story_points > 0 else 0,
            "user_stories_count": len(user_stories),
            "tests_count": len(tests),
            "test_pass_rate": test_pass_rate,
            "defects_count": len(defects),
            "critical_defects": critical_defects,
            "open_defects": open_defects
        }
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
    completed_epics = sum(1 for epic in epics if epic.status == 'completed')

    total_story_points = sum(us.story_points for us in user_stories)
    completed_story_points = sum(
        us.story_points for us in user_stories
        if us.implementation_status in ['done', 'completed']
    )

    total_tests = len(tests)
    passed_tests = sum(1 for test in tests if test.last_execution_status == 'passed')

    critical_defects = sum(1 for defect in defects if defect.severity == 'critical')
    security_issues = sum(1 for defect in defects if defect.is_security_issue)

    return {
        "summary": {
            "epics": {
                "total": total_epics,
                "completed": completed_epics,
                "completion_rate": (completed_epics / total_epics * 100) if total_epics > 0 else 0
            },
            "user_stories": {
                "total": len(user_stories),
                "story_points": {
                    "total": total_story_points,
                    "completed": completed_story_points,
                    "completion_rate": (completed_story_points / total_story_points * 100) if total_story_points > 0 else 0
                }
            },
            "tests": {
                "total": total_tests,
                "passed": passed_tests,
                "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "defects": {
                "total": len(defects),
                "critical": critical_defects,
                "security_issues": security_issues
            }
        }
    }