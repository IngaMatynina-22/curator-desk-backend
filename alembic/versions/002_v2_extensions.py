"""v2 extensions: periods, notifications, settings, import_jobs, event recurrence

Revision ID: 002
Revises: 001
Create Date: 2026-10-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Desktop app uses create_all; this revision documents schema for Alembic users.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "academic_periods" not in tables:
        op.create_table(
            "academic_periods",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("academic_year", sa.String(32), nullable=False),
            sa.Column("kind", sa.String(32), nullable=False),
            sa.Column("starts_on", sa.Date(), nullable=False),
            sa.Column("ends_on", sa.Date(), nullable=False),
            sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    if "notifications" not in tables:
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("kind", sa.String(64), nullable=False),
            sa.Column("source_type", sa.String(64), nullable=False),
            sa.Column("source_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("due_at", sa.DateTime(), nullable=True),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("snoozed_until", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("kind", "source_type", "source_id", name="uq_notification_source"),
        )

    if "app_settings" not in tables:
        op.create_table(
            "app_settings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("key", sa.String(128), nullable=False, unique=True),
            sa.Column("value_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    if "import_jobs" not in tables:
        op.create_table(
            "import_jobs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("source_path", sa.String(512), nullable=False),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("group_id", sa.Integer(), nullable=True),
            sa.Column("report_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    if "events" in tables:
        cols = {c["name"] for c in inspector.get_columns("events")}
        if "recurrence_group_id" not in cols:
            with op.batch_alter_table("events") as batch:
                batch.add_column(sa.Column("recurrence_group_id", sa.String(64), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "events" in tables:
        cols = {c["name"] for c in inspector.get_columns("events")}
        if "recurrence_group_id" in cols:
            with op.batch_alter_table("events") as batch:
                batch.drop_column("recurrence_group_id")
    for name in ("import_jobs", "app_settings", "notifications", "academic_periods"):
        if name in tables:
            op.drop_table(name)
