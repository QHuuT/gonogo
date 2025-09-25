#!/usr/bin/env python3
"""
Script pour ajouter les colonnes de métriques Epic directement via SQLAlchemy.
Alternative à Alembic pour le développement rapide.

Related Issue: US-00071 - Extension modèle Epic pour métriques
Parent Epic: EP-00010 - Dashboard de Traçabilité Multi-Persona
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from be.database import engine
from be.models.traceability.epic import Epic
from be.models.traceability.base import Base
from sqlalchemy import inspect, text

def add_epic_metrics_columns():
    """Ajouter les colonnes de métriques Epic si elles n'existent pas."""

    print("Epic Metrics Columns Addition")
    print("=" * 50)

    # Vérifier les colonnes existantes
    inspector = inspect(engine)

    try:
        columns = inspector.get_columns('epics')
        existing_columns = [col['name'] for col in columns]

        # Colonnes de métriques attendues
        expected_metrics_columns = [
            'estimated_duration_days', 'actual_duration_days',
            'planned_start_date', 'actual_start_date', 'planned_end_date', 'actual_end_date',
            'initial_scope_estimate', 'scope_creep_percentage', 'velocity_points_per_sprint', 'team_size',
            'defect_density', 'test_coverage_percentage', 'code_review_score', 'technical_debt_hours',
            'stakeholder_satisfaction_score', 'business_impact_score', 'roi_percentage', 'user_adoption_rate',
            'last_metrics_update', 'metrics_calculation_frequency'
        ]

        missing_columns = [col for col in expected_metrics_columns if col not in existing_columns]

        if not missing_columns:
            print("[OK] All Epic metrics columns already exist")
            return True

        print(f"Adding {len(missing_columns)} missing metrics columns...")

        # Utiliser ALTER TABLE pour ajouter les colonnes manquantes
        print("Adding missing columns to epics table...")

        column_definitions = {
            'estimated_duration_days': 'INTEGER',
            'actual_duration_days': 'INTEGER',
            'planned_start_date': 'DATETIME',
            'actual_start_date': 'DATETIME',
            'planned_end_date': 'DATETIME',
            'actual_end_date': 'DATETIME',
            'initial_scope_estimate': 'INTEGER NOT NULL DEFAULT 0',
            'scope_creep_percentage': 'REAL NOT NULL DEFAULT 0.0',
            'velocity_points_per_sprint': 'REAL NOT NULL DEFAULT 0.0',
            'team_size': 'INTEGER NOT NULL DEFAULT 1',
            'defect_density': 'REAL NOT NULL DEFAULT 0.0',
            'test_coverage_percentage': 'REAL NOT NULL DEFAULT 0.0',
            'code_review_score': 'REAL NOT NULL DEFAULT 0.0',
            'technical_debt_hours': 'INTEGER NOT NULL DEFAULT 0',
            'stakeholder_satisfaction_score': 'REAL NOT NULL DEFAULT 0.0',
            'business_impact_score': 'REAL NOT NULL DEFAULT 0.0',
            'roi_percentage': 'REAL NOT NULL DEFAULT 0.0',
            'user_adoption_rate': 'REAL NOT NULL DEFAULT 0.0',
            'last_metrics_update': 'DATETIME',
            'metrics_calculation_frequency': 'VARCHAR(20) NOT NULL DEFAULT "daily"'
        }

        with engine.connect() as conn:
            for column_name in missing_columns:
                column_def = column_definitions.get(column_name)
                if column_def:
                    alter_sql = f"ALTER TABLE epics ADD COLUMN {column_name} {column_def}"
                    print(f"  Adding column: {column_name}")
                    conn.execute(text(alter_sql))
            conn.commit()

        # Vérifier si les colonnes ont été ajoutées
        inspector = inspect(engine)
        updated_columns = inspector.get_columns('epics')
        updated_column_names = [col['name'] for col in updated_columns]

        still_missing = [col for col in expected_metrics_columns if col not in updated_column_names]

        if not still_missing:
            print(f"[OK] Successfully added {len(missing_columns)} metrics columns")

            # Afficher les colonnes métriques
            metrics_columns = [col for col in updated_columns if col['name'] in expected_metrics_columns]
            print(f"\nMetrics columns ({len(metrics_columns)}):")
            for col in metrics_columns:
                print(f"  - {col['name']}: {col['type']}")

            # Populate initial scope estimate
            print("\nPopulating initial scope estimates...")
            with engine.connect() as conn:
                result = conn.execute(text("""
                    UPDATE epics
                    SET initial_scope_estimate = total_story_points
                    WHERE initial_scope_estimate = 0 OR initial_scope_estimate IS NULL
                """))
                conn.commit()
                print(f"[OK] Updated {result.rowcount} epics with initial scope estimates")

        else:
            print(f"[ERROR] Still missing columns: {still_missing}")
            return False

    except Exception as e:
        print(f"[ERROR] Error adding metrics columns: {e}")
        return False

    return True

def test_epic_metrics():
    """Tester les nouvelles métriques sur un Epic existant."""
    from be.database import get_db_session

    print("\nTesting Epic metrics functionality...")

    session = get_db_session()
    try:
        # Récupérer le premier Epic
        epic = session.query(Epic).first()

        if not epic:
            print("[ERROR] No epics found to test metrics")
            return

        print(f"Testing metrics on Epic: {epic.epic_id} - {epic.title}")

        # Test basic metrics calculation
        all_metrics = epic.calculate_all_metrics()
        print(f"[OK] Calculated {len(all_metrics)} metric categories")

        # Test persona-specific metrics
        for persona in ['PM', 'PO', 'QA']:
            persona_metrics = epic.get_persona_specific_metrics(persona)
            print(f"[OK] {persona} persona metrics: {len(persona_metrics)} categories")

        # Test metrics update
        epic.update_metrics(force_recalculate=True)
        print(f"[OK] Metrics updated at: {epic.last_metrics_update}")

        session.commit()

        print("\n[OK] All Epic metrics functionality working correctly!")

    except Exception as e:
        print(f"[ERROR] Error testing metrics: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    success = add_epic_metrics_columns()

    if success:
        test_epic_metrics()

        print(f"\n" + "=" * 50)
        print("Epic Metrics Extension Complete!")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Test the new metrics API endpoints:")
        print("   - GET /api/rtm/epics/{epic_id}/metrics")
        print("   - GET /api/rtm/epics/{epic_id}/metrics?persona=PM")
        print("   - GET /api/rtm/dashboard/metrics?persona=PO")
        print("2. Access FastAPI docs: http://localhost:8000/docs")
        print("3. Multi-persona dashboard endpoints are ready!")
    else:
        print("\n[ERROR] Metrics columns addition failed")
        sys.exit(1)