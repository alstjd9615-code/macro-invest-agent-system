"""Draft Alembic migration: create feature_snapshots table.

Revision ID: 0001_feature_store_initial
Revises: (none — first migration)
Create Date: 2026-04-13

This is an **initial schema draft** for the feature-store tables.  It is not
yet wired to a live database or Alembic environment.  The migration is
recorded here to:

1. Document the intended persistent schema alongside the in-memory reference
   implementation in ``adapters/repositories/in_memory_feature_store.py``.
2. Provide a ready-to-activate migration once a database connection is
   configured (SQLAlchemy + psycopg3, as declared in ``pyproject.toml``).
3. Serve as the authoritative schema reference when extending
   ``FeatureSnapshot`` with new fields.

----------------------------------------------------------------------
Schema overview
----------------------------------------------------------------------

feature_snapshots
    snapshot_id         TEXT PRIMARY KEY        UUID4 string
    country             TEXT NOT NULL           ISO 3166-1 alpha-2
    source_id           TEXT NOT NULL           Data source identifier
    ingested_at         TIMESTAMPTZ NOT NULL    UTC ingestion timestamp
    features_count      INTEGER NOT NULL >= 0   Derived feature count
    features_json       JSONB NOT NULL          Serialised MacroFeature list

----------------------------------------------------------------------
Activation instructions (once a database is configured)
----------------------------------------------------------------------

    1. Set DATABASE_URL in the environment (or .env).
    2. Run:  alembic upgrade head
    3. Verify:  alembic current

"""

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# upgrade / downgrade stubs
# ---------------------------------------------------------------------------
# These are intentionally left as stubs.  Activate by importing alembic.op
# and implementing the table creation and drop operations.
#
# Example upgrade body:
#
#   import alembic.op as op
#   import sqlalchemy as sa
#
#   def upgrade() -> None:
#       op.create_table(
#           "feature_snapshots",
#           sa.Column("snapshot_id", sa.Text(), nullable=False),
#           sa.Column("country", sa.Text(), nullable=False),
#           sa.Column("source_id", sa.Text(), nullable=False),
#           sa.Column(
#               "ingested_at",
#               sa.DateTime(timezone=True),
#               nullable=False,
#               server_default=sa.text("NOW()"),
#           ),
#           sa.Column("features_count", sa.Integer(), nullable=False, server_default="0"),
#           sa.Column("features_json", sa.JSON(), nullable=False),
#           sa.PrimaryKeyConstraint("snapshot_id"),
#       )
#       op.create_index(
#           "ix_feature_snapshots_country_ingested_at",
#           "feature_snapshots",
#           ["country", "ingested_at"],
#       )
#
#   def downgrade() -> None:
#       op.drop_index("ix_feature_snapshots_country_ingested_at")
#       op.drop_table("feature_snapshots")


def upgrade() -> None:
    """Stub: create the feature_snapshots table."""
    # Activate by uncommenting the example above and importing alembic.op.
    pass


def downgrade() -> None:
    """Stub: drop the feature_snapshots table."""
    # Activate by uncommenting the example above and importing alembic.op.
    pass
