"""
Epic Dependency Model

Database model for Epic dependencies in the RTM system.
Manages functional dependencies between Epics with cycle detection and critical path calculation.

Related Issue: US-00070 - Modèle dépendances fonctionnelles Epic
Parent Epic: EP-00010 - Dashboard de Traçabilité Multi-Persona
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Index,
    UniqueConstraint,
    CheckConstraint,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship, validates
from datetime import datetime
from enum import Enum
from typing import List, Dict

from .base import TraceabilityBase


class DependencyType(Enum):
    """Types de dépendances entre Epics."""
    BLOCKING = "blocking"          # Epic A bloque Epic B - B ne peut pas commencer sans A
    PREREQUISITE = "prerequisite"  # Epic A est prérequis pour B - B peut commencer mais bénéficie de A
    INFORMATIONAL = "informational"  # Epic A informe Epic B - pas de blocage réel
    TECHNICAL = "technical"        # Dépendance technique (infrastructure, API, etc.)
    BUSINESS = "business"          # Dépendance business (processus, validation métier)


class EpicDependency(TraceabilityBase):
    """Dépendance entre deux Epics."""

    __tablename__ = "epic_dependencies"

    # Référence vers les Epics
    parent_epic_id = Column(Integer, ForeignKey("epics.id"), nullable=False, index=True)
    dependent_epic_id = Column(Integer, ForeignKey("epics.id"), nullable=False, index=True)

    # Type et priorité de la dépendance
    dependency_type = Column(String(20), nullable=False, default=DependencyType.PREREQUISITE.value, index=True)
    priority = Column(String(10), nullable=False, default="medium", index=True)  # critical, high, medium, low

    # Métadonnées
    reason = Column(Text, nullable=True)  # Explication de la dépendance
    estimated_impact_days = Column(Integer, nullable=True)  # Impact estimé en jours si non respectée

    # État de la dépendance
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolution_date = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Tracking automatique
    created_by_system = Column(Boolean, default=False, nullable=False)  # Détectée automatiquement
    last_validation_date = Column(DateTime, nullable=True)
    validation_status = Column(String(20), default="pending", nullable=False)  # pending, valid, invalid, warning

    # Relations
    parent_epic = relationship("Epic", foreign_keys=[parent_epic_id], back_populates="dependencies_as_parent")
    dependent_epic = relationship("Epic", foreign_keys=[dependent_epic_id], back_populates="dependencies_as_dependent")

    # Contraintes
    __table_args__ = (
        # Éviter les doublons
        UniqueConstraint('parent_epic_id', 'dependent_epic_id', 'dependency_type', name='uq_epic_dependency'),

        # Éviter les auto-dépendances
        CheckConstraint('parent_epic_id != dependent_epic_id', name='no_self_dependency'),

        # Index pour performance
        Index('idx_dependency_type_priority', 'dependency_type', 'priority'),
        Index('idx_dependency_active', 'is_active', 'is_resolved'),
        Index('idx_dependency_validation', 'validation_status', 'last_validation_date'),
    )

    @validates('dependency_type')
    def validate_dependency_type(self, key, value):
        """Valide le type de dépendance."""
        valid_types = [dt.value for dt in DependencyType]
        if value not in valid_types:
            raise ValueError(f"Invalid dependency type: {value}. Must be one of {valid_types}")
        return value

    @validates('priority')
    def validate_priority(self, key, value):
        """Valide la priorité."""
        valid_priorities = ['critical', 'high', 'medium', 'low']
        if value not in valid_priorities:
            raise ValueError(f"Invalid priority: {value}. Must be one of {valid_priorities}")
        return value

    @validates('validation_status')
    def validate_validation_status(self, key, value):
        """Valide le statut de validation."""
        valid_statuses = ['pending', 'valid', 'invalid', 'warning']
        if value not in valid_statuses:
            raise ValueError(f"Invalid validation status: {value}. Must be one of {valid_statuses}")
        return value

    def is_blocking(self) -> bool:
        """Retourne True si la dépendance est bloquante."""
        return self.dependency_type == DependencyType.BLOCKING.value and self.is_active and not self.is_resolved

    def get_criticality_score(self) -> int:
        """Calcule un score de criticité pour le tri et les alertes."""
        score = 0

        # Points par type
        type_scores = {
            DependencyType.BLOCKING.value: 10,
            DependencyType.PREREQUISITE.value: 7,
            DependencyType.TECHNICAL.value: 6,
            DependencyType.BUSINESS.value: 5,
            DependencyType.INFORMATIONAL.value: 2
        }
        score += type_scores.get(self.dependency_type, 0)

        # Points par priorité
        priority_scores = {'critical': 8, 'high': 6, 'medium': 3, 'low': 1}
        score += priority_scores.get(self.priority, 0)

        # Pénalité si pas résolue et active
        if self.is_active and not self.is_resolved:
            score += 5

        # Bonus impact estimé élevé
        if self.estimated_impact_days and self.estimated_impact_days > 5:
            score += 3

        return score

    def mark_resolved(self, notes: str = None):
        """Marque la dépendance comme résolue."""
        self.is_resolved = True
        self.resolution_date = datetime.now()
        if notes:
            self.resolution_notes = notes
        self.validation_status = "valid"

    def reactivate(self, reason: str = None):
        """Réactive la dépendance."""
        self.is_resolved = False
        self.resolution_date = None
        self.validation_status = "pending"
        if reason:
            self.reason = reason

    def update_validation(self, status: str, notes: str = None):
        """Met à jour le statut de validation."""
        self.validation_status = status
        self.last_validation_date = datetime.now()
        if notes and self.resolution_notes:
            self.resolution_notes += f"\n[{datetime.now()}] {notes}"
        elif notes:
            self.resolution_notes = notes

    def to_dict(self):
        """Convert to dictionary avec champs spécifiques."""
        base_dict = super().to_dict()
        base_dict.update({
            "parent_epic_id": self.parent_epic_id,
            "dependent_epic_id": self.dependent_epic_id,
            "dependency_type": self.dependency_type,
            "priority": self.priority,
            "reason": self.reason,
            "estimated_impact_days": self.estimated_impact_days,
            "is_active": self.is_active,
            "is_resolved": self.is_resolved,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None,
            "resolution_notes": self.resolution_notes,
            "created_by_system": self.created_by_system,
            "last_validation_date": self.last_validation_date.isoformat() if self.last_validation_date else None,
            "validation_status": self.validation_status,
            "criticality_score": self.get_criticality_score(),
            "is_blocking": self.is_blocking(),

            # Relations si chargées
            "parent_epic": self.parent_epic.to_dict() if self.parent_epic else None,
            "dependent_epic": self.dependent_epic.to_dict() if self.dependent_epic else None,
        })
        return base_dict

    def __repr__(self):
        return f"<EpicDependency(parent={self.parent_epic_id}, dependent={self.dependent_epic_id}, type='{self.dependency_type}', active={self.is_active})>"


class DependencyGraph:
    """Utilitaire pour analyser le graphe de dépendances Epic."""

    def __init__(self, session):
        self.session = session

    def detect_cycles(self, dependencies: List[EpicDependency] = None) -> List[List[int]]:
        """Détecte les cycles dans le graphe de dépendances."""
        if dependencies is None:
            dependencies = self.session.query(EpicDependency).filter(
                EpicDependency.is_active == True
            ).all()

        # Construire le graphe
        graph = {}
        for dep in dependencies:
            if dep.parent_epic_id not in graph:
                graph[dep.parent_epic_id] = []
            graph[dep.parent_epic_id].append(dep.dependent_epic_id)

        # Détection de cycles avec DFS
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs_cycle_detect(node, path):
            if node in rec_stack:
                # Cycle détecté - extraire le cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True

            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if dfs_cycle_detect(neighbor, path):
                    return True

            rec_stack.remove(node)
            path.pop()
            return False

        for node in graph:
            if node not in visited:
                dfs_cycle_detect(node, [])

        return cycles

    def calculate_critical_path(self, epic_ids: List[int] = None) -> Dict[str, any]:
        """Calcule le chemin critique pour les Epics donnés."""
        if epic_ids is None:
            from .epic import Epic
            epics = self.session.query(Epic).all()
            epic_ids = [e.id for e in epics]

        dependencies = self.session.query(EpicDependency).filter(
            EpicDependency.is_active == True,
            EpicDependency.dependency_type.in_([
                DependencyType.BLOCKING.value,
                DependencyType.PREREQUISITE.value
            ])
        ).all()

        # Construire le graphe avec poids
        graph = {}
        weights = {}

        for dep in dependencies:
            if dep.parent_epic_id not in graph:
                graph[dep.parent_epic_id] = []
            graph[dep.parent_epic_id].append(dep.dependent_epic_id)

            # Poids basé sur impact estimé ou criticité
            weight = dep.estimated_impact_days or dep.get_criticality_score()
            weights[(dep.parent_epic_id, dep.dependent_epic_id)] = weight

        # Algorithme de chemin critique (adaptation topologique)
        in_degree = {epic_id: 0 for epic_id in epic_ids}
        for parent in graph:
            for dependent in graph[parent]:
                if dependent in in_degree:
                    in_degree[dependent] += 1

        # Distance la plus longue (chemin critique)
        distances = {epic_id: 0 for epic_id in epic_ids}
        queue = [epic_id for epic_id in epic_ids if in_degree[epic_id] == 0]

        critical_path = []
        max_distance = 0
        critical_end = None

        while queue:
            current = queue.pop(0)

            for neighbor in graph.get(current, []):
                if neighbor in distances:
                    weight = weights.get((current, neighbor), 1)
                    new_distance = distances[current] + weight

                    if new_distance > distances[neighbor]:
                        distances[neighbor] = new_distance

                        if new_distance > max_distance:
                            max_distance = new_distance
                            critical_end = neighbor

                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        # Reconstruire le chemin critique
        if critical_end:
            path = [critical_end]
            current = critical_end

            while distances[current] > 0:
                for parent in graph:
                    if current in graph.get(parent, []):
                        parent_distance = distances[parent]
                        edge_weight = weights.get((parent, current), 1)

                        if parent_distance + edge_weight == distances[current]:
                            path.append(parent)
                            current = parent
                            break

            critical_path = list(reversed(path))

        return {
            "critical_path": critical_path,
            "total_duration": max_distance,
            "distances": distances,
            "bottlenecks": [epic_id for epic_id, dist in distances.items() if dist == max_distance]
        }

    def get_dependency_impact(self, epic_id: int) -> Dict[str, any]:
        """Analyse l'impact des dépendances pour un Epic donné."""
        # Dépendances où l'Epic est parent (bloque d'autres)
        blocking = self.session.query(EpicDependency).filter(
            EpicDependency.parent_epic_id == epic_id,
            EpicDependency.is_active == True
        ).all()

        # Dépendances où l'Epic est dépendant (bloqué par d'autres)
        blocked_by = self.session.query(EpicDependency).filter(
            EpicDependency.dependent_epic_id == epic_id,
            EpicDependency.is_active == True
        ).all()

        return {
            "epic_id": epic_id,
            "blocks_count": len(blocking),
            "blocked_by_count": len(blocked_by),
            "blocking_epics": [dep.dependent_epic_id for dep in blocking if dep.is_blocking()],
            "blocked_by_epics": [dep.parent_epic_id for dep in blocked_by if dep.is_blocking()],
            "critical_dependencies": [
                dep.to_dict() for dep in blocked_by
                if dep.priority in ['critical', 'high'] and not dep.is_resolved
            ],
            "risk_score": len([dep for dep in blocked_by if dep.is_blocking()]) * 2 +
                         len([dep for dep in blocked_by if dep.priority == 'critical'])
        }