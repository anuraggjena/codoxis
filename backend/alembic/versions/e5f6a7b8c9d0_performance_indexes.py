"""performance indexes on graph tables

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-14

"""
from typing import Sequence, Union

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_files_version_id", "files", ["version_id"])
    op.create_index("ix_edges_version_id", "edges", ["version_id"])
    op.create_index("ix_symbols_version_id", "symbols", ["version_id"])
    op.create_index("ix_metrics_version_id", "metrics", ["version_id"])


def downgrade() -> None:
    op.drop_index("ix_metrics_version_id", table_name="metrics")
    op.drop_index("ix_symbols_version_id", table_name="symbols")
    op.drop_index("ix_edges_version_id", table_name="edges")
    op.drop_index("ix_files_version_id", table_name="files")
