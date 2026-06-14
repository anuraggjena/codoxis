"""initial schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-06-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "project_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("architecture_score", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("loc", sa.Integer(), nullable=True),
        sa.Column("complexity_score", sa.Float(), nullable=True),
        sa.Column("hash", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["version_id"], ["project_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "symbols",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=True),
        sa.Column("end_line", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "metrics",
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("circular_dependencies", sa.Integer(), nullable=True),
        sa.Column("dependency_depth", sa.Integer(), nullable=True),
        sa.Column("avg_complexity", sa.Float(), nullable=True),
        sa.Column("coupling_score", sa.Float(), nullable=True),
        sa.Column("cohesion_score", sa.Float(), nullable=True),
        sa.Column("dead_code_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["version_id"], ["project_versions.id"]),
        sa.PrimaryKeyConstraint("version_id"),
    )

    op.create_table(
        "edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_symbol_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_symbol_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("relation_type", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["source_file_id"], ["files.id"]),
        sa.ForeignKeyConstraint(["source_symbol_id"], ["symbols.id"]),
        sa.ForeignKeyConstraint(["target_file_id"], ["files.id"]),
        sa.ForeignKeyConstraint(["target_symbol_id"], ["symbols.id"]),
        sa.ForeignKeyConstraint(["version_id"], ["project_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("edges")
    op.drop_table("metrics")
    op.drop_table("symbols")
    op.drop_table("files")
    op.drop_table("project_versions")
    op.drop_table("projects")
    op.drop_table("users")
