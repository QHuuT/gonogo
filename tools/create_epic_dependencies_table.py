#!/usr/bin/env python3
"""
Script pour créer la table epic_dependencies directement via SQLAlchemy.
Alternative à Alembic pour le développement rapide.

Related Issue: US-00070 - Modèle dépendances fonctionnelles Epic
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from be.database import engine, create_tables
from be.models.traceability.epic_dependency import EpicDependency
from be.models.traceability.epic import Epic
from be.models.traceability.base import Base
from sqlalchemy import inspect

def create_epic_dependencies_table():
    """Créer la table epic_dependencies si elle n'existe pas."""

    print("Epic Dependencies Table Creation")
    print("=" * 50)

    # Vérifier si la table existe déjà
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if 'epic_dependencies' in existing_tables:
        print("[OK] Table 'epic_dependencies' already exists")
        return True

    try:
        # Créer toutes les tables (y compris epic_dependencies)
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)

        # Vérifier la création
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if 'epic_dependencies' in existing_tables:
            print("[OK] Table 'epic_dependencies' created successfully")

            # Afficher les colonnes créées
            columns = inspector.get_columns('epic_dependencies')
            print(f"\nColumns created ({len(columns)}):")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")

            # Afficher les index créés
            indexes = inspector.get_indexes('epic_dependencies')
            print(f"\nIndexes created ({len(indexes)}):")
            for idx in indexes:
                print(f"  - {idx['name']}: {idx['column_names']}")

        else:
            print("[ERROR] Failed to create table 'epic_dependencies'")

    except Exception as e:
        print(f"[ERROR] Error creating table: {e}")
        return False

    return True

def create_sample_dependencies():
    """Créer quelques dépendances d'exemple."""
    from be.database import get_db_session

    print("\nCreating sample dependencies...")

    session = get_db_session()
    try:
        # Récupérer les premiers Epics
        epics = session.query(Epic).limit(4).all()

        if len(epics) < 2:
            print("[ERROR] Need at least 2 Epics to create sample dependencies")
            return

        print(f"Found {len(epics)} epics for sample dependencies")

        # Créer des exemples de dépendances
        sample_deps = []

        if len(epics) >= 2:
            dep1 = EpicDependency(
                parent_epic_id=epics[0].id,
                dependent_epic_id=epics[1].id,
                dependency_type="prerequisite",
                priority="high",
                reason=f"Epic '{epics[1].title}' requires infrastructure from '{epics[0].title}'",
                estimated_impact_days=3,
                title=f"Prerequisite: {epics[0].epic_id} -> {epics[1].epic_id}",
                description="Sample prerequisite dependency"
            )
            sample_deps.append(dep1)

        if len(epics) >= 3:
            dep2 = EpicDependency(
                parent_epic_id=epics[1].id,
                dependent_epic_id=epics[2].id,
                dependency_type="blocking",
                priority="critical",
                reason=f"Epic '{epics[2].title}' cannot start until '{epics[1].title}' is completed",
                estimated_impact_days=5,
                title=f"Blocking: {epics[1].epic_id} -> {epics[2].epic_id}",
                description="Critical blocking dependency"
            )
            sample_deps.append(dep2)

        if len(epics) >= 4:
            dep3 = EpicDependency(
                parent_epic_id=epics[0].id,
                dependent_epic_id=epics[3].id,
                dependency_type="technical",
                priority="medium",
                reason=f"Epic '{epics[3].title}' shares technical components with '{epics[0].title}'",
                estimated_impact_days=2,
                title=f"Technical: {epics[0].epic_id} -> {epics[3].epic_id}",
                description="Technical infrastructure dependency"
            )
            sample_deps.append(dep3)

        # Insérer les dépendances
        for dep in sample_deps:
            session.add(dep)

        session.commit()
        print(f"[OK] Created {len(sample_deps)} sample dependencies")

        # Afficher les dépendances créées
        print("\nSample dependencies created:")
        for dep in sample_deps:
            print(f"  - {dep.title}: {dep.dependency_type} ({dep.priority})")

    except Exception as e:
        print(f"[ERROR] Error creating sample dependencies: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    success = create_epic_dependencies_table()

    if success:
        create_sample_dependencies()

        print(f"\n" + "=" * 50)
        print("Epic Dependencies Table Setup Complete!")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Test the API endpoints at: http://localhost:8000/docs")
        print("2. View dependencies: GET /api/epic-dependencies/")
        print("3. Check critical path: GET /api/epic-dependencies/analysis/critical-path")
        print("4. Detect cycles: GET /api/epic-dependencies/analysis/cycles")
    else:
        print("\n[ERROR] Table creation failed")
        sys.exit(1)