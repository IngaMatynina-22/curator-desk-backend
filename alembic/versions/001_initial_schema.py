"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-10-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schema is managed via Base.metadata.create_all for desktop init.
    # This revision marks baseline for future Alembic migrations.
    pass


def downgrade() -> None:
    pass
