"""Add Epic Dependencies Table

Migration pour ajouter la table epic_dependencies et les relations associées.

Related Issue: US-00070 - Modèle dépendances fonctionnelles Epic
Parent Epic: EP-00010 - Dashboard de Traçabilité Multi-Persona

Revision ID: add_epic_dependencies
Create Date: 2025-09-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers
revision = 'add_epic_dependencies'
down_revision = None  # Premier migration pour cette fonctionnalité
branch_labels = None
depends_on = None


def upgrade():
    """Ajouter la table epic_dependencies et les relations."""

    # Créer la table epic_dependencies
    op.create_table(
        'epic_dependencies',

        # Colonnes héritées de TraceabilityBase
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            'title', sa.String(255), nullable=True
        ),  # Peut être NULL pour les dépendances
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('target_release_version', sa.String(50), nullable=True),
        sa.Column(
            'created_at', sa.DateTime, nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),
        sa.Column(
            'updated_at', sa.DateTime, nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),

        # Colonnes spécifiques aux dépendances Epic
        sa.Column(
            'parent_epic_id', sa.Integer,
            sa.ForeignKey('epics.id'), nullable=False
        ),
        sa.Column(
            'dependent_epic_id', sa.Integer,
            sa.ForeignKey('epics.id'), nullable=False
        ),

        # Type et priorité
        sa.Column(
            'dependency_type', sa.String(20),
            nullable=False, default='prerequisite'
        ),
        sa.Column('priority', sa.String(10), nullable=False, default='medium'),

        # Métadonnées
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('estimated_impact_days', sa.Integer, nullable=True),

        # État
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('is_resolved', sa.Boolean, nullable=False, default=False),
        sa.Column('resolution_date', sa.DateTime, nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),

        # Tracking
        sa.Column(
            'created_by_system', sa.Boolean,
            nullable=False, default=False
        ),
        sa.Column('last_validation_date', sa.DateTime, nullable=True),
        sa.Column(
            'validation_status', sa.String(20),
            nullable=False, default='pending'
        ),

        # Contraintes
        sa.UniqueConstraint(
            'parent_epic_id', 'dependent_epic_id', 'dependency_type',
            name='uq_epic_dependency'
        ),
        sa.CheckConstraint(
            'parent_epic_id != dependent_epic_id',
            name='no_self_dependency'
        ),
    )

    # Créer les index pour la performance
    op.create_index(
        'idx_epic_dep_parent', 'epic_dependencies', ['parent_epic_id']
    )
    op.create_index(
        'idx_epic_dep_dependent', 'epic_dependencies', ['dependent_epic_id']
    )
    op.create_index(
        'idx_epic_dep_type_priority', 'epic_dependencies',
        ['dependency_type', 'priority']
    )
    op.create_index(
        'idx_epic_dep_active', 'epic_dependencies',
        ['is_active', 'is_resolved']
    )
    op.create_index(
        'idx_epic_dep_validation', 'epic_dependencies',
        ['validation_status', 'last_validation_date']
    )

    # Insérer quelques exemples de dépendances pour démonstration
    # (Optionnel - peut être retiré en production)
    insert_sample_dependencies()


def downgrade():
    """Supprimer la table epic_dependencies."""

    # Supprimer les index
    op.drop_index('idx_epic_dep_validation', 'epic_dependencies')
    op.drop_index('idx_epic_dep_active', 'epic_dependencies')
    op.drop_index('idx_epic_dep_type_priority', 'epic_dependencies')
    op.drop_index('idx_epic_dep_dependent', 'epic_dependencies')
    op.drop_index('idx_epic_dep_parent', 'epic_dependencies')

    # Supprimer la table
    op.drop_table('epic_dependencies')


def insert_sample_dependencies():
    """Insérer des exemples de dépendances pour démonstration."""

    # Récupérer les IDs des Epics existants
    connection = op.get_bind()

    # Vérifier s'il y a des Epics dans la base
    epics_result = connection.execute(
        text("SELECT id, epic_id FROM epics ORDER BY id LIMIT 5")
    )
    epics = epics_result.fetchall()

    if len(epics) >= 2:
        print(f"Creating sample dependencies for {len(epics)} epics...")

        sample_dependencies = [
            {
                'parent_epic_id': epics[0][0],
                'dependent_epic_id': epics[1][0],
                'dependency_type': 'prerequisite',
                'priority': 'high',
                'reason': (
                    f'Epic {epics[1][1]} requires infrastructure '
                    f'from Epic {epics[0][1]}'
                ),
                'estimated_impact_days': 3,
                'title': f'Dependency: {epics[0][1]} -> {epics[1][1]}',
                'description': 'Sample dependency created by migration'
            }
        ]

        # Ajouter plus de dépendances si on a plus d'Epics
        if len(epics) >= 3:
            sample_dependencies.append({
                'parent_epic_id': epics[1][0],
                'dependent_epic_id': epics[2][0],
                'dependency_type': 'blocking',
                'priority': 'critical',
                'reason': (
                    f'Epic {epics[2][1]} cannot start until '
                    f'Epic {epics[1][1]} is completed'
                ),
                'estimated_impact_days': 5,
                'title': f'Dependency: {epics[1][1]} -> {epics[2][1]}',
                'description': 'Critical blocking dependency'
            })

        if len(epics) >= 4:
            sample_dependencies.append({
                'parent_epic_id': epics[0][0],
                'dependent_epic_id': epics[3][0],
                'dependency_type': 'technical',
                'priority': 'medium',
                'reason': (
                    f'Epic {epics[3][1]} shares technical components '
                    f'with Epic {epics[0][1]}'
                ),
                'estimated_impact_days': 2,
                'title': (
                    f'Technical Dependency: {epics[0][1]} -> {epics[3][1]}'
                ),
                'description': 'Technical infrastructure dependency'
            })

        # Insérer les dépendances d'exemple
        for dep in sample_dependencies:
            insert_query = text("""
                INSERT INTO epic_dependencies
                (title, description, parent_epic_id, dependent_epic_id,
                 dependency_type, priority, reason, estimated_impact_days)
                VALUES
                (:title, :description, :parent_epic_id, :dependent_epic_id,
                 :dependency_type, :priority, :reason, :estimated_impact_days)
            """)
            connection.execute(insert_query, dep)

        print(f"Inserted {len(sample_dependencies)} sample dependencies")
    else:
        print("No existing epics found - skipping sample dependency creation")


if __name__ == '__main__':
    """Script pour exécuter la migration manuellement."""
    print("Manual execution of epic dependencies migration")
    print("This would normally be run via Alembic")
    print("To apply: alembic upgrade head")
    print("To rollback: alembic downgrade -1")