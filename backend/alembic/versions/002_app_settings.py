"""Add app_settings table for backup configuration

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import JSON

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the app_settings table for storing application configuration.
    
    Uses JSONB on PostgreSQL and JSON on SQLite for the value column,
    matching the pattern established in 001_initial_schema.py.
    """
    # Get the current dialect
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Use the appropriate JSON type based on dialect
    if dialect_name == "postgresql":
        value_type = JSONB()
    else:
        # SQLite and other dialects use JSON
        value_type = JSON()
    
    op.create_table(
        "app_settings",
        sa.Column(
            "key",
            sa.String(100),
            primary_key=True,
        ),
        sa.Column(
            "value",
            value_type,
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove the app_settings table."""
    op.drop_table("app_settings")
