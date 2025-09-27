"""
Add Epic Metrics Cache and History Table

Introduces cached metrics columns and a history table so persona dashboards
can reuse precomputed data without recalculating on every request.

Related Issue: US-00071 - Extend Epic model for metrics
Parent Epic: EP-00010 - Multi-persona traceability dashboard
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "add_epic_metrics_cache"
down_revision = "add_epic_metrics_columns"
branch_labels = None
depends_on = None


def upgrade():
    """Apply metric cache changes."""
    print("Adding metrics_cache columns to epics...")
    op.add_column("epics", sa.Column("metrics_cache", sa.Text, nullable=True))
    op.add_column(
        "epics", sa.Column("metrics_cache_updated_at", sa.DateTime, nullable=True)
    )

    print("Creating epic_metric_history table...")
    op.create_table(
        "epic_metric_history",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "epic_id",
            sa.Integer,
            sa.ForeignKey("epics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("captured_at", sa.DateTime, nullable=False),
        sa.Column("metrics", sa.Text, nullable=False),
    )
    op.create_index(
        "ix_epic_metric_history_epic_time",
        "epic_metric_history",
        ["epic_id", "captured_at"],
    )


def downgrade():
    """Revert metric cache changes."""
    print("Dropping epic_metric_history table...")
    op.drop_index("ix_epic_metric_history_epic_time", table_name="epic_metric_history")
    op.drop_table("epic_metric_history")

    print("Removing metrics_cache columns from epics...")
    op.drop_column("epics", "metrics_cache_updated_at")
    op.drop_column("epics", "metrics_cache")
