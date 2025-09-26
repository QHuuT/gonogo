"""
Program Areas/Capabilities API Router

REST API endpoints for managing strategic Epic grouping through Capabilities.
Implements Program Areas/Capabilities functionality per US-00062.

Related Issue: US-00062 - Program Areas/Capabilities - Epic Grouping and Strategic Management
Parent Epic: EP-00010 - Dashboard de Traçabilité Multi-Persona
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict

from ..database import get_db
from ..models.traceability.capability import Capability, CapabilityDependency
from ..models.traceability.epic import Epic

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


# Pydantic models for API requests/responses
class CapabilityCreate(BaseModel):
    capability_id: str = Field(..., description="Capability ID (CAP-00001)", json_schema_extra={"example": "CAP-00001"})
    name: str = Field(..., description="Capability name", json_schema_extra={"example": "GitHub Integration"})
    description: Optional[str] = Field(None, description="Detailed description")
    strategic_priority: str = Field("medium", description="Strategic priority")
    business_value_theme: Optional[str] = Field(None, description="Business value theme")
    owner: Optional[str] = Field(None, description="Capability owner")
    estimated_business_impact_score: float = Field(0.0, description="Business impact score (0-100)")
    roi_target_percentage: float = Field(0.0, description="Target ROI percentage")
    strategic_alignment_score: float = Field(0.0, description="Strategic alignment score (0-100)")


class CapabilityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    strategic_priority: Optional[str] = None
    business_value_theme: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    completion_percentage: Optional[float] = None
    estimated_business_impact_score: Optional[float] = None
    roi_target_percentage: Optional[float] = None
    strategic_alignment_score: Optional[float] = None


class CapabilityResponse(BaseModel):
    id: int
    capability_id: str
    name: str
    description: Optional[str]
    strategic_priority: str
    business_value_theme: Optional[str]
    owner: Optional[str]
    status: str
    completion_percentage: float
    epic_count: int
    estimated_business_impact_score: float
    roi_target_percentage: float
    strategic_alignment_score: float

    model_config = ConfigDict(from_attributes=True)


# Capability CRUD endpoints
@router.get("/", response_model=List[CapabilityResponse])
def get_capabilities(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by strategic priority"),
    db: Session = Depends(get_db)
):
    """Get all capabilities with optional filtering."""
    query = db.query(Capability)

    if status:
        query = query.filter(Capability.status == status)
    if priority:
        query = query.filter(Capability.strategic_priority == priority)

    capabilities = query.offset(skip).limit(limit).all()

    # Add epic count to each capability
    result = []
    for capability in capabilities:
        cap_dict = capability.to_dict()
        cap_dict["epic_count"] = capability.epics.count()
        result.append(cap_dict)

    return result


@router.get("/{capability_id}", response_model=CapabilityResponse)
def get_capability(capability_id: str, db: Session = Depends(get_db)):
    """Get a specific capability by ID."""
    capability = db.query(Capability).filter(Capability.capability_id == capability_id).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")

    cap_dict = capability.to_dict()
    cap_dict["epic_count"] = capability.epics.count()
    return cap_dict


@router.post("/", response_model=CapabilityResponse)
def create_capability(capability: CapabilityCreate, db: Session = Depends(get_db)):
    """Create a new capability."""
    # Check if capability_id already exists
    existing = db.query(Capability).filter(Capability.capability_id == capability.capability_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Capability ID already exists")

    db_capability = Capability(**capability.dict())
    db.add(db_capability)
    db.commit()
    db.refresh(db_capability)

    cap_dict = db_capability.to_dict()
    cap_dict["epic_count"] = 0  # New capability has no epics yet
    return cap_dict


@router.put("/{capability_id}", response_model=CapabilityResponse)
def update_capability(capability_id: str, capability_update: CapabilityUpdate, db: Session = Depends(get_db)):
    """Update an existing capability."""
    capability = db.query(Capability).filter(Capability.capability_id == capability_id).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")

    # Update fields that are provided
    for field, value in capability_update.dict(exclude_unset=True).items():
        setattr(capability, field, value)

    db.commit()
    db.refresh(capability)

    cap_dict = capability.to_dict()
    cap_dict["epic_count"] = capability.epics.count()
    return cap_dict


@router.delete("/{capability_id}")
def delete_capability(capability_id: str, db: Session = Depends(get_db)):
    """Delete a capability."""
    capability = db.query(Capability).filter(Capability.capability_id == capability_id).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")

    # Check if capability has assigned epics
    epic_count = capability.epics.count()
    if epic_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete capability with {epic_count} assigned epics. Remove epics first."
        )

    db.delete(capability)
    db.commit()
    return {"message": "Capability deleted successfully"}


# Epic assignment endpoints
@router.get("/{capability_id}/epics")
def get_capability_epics(capability_id: str, db: Session = Depends(get_db)):
    """Get all epics assigned to a capability."""
    capability = db.query(Capability).filter(Capability.capability_id == capability_id).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")

    epics = [epic.to_dict() for epic in capability.epics]
    return {
        "capability_id": capability_id,
        "capability_name": capability.name,
        "epic_count": len(epics),
        "epics": epics
    }


@router.post("/{capability_id}/epics/{epic_id}")
def assign_epic_to_capability(capability_id: str, epic_id: str, db: Session = Depends(get_db)):
    """Assign an epic to a capability."""
    capability = db.query(Capability).filter(Capability.capability_id == capability_id).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")

    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    # Assign the epic to the capability
    epic.capability_id = capability.id
    db.commit()

    return {
        "message": "Epic assigned to capability successfully",
        "capability_id": capability_id,
        "epic_id": epic_id
    }


@router.delete("/{capability_id}/epics/{epic_id}")
def unassign_epic_from_capability(capability_id: str, epic_id: str, db: Session = Depends(get_db)):
    """Remove an epic from a capability."""
    capability = db.query(Capability).filter(Capability.capability_id == capability_id).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")

    epic = db.query(Epic).filter(Epic.epic_id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    if epic.capability_id != capability.id:
        raise HTTPException(status_code=400, detail="Epic is not assigned to this capability")

    # Remove the epic from the capability
    epic.capability_id = None
    db.commit()

    return {
        "message": "Epic unassigned from capability successfully",
        "capability_id": capability_id,
        "epic_id": epic_id
    }


# Analytics and reporting endpoints
@router.get("/{capability_id}/metrics")
def get_capability_metrics(capability_id: str, db: Session = Depends(get_db)):
    """Get comprehensive metrics for a capability."""
    capability = db.query(Capability).filter(Capability.capability_id == capability_id).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")

    # Calculate metrics
    business_metrics = capability.calculate_business_metrics()
    epic_status_counts = capability.get_epic_count_by_status()
    critical_path = capability.get_critical_path_analysis()

    return {
        "capability_id": capability_id,
        "capability_name": capability.name,
        "completion_percentage": capability.calculate_completion_percentage(),
        "business_metrics": business_metrics,
        "epic_status_distribution": epic_status_counts,
        "critical_path_analysis": critical_path
    }


@router.get("/", response_model=List[dict])
def get_capabilities_summary(db: Session = Depends(get_db)):
    """Get summary view of all capabilities with key metrics."""
    capabilities = db.query(Capability).all()

    summary = []
    for capability in capabilities:
        business_metrics = capability.calculate_business_metrics()
        epic_counts = capability.get_epic_count_by_status()

        summary.append({
            "capability_id": capability.capability_id,
            "name": capability.name,
            "strategic_priority": capability.strategic_priority,
            "status": capability.status,
            "completion_percentage": capability.calculate_completion_percentage(),
            "epic_count": capability.epics.count(),
            "epic_status_distribution": epic_counts,
            "total_story_points": business_metrics["total_story_points"],
            "average_roi": business_metrics["average_roi"],
            "business_impact_score": capability.estimated_business_impact_score
        })

    return summary