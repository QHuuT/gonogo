"""Add Advanced Epic Metrics Columns

Migration pour ajouter les colonnes de métriques avancées à la table epics.

Related Issue: US-00071 - Extension modèle Epic pour métriques
Parent Epic: EP-00010 - Dashboard de Traçabilité Multi-Persona

Revision ID: add_epic_metrics_columns
Create Date: 2025-09-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers
revision = 'add_epic_metrics_columns'
down_revision = 'add_epic_dependencies'  # After the dependencies migration
branch_labels = None
depends_on = None


def upgrade():
    """Ajouter les colonnes de métriques avancées à la table epics."""

    print("Adding advanced metrics columns to epics table...")

    # Timeline metrics columns
    op.add_column('epics', sa.Column('estimated_duration_days', sa.Integer, nullable=True))
    op.add_column('epics', sa.Column('actual_duration_days', sa.Integer, nullable=True))
    op.add_column('epics', sa.Column('planned_start_date', sa.DateTime, nullable=True))
    op.add_column('epics', sa.Column('actual_start_date', sa.DateTime, nullable=True))
    op.add_column('epics', sa.Column('planned_end_date', sa.DateTime, nullable=True))
    op.add_column('epics', sa.Column('actual_end_date', sa.DateTime, nullable=True))
    print("✓ Timeline metrics columns added")

    # Velocity and productivity metrics columns
    op.add_column('epics', sa.Column('initial_scope_estimate', sa.Integer, nullable=False, server_default='0'))
    op.add_column('epics', sa.Column('scope_creep_percentage', sa.Float, nullable=False, server_default='0.0'))
    op.add_column('epics', sa.Column('velocity_points_per_sprint', sa.Float, nullable=False, server_default='0.0'))
    op.add_column('epics', sa.Column('team_size', sa.Integer, nullable=False, server_default='1'))
    print("✓ Velocity and productivity metrics columns added")

    # Quality metrics columns
    op.add_column('epics', sa.Column('defect_density', sa.Float, nullable=False, server_default='0.0'))
    op.add_column('epics', sa.Column('test_coverage_percentage', sa.Float, nullable=False, server_default='0.0'))
    op.add_column('epics', sa.Column('code_review_score', sa.Float, nullable=False, server_default='0.0'))
    op.add_column('epics', sa.Column('technical_debt_hours', sa.Integer, nullable=False, server_default='0'))
    print("✓ Quality metrics columns added")

    # Stakeholder and business metrics columns
    op.add_column('epics', sa.Column('stakeholder_satisfaction_score', sa.Float, nullable=False, server_default='0.0'))
    op.add_column('epics', sa.Column('business_impact_score', sa.Float, nullable=False, server_default='0.0'))
    op.add_column('epics', sa.Column('roi_percentage', sa.Float, nullable=False, server_default='0.0'))
    op.add_column('epics', sa.Column('user_adoption_rate', sa.Float, nullable=False, server_default='0.0'))
    print("✓ Business metrics columns added")

    # Tracking and history columns
    op.add_column('epics', sa.Column('last_metrics_update', sa.DateTime, nullable=True))
    op.add_column('epics', sa.Column('metrics_calculation_frequency', sa.String(20), nullable=False, server_default="'daily'"))
    print("✓ Metrics tracking columns added")

    # Create indexes for performance
    print("Creating performance indexes...")
    op.create_index('idx_epic_timeline', 'epics', ['planned_start_date', 'planned_end_date'])
    op.create_index('idx_epic_velocity', 'epics', ['velocity_points_per_sprint', 'completion_percentage'])
    op.create_index('idx_epic_quality', 'epics', ['defect_density', 'test_coverage_percentage'])
    op.create_index('idx_epic_business_impact', 'epics', ['business_impact_score', 'roi_percentage'])
    op.create_index('idx_epic_metrics_update', 'epics', ['last_metrics_update'])
    print("✓ Performance indexes created")

    # Populate initial_scope_estimate with current total_story_points for existing epics
    print("Populating initial scope estimates...")
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE epics
        SET initial_scope_estimate = total_story_points
        WHERE initial_scope_estimate = 0
    """))
    print("✓ Initial scope estimates populated")

    print("Epic metrics columns migration completed successfully!")


def downgrade():
    """Supprimer les colonnes de métriques avancées de la table epics."""

    print("Removing advanced metrics columns from epics table...")

    # Drop indexes first
    op.drop_index('idx_epic_metrics_update', 'epics')
    op.drop_index('idx_epic_business_impact', 'epics')
    op.drop_index('idx_epic_quality', 'epics')
    op.drop_index('idx_epic_velocity', 'epics')
    op.drop_index('idx_epic_timeline', 'epics')
    print("✓ Indexes dropped")

    # Drop tracking columns
    op.drop_column('epics', 'metrics_calculation_frequency')
    op.drop_column('epics', 'last_metrics_update')

    # Drop business metrics columns
    op.drop_column('epics', 'user_adoption_rate')
    op.drop_column('epics', 'roi_percentage')
    op.drop_column('epics', 'business_impact_score')
    op.drop_column('epics', 'stakeholder_satisfaction_score')

    # Drop quality metrics columns
    op.drop_column('epics', 'technical_debt_hours')
    op.drop_column('epics', 'code_review_score')
    op.drop_column('epics', 'test_coverage_percentage')
    op.drop_column('epics', 'defect_density')

    # Drop velocity columns
    op.drop_column('epics', 'team_size')
    op.drop_column('epics', 'velocity_points_per_sprint')
    op.drop_column('epics', 'scope_creep_percentage')
    op.drop_column('epics', 'initial_scope_estimate')

    # Drop timeline columns
    op.drop_column('epics', 'actual_end_date')
    op.drop_column('epics', 'planned_end_date')
    op.drop_column('epics', 'actual_start_date')
    op.drop_column('epics', 'planned_start_date')
    op.drop_column('epics', 'actual_duration_days')
    op.drop_column('epics', 'estimated_duration_days')

    print("Advanced metrics columns removed successfully!")


if __name__ == '__main__':
    """Script pour exécuter la migration manuellement."""
    print("Manual execution of epic metrics columns migration")
    print("This would normally be run via Alembic")
    print("To apply: alembic upgrade head")
    print("To rollback: alembic downgrade -1")