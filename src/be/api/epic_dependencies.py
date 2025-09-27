"""
Epic Dependencies API

FastAPI endpoints for managing Epic dependencies in the dashboard system.
Provides CRUD operations, cycle detection, and critical path calculation.

Related Issue: US-00070 - Modèle dépendances fonctionnelles Epic
Parent Epic: EP-00010 - Dashboard de Traçabilité Multi-Persona
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict

from ..database import get_db_session
from ..models.traceability.epic import Epic
from ..models.traceability.epic_dependency import (
    EpicDependency,
    DependencyGraph,
    DependencyType,
)


# Pydantic models pour les requêtes/réponses API
class DependencyCreate(BaseModel):
    """Modèle pour créer une dépendance Epic."""

    parent_epic_id: int = Field(..., description="ID de l'Epic parent (qui bloque)")
    dependent_epic_id: int = Field(
        ..., description="ID de l'Epic dépendant (qui est bloqué)"
    )
    dependency_type: str = Field(
        ...,
        description="Type de dépendance",
        pattern="^(blocking|prerequisite|informational|technical|business)$",
    )
    priority: str = Field(
        "medium",
        description="Priorité de la dépendance",
        pattern="^(critical|high|medium|low)$",
    )
    reason: Optional[str] = Field(
        None, description="Raison/explication de la dépendance"
    )
    estimated_impact_days: Optional[int] = Field(
        None, description="Impact estimé en jours", ge=0, le=365
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parent_epic_id": 1,
                "dependent_epic_id": 2,
                "dependency_type": "blocking",
                "priority": "high",
                "reason": "Epic 2 needs authentication system from Epic 1",
                "estimated_impact_days": 5,
            }
        }
    )


class DependencyUpdate(BaseModel):
    """Modèle pour mettre à jour une dépendance Epic."""

    dependency_type: Optional[str] = Field(
        None, pattern="^(blocking|prerequisite|informational|technical|business)$"
    )
    priority: Optional[str] = Field(None, pattern="^(critical|high|medium|low)$")
    reason: Optional[str] = None
    estimated_impact_days: Optional[int] = Field(None, ge=0, le=365)
    is_active: Optional[bool] = None
    resolution_notes: Optional[str] = None


class DependencyResponse(BaseModel):
    """Modèle de réponse pour une dépendance Epic."""

    id: int
    parent_epic_id: int
    dependent_epic_id: int
    dependency_type: str
    priority: str
    reason: Optional[str]
    estimated_impact_days: Optional[int]
    is_active: bool
    is_resolved: bool
    resolution_date: Optional[str]
    resolution_notes: Optional[str]
    created_by_system: bool
    validation_status: str
    created_at: str
    updated_at: str

    # Computed fields
    criticality_score: int
    is_blocking: bool

    model_config = ConfigDict(from_attributes=True)


class CriticalPathResponse(BaseModel):
    """Réponse pour le calcul du chemin critique."""

    critical_path: List[int]
    total_duration: int
    distances: Dict[str, int]
    bottlenecks: List[int]


class DependencyAnalysis(BaseModel):
    """Analyse d'impact des dépendances pour un Epic."""

    epic_id: int
    blocks_count: int
    blocked_by_count: int
    blocking_epics: List[int]
    blocked_by_epics: List[int]
    critical_dependencies: List[DependencyResponse]
    risk_score: int


router = APIRouter(prefix="/api/epic-dependencies", tags=["Epic Dependencies"])


