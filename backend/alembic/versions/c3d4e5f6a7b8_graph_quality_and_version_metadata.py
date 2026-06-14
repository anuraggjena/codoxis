"""graph quality and version metadata

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("project_versions", sa.Column("graph_quality_json", sa.JSON(), nullable=True))
    op.add_column("project_versions", sa.Column("commit_sha", sa.String(), nullable=True))
    op.add_column("project_versions", sa.Column("commit_message", sa.String(), nullable=True))
    op.add_column("project_versions", sa.Column("source_type", sa.String(), nullable=True))
    op.add_column("project_versions", sa.Column("ingestion_status", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("project_versions", "ingestion_status")
    op.drop_column("project_versions", "source_type")
    op.drop_column("project_versions", "commit_message")
    op.drop_column("project_versions", "commit_sha")
    op.drop_column("project_versions", "graph_quality_json")
