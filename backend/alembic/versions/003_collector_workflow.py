"""collector-workflow: country_of_origin, collection_catalogs, maintenance, pending

Revision ID: 003
Revises: 002
Create Date: 2026-09-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "collection_items",
        sa.Column("country_of_origin", sa.String(length=2), nullable=True),
    )

    op.create_table(
        "collection_catalogs",
        sa.Column("collection_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("catalog_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["catalog_id"], ["catalogs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("collection_id", "catalog_id"),
    )
    op.create_index(
        "idx_collection_catalogs_catalog", "collection_catalogs", ["catalog_id"]
    )

    op.create_table(
        "maintenance_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("collection_item_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("maintenance_type", sa.String(length=50), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_done", sa.Boolean(), server_default=sa.false(), nullable=True),
        sa.Column("done_date", sa.Date(), nullable=True),
        sa.Column("done_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_item_id"], ["collection_items.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_maintenance_item", "maintenance_schedules", ["collection_item_id"]
    )
    op.create_index("idx_maintenance_due", "maintenance_schedules", ["due_date"])

    op.create_table(
        "pending_completions",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("entity_type", sa.String(length=30), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "missing_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_pending_status_type",
        "pending_completions",
        ["status", "entity_type"],
    )


def downgrade() -> None:
    op.drop_index("idx_pending_status_type", table_name="pending_completions")
    op.drop_table("pending_completions")
    op.drop_index("idx_maintenance_due", table_name="maintenance_schedules")
    op.drop_index("idx_maintenance_item", table_name="maintenance_schedules")
    op.drop_table("maintenance_schedules")
    op.drop_index("idx_collection_catalogs_catalog", table_name="collection_catalogs")
    op.drop_table("collection_catalogs")
    op.drop_column("collection_items", "country_of_origin")