def get_db():
    """Dependency injection pour la session DB."""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/", response_model=DependencyResponse, status_code=status.HTTP_201_CREATED
)
async def create_dependency(
    dependency: DependencyCreate, db: Session = Depends(get_db)
):
    """Créer une nouvelle dépendance Epic avec validation anti-cycle."""

    # Vérifier que les Epics existent
    parent_epic = db.query(Epic).filter(Epic.id == dependency.parent_epic_id).first()
    if not parent_epic:
        raise HTTPException(
            status_code=404, detail=f"Parent Epic {dependency.parent_epic_id} not found"
        )

    dependent_epic = (
        db.query(Epic).filter(Epic.id == dependency.dependent_epic_id).first()
    )
    if not dependent_epic:
        raise HTTPException(
            status_code=404,
            detail=f"Dependent Epic {dependency.dependent_epic_id} not found",
        )

    # Vérifier les auto-dépendances
    if dependency.parent_epic_id == dependency.dependent_epic_id:
        raise HTTPException(status_code=400, detail="Epic cannot depend on itself")

    # Créer la dépendance temporairement pour tester les cycles
    test_dependency = EpicDependency(
        parent_epic_id=dependency.parent_epic_id,
        dependent_epic_id=dependency.dependent_epic_id,
        dependency_type=dependency.dependency_type,
        priority=dependency.priority,
        reason=dependency.reason,
        estimated_impact_days=dependency.estimated_impact_days,
    )

    # Tester la détection de cycles
    existing_dependencies = (
        db.query(EpicDependency).filter(EpicDependency.is_active == True).all()
    )
    test_dependencies = existing_dependencies + [test_dependency]

    graph = DependencyGraph(db)
    cycles = graph.detect_cycles(test_dependencies)

    if cycles:
        cycle_description = " -> ".join([str(epic_id) for epic_id in cycles[0]])
        raise HTTPException(
            status_code=400,
            detail=(
                f"Creating this dependency would create a cycle: {cycle_description}"
            ),
        )

    # Vérifier les doublons
    existing = (
        db.query(EpicDependency)
        .filter(
            EpicDependency.parent_epic_id == dependency.parent_epic_id,
            EpicDependency.dependent_epic_id == dependency.dependent_epic_id,
            EpicDependency.dependency_type == dependency.dependency_type,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Dependency already exists between Epic "
                f"{dependency.parent_epic_id} and "
                f"{dependency.dependent_epic_id} with type "
                f"'{dependency.dependency_type}'"
            ),
        )

    # Créer la dépendance
    db_dependency = EpicDependency(**dependency.dict())
    db.add(db_dependency)
    db.commit()
    db.refresh(db_dependency)

    # Convert to response format with computed fields
    dep_dict = {
        "id": db_dependency.id,
        "parent_epic_id": db_dependency.parent_epic_id,
        "dependent_epic_id": db_dependency.dependent_epic_id,
        "dependency_type": db_dependency.dependency_type,
        "priority": db_dependency.priority,
        "reason": db_dependency.reason,
        "estimated_impact_days": db_dependency.estimated_impact_days,
        "is_active": db_dependency.is_active,
        "is_resolved": db_dependency.is_resolved,
        "resolution_date": (
            db_dependency.resolution_date.isoformat()
            if db_dependency.resolution_date
            else None
        ),
        "resolution_notes": db_dependency.resolution_notes,
        "created_by_system": db_dependency.created_by_system,
        "validation_status": db_dependency.validation_status,
        "created_at": db_dependency.created_at.isoformat(),
        "updated_at": db_dependency.updated_at.isoformat(),
        "criticality_score": db_dependency.get_criticality_score(),
        "is_blocking": db_dependency.is_blocking(),
    }
    return DependencyResponse(**dep_dict)


@router.get("/", response_model=List[DependencyResponse])
async def list_dependencies(
    parent_epic_id: Optional[int] = Query(None, description="Filtrer par Epic parent"),
    dependent_epic_id: Optional[int] = Query(
        None, description="Filtrer par Epic dépendant"
    ),
    dependency_type: Optional[str] = Query(
        None, description="Filtrer par type de dépendance"
    ),
    priority: Optional[str] = Query(None, description="Filtrer par priorité"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    is_resolved: Optional[bool] = Query(None, description="Filtrer par statut résolu"),
    db: Session = Depends(get_db),
):
    """Lister les dépendances Epic avec filtres optionnels."""

    query = db.query(EpicDependency)

    if parent_epic_id is not None:
        query = query.filter(EpicDependency.parent_epic_id == parent_epic_id)

    if dependent_epic_id is not None:
        query = query.filter(EpicDependency.dependent_epic_id == dependent_epic_id)

    if dependency_type is not None:
        query = query.filter(EpicDependency.dependency_type == dependency_type)

    if priority is not None:
        query = query.filter(EpicDependency.priority == priority)

    if is_active is not None:
        query = query.filter(EpicDependency.is_active == is_active)

    if is_resolved is not None:
        query = query.filter(EpicDependency.is_resolved == is_resolved)

    dependencies = query.order_by(EpicDependency.created_at.desc()).all()

    # Convert to response format with computed fields
    result = []
    for dep in dependencies:
        dep_dict = {
            "id": dep.id,
            "parent_epic_id": dep.parent_epic_id,
            "dependent_epic_id": dep.dependent_epic_id,
            "dependency_type": dep.dependency_type,
            "priority": dep.priority,
            "reason": dep.reason,
            "estimated_impact_days": dep.estimated_impact_days,
            "is_active": dep.is_active,
            "is_resolved": dep.is_resolved,
            "resolution_date": (
                dep.resolution_date.isoformat() if dep.resolution_date else None
            ),
            "resolution_notes": dep.resolution_notes,
            "created_by_system": dep.created_by_system,
            "validation_status": dep.validation_status,
            "created_at": dep.created_at.isoformat(),
            "updated_at": dep.updated_at.isoformat(),
            "criticality_score": dep.get_criticality_score(),
            "is_blocking": dep.is_blocking(),
        }
        result.append(DependencyResponse(**dep_dict))

    return result


@router.get("/{dependency_id}", response_model=DependencyResponse)
async def get_dependency(dependency_id: int, db: Session = Depends(get_db)):
    """Récupérer une dépendance Epic par ID."""

    dependency = (
        db.query(EpicDependency).filter(EpicDependency.id == dependency_id).first()
    )
    if not dependency:
        raise HTTPException(
            status_code=404, detail=f"Dependency {dependency_id} not found"
        )

    # Convert to response format with computed fields
    dep_dict = {
        "id": dependency.id,
        "parent_epic_id": dependency.parent_epic_id,
        "dependent_epic_id": dependency.dependent_epic_id,
        "dependency_type": dependency.dependency_type,
        "priority": dependency.priority,
        "reason": dependency.reason,
        "estimated_impact_days": dependency.estimated_impact_days,
        "is_active": dependency.is_active,
        "is_resolved": dependency.is_resolved,
        "resolution_date": (
            dependency.resolution_date.isoformat()
            if dependency.resolution_date
            else None
        ),
        "resolution_notes": dependency.resolution_notes,
        "created_by_system": dependency.created_by_system,
        "validation_status": dependency.validation_status,
        "created_at": dependency.created_at.isoformat(),
        "updated_at": dependency.updated_at.isoformat(),
        "criticality_score": dependency.get_criticality_score(),
        "is_blocking": dependency.is_blocking(),
    }
    return DependencyResponse(**dep_dict)


@router.put("/{dependency_id}", response_model=DependencyResponse)
async def update_dependency(
    dependency_id: int, update: DependencyUpdate, db: Session = Depends(get_db)
):
    """Mettre à jour une dépendance Epic."""

    dependency = (
        db.query(EpicDependency).filter(EpicDependency.id == dependency_id).first()
    )
    if not dependency:
        raise HTTPException(
            status_code=404, detail=f"Dependency {dependency_id} not found"
        )

    # Appliquer les mises à jour
    for field, value in update.dict(exclude_unset=True).items():
        if hasattr(dependency, field):
            setattr(dependency, field, value)

    db.commit()
    db.refresh(dependency)

    # Convert to response format with computed fields
    dep_dict = {
        "id": dependency.id,
        "parent_epic_id": dependency.parent_epic_id,
        "dependent_epic_id": dependency.dependent_epic_id,
        "dependency_type": dependency.dependency_type,
        "priority": dependency.priority,
        "reason": dependency.reason,
        "estimated_impact_days": dependency.estimated_impact_days,
        "is_active": dependency.is_active,
        "is_resolved": dependency.is_resolved,
        "resolution_date": (
            dependency.resolution_date.isoformat()
            if dependency.resolution_date
            else None
        ),
        "resolution_notes": dependency.resolution_notes,
        "created_by_system": dependency.created_by_system,
        "validation_status": dependency.validation_status,
        "created_at": dependency.created_at.isoformat(),
        "updated_at": dependency.updated_at.isoformat(),
        "criticality_score": dependency.get_criticality_score(),
        "is_blocking": dependency.is_blocking(),
    }
    return DependencyResponse(**dep_dict)


@router.delete("/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dependency(dependency_id: int, db: Session = Depends(get_db)):
    """Supprimer une dépendance Epic."""

    dependency = (
        db.query(EpicDependency).filter(EpicDependency.id == dependency_id).first()
    )
    if not dependency:
        raise HTTPException(
            status_code=404, detail=f"Dependency {dependency_id} not found"
        )

    db.delete(dependency)
    db.commit()


@router.post("/{dependency_id}/resolve")
async def resolve_dependency(
    dependency_id: int, notes: Optional[str] = None, db: Session = Depends(get_db)
):
    """Marquer une dépendance comme résolue."""

    dependency = (
        db.query(EpicDependency).filter(EpicDependency.id == dependency_id).first()
    )
    if not dependency:
        raise HTTPException(
            status_code=404, detail=f"Dependency {dependency_id} not found"
        )

    dependency.mark_resolved(notes)
    db.commit()

    return {
        "message": "Dependency resolved successfully",
        "dependency_id": dependency_id,
    }


@router.post("/{dependency_id}/reactivate")
async def reactivate_dependency(
    dependency_id: int, reason: Optional[str] = None, db: Session = Depends(get_db)
):
    """Réactiver une dépendance."""

    dependency = (
        db.query(EpicDependency).filter(EpicDependency.id == dependency_id).first()
    )
    if not dependency:
        raise HTTPException(
            status_code=404, detail=f"Dependency {dependency_id} not found"
        )

    dependency.reactivate(reason)
    db.commit()

    return {
        "message": "Dependency reactivated successfully",
        "dependency_id": dependency_id,
    }


@router.get("/analysis/cycles")
async def detect_cycles(db: Session = Depends(get_db)):
    """Détecter les cycles dans les dépendances Epic."""

    graph = DependencyGraph(db)
    cycles = graph.detect_cycles()

    return {
        "cycles_detected": len(cycles) > 0,
        "cycle_count": len(cycles),
        "cycles": cycles,
    }


@router.get("/analysis/critical-path", response_model=CriticalPathResponse)
async def calculate_critical_path(
    epic_ids: Optional[str] = Query(
        None, description="IDs des Epics séparés par virgule"
    ),
    db: Session = Depends(get_db),
):
    """Calculer le chemin critique pour les Epics donnés."""

    if epic_ids:
        epic_id_list = [int(id.strip()) for id in epic_ids.split(",")]
    else:
        epic_id_list = None

    graph = DependencyGraph(db)
    result = graph.calculate_critical_path(epic_id_list)

    # Convertir les clés de distances en string pour JSON
    result["distances"] = {str(k): v for k, v in result["distances"].items()}

    return CriticalPathResponse(**result)


@router.get("/analysis/impact/{epic_id}", response_model=DependencyAnalysis)
async def analyze_epic_impact(epic_id: int, db: Session = Depends(get_db)):
    """Analyser l'impact des dépendances pour un Epic."""

    epic = db.query(Epic).filter(Epic.id == epic_id).first()
    if not epic:
        raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")

    graph = DependencyGraph(db)
    analysis = graph.get_dependency_impact(epic_id)

    # Convertir les critical_dependencies en DependencyResponse
    critical_deps = []
    for dep_dict in analysis["critical_dependencies"]:
        # Récupérer l'objet dependency complet pour la conversion
        dep_obj = (
            db.query(EpicDependency).filter(EpicDependency.id == dep_dict["id"]).first()
        )
        if dep_obj:
            critical_deps.append(DependencyResponse.from_orm(dep_obj))

    analysis["critical_dependencies"] = critical_deps

    return DependencyAnalysis(**analysis)


@router.get("/statistics/summary")
async def get_dependency_statistics(db: Session = Depends(get_db)):
    """Obtenir des statistiques générales sur les dépendances."""

    total_dependencies = db.query(EpicDependency).count()
    active_dependencies = (
        db.query(EpicDependency).filter(EpicDependency.is_active == True).count()
    )
    resolved_dependencies = (
        db.query(EpicDependency).filter(EpicDependency.is_resolved == True).count()
    )
    blocking_dependencies = (
        db.query(EpicDependency)
        .filter(
            EpicDependency.dependency_type == DependencyType.BLOCKING.value,
            EpicDependency.is_active == True,
            EpicDependency.is_resolved == False,
        )
        .count()
    )

    # Statistiques par type
    type_stats = {}
    for dep_type in DependencyType:
        count = (
            db.query(EpicDependency)
            .filter(
                EpicDependency.dependency_type == dep_type.value,
                EpicDependency.is_active == True,
            )
            .count()
        )
        type_stats[dep_type.value] = count

    # Statistiques par priorité
    priority_stats = {}
    for priority in ["critical", "high", "medium", "low"]:
        count = (
            db.query(EpicDependency)
            .filter(
                EpicDependency.priority == priority, EpicDependency.is_active == True
            )
            .count()
        )
        priority_stats[priority] = count

    return {
        "total_dependencies": total_dependencies,
        "active_dependencies": active_dependencies,
        "resolved_dependencies": resolved_dependencies,
        "blocking_dependencies": blocking_dependencies,
        "resolution_rate": (
            (resolved_dependencies / total_dependencies * 100)
            if total_dependencies > 0
            else 0
        ),
        "type_distribution": type_stats,
        "priority_distribution": priority_stats,
    }
