#!/usr/bin/env python3
"""
Database migration script for Program Areas/Capabilities (US-00062)

Adds capabilities and capability_dependencies tables, and capability_id column to epics table.
"""

import sys
import sqlite3
from pathlib import Path

def migrate_capabilities():
    """Migrate database to support Program Areas/Capabilities."""
    # Use the default SQLite database path
    db_path = "./gonogo.db"
    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create capabilities table
        print("Creating capabilities table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capabilities (
                id INTEGER PRIMARY KEY,
                capability_id VARCHAR(20) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                strategic_priority VARCHAR(20) DEFAULT 'medium',
                business_value_theme VARCHAR(100),
                owner VARCHAR(100),
                estimated_business_impact_score REAL DEFAULT 0.0,
                roi_target_percentage REAL DEFAULT 0.0,
                strategic_alignment_score REAL DEFAULT 0.0,
                planned_start_date DATETIME,
                planned_completion_date DATETIME,
                actual_start_date DATETIME,
                actual_completion_date DATETIME,
                status VARCHAR(50) DEFAULT 'planned',
                completion_percentage REAL DEFAULT 0.0,
                estimated_team_size INTEGER DEFAULT 1,
                budget_allocated REAL DEFAULT 0.0,
                budget_consumed REAL DEFAULT 0.0,
                risk_level VARCHAR(20) DEFAULT 'medium',
                risk_notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create capability_dependencies table
        print("Creating capability_dependencies table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capability_dependencies (
                id INTEGER PRIMARY KEY,
                parent_capability_id INTEGER NOT NULL,
                dependent_capability_id INTEGER NOT NULL,
                dependency_type VARCHAR(50) DEFAULT 'strategic',
                priority VARCHAR(20) DEFAULT 'medium',
                rationale TEXT,
                estimated_impact_weeks INTEGER,
                risk_mitigation_notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_resolved BOOLEAN DEFAULT 0,
                resolution_date DATETIME,
                resolution_notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                FOREIGN KEY (parent_capability_id) REFERENCES capabilities (id),
                FOREIGN KEY (dependent_capability_id) REFERENCES capabilities (id)
            )
        """)

        # Add capability_id column to epics table if it doesn't exist
        print("Adding capability_id column to epics table...")
        try:
            cursor.execute("ALTER TABLE epics ADD COLUMN capability_id INTEGER")
            print("Added capability_id column to epics table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("capability_id column already exists in epics table")
            else:
                raise

        # Create indexes for performance
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_capabilities_capability_id ON capabilities (capability_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_capabilities_status ON capabilities (status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_capabilities_priority ON capabilities (strategic_priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_epic_capability ON epics (capability_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_capability_dep_parent ON capability_dependencies (parent_capability_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_capability_dep_dependent ON capability_dependencies (dependent_capability_id)")

        # Commit the changes
        conn.commit()
        print("✅ Migration completed successfully!")

        # Verify the changes
        print("\nVerifying migration...")
        cursor.execute("PRAGMA table_info(capabilities)")
        capabilities_columns = cursor.fetchall()
        print(f"Capabilities table has {len(capabilities_columns)} columns")

        cursor.execute("PRAGMA table_info(capability_dependencies)")
        cap_deps_columns = cursor.fetchall()
        print(f"Capability_dependencies table has {len(cap_deps_columns)} columns")

        cursor.execute("PRAGMA table_info(epics)")
        epic_columns = cursor.fetchall()
        has_capability_id = any(col[1] == 'capability_id' for col in epic_columns)
        print(f"Epics table has capability_id column: {has_capability_id}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

    return True

if __name__ == "__main__":
    success = migrate_capabilities()
    sys.exit(0 if success else 1)