"""Initial ideation tables

Revision ID: 001_initial
Revises:
Create Date: 2026-01-31 00:00:00.000000

This migration creates the initial database schema for the Ideation Studio
persistence layer, including:
- ideation_sessions: Core session table
- ideation_messages: Chat messages
- ideation_requirements: Extracted requirements
- ideation_maturity: Maturity state (one-to-one with sessions)
- ideation_prd_drafts: PRD drafts
- ideation_user_stories: User stories

All tables use TIMESTAMPTZ for timezone-aware timestamps and include
appropriate indexes for query performance.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all ideation tables and indexes."""
    # Create ideation_sessions table
    op.create_table(
        "ideation_sessions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("project_name", sa.String(255), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), server_default="draft"),
        sa.Column("data_source", sa.String(32), server_default="mock"),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("idx_sessions_user_id", "ideation_sessions", ["user_id"])
    op.create_index("idx_sessions_updated_at", "ideation_sessions", ["updated_at"])

    # Create ideation_messages table
    op.create_table(
        "ideation_messages",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("ideation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "timestamp",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("maturity_delta", sa.Integer, server_default="0"),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
    )
    op.create_index("idx_messages_session_id", "ideation_messages", ["session_id"])
    op.create_index("idx_messages_timestamp", "ideation_messages", ["timestamp"])

    # Create ideation_requirements table
    op.create_table(
        "ideation_requirements",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("ideation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("priority", sa.String(32), nullable=False),
        sa.Column("category_id", sa.String(32), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "idx_requirements_session_id", "ideation_requirements", ["session_id"]
    )

    # Create ideation_maturity table (one-to-one with sessions)
    op.create_table(
        "ideation_maturity",
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("ideation_sessions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("level", sa.String(32), nullable=False),
        sa.Column("categories", postgresql.JSONB, nullable=False),
        sa.Column("can_submit", sa.Boolean, server_default="false"),
        sa.Column("gaps", postgresql.JSONB, nullable=True),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Create ideation_prd_drafts table
    op.create_table(
        "ideation_prd_drafts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("ideation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("sections", postgresql.JSONB, nullable=False),
        sa.Column("status", sa.String(32), server_default="draft"),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("idx_prd_drafts_session_id", "ideation_prd_drafts", ["session_id"])

    # Create ideation_user_stories table
    op.create_table(
        "ideation_user_stories",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(64),
            sa.ForeignKey("ideation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("as_a", sa.Text, nullable=False),
        sa.Column("i_want", sa.Text, nullable=False),
        sa.Column("so_that", sa.Text, nullable=False),
        sa.Column("acceptance_criteria", postgresql.JSONB, nullable=False),
        sa.Column("linked_requirements", postgresql.JSONB, nullable=True),
        sa.Column("priority", sa.String(32), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "idx_user_stories_session_id", "ideation_user_stories", ["session_id"]
    )


def downgrade() -> None:
    """Drop all ideation tables and indexes."""
    # Drop tables in reverse order (children first)
    op.drop_table("ideation_user_stories")
    op.drop_table("ideation_prd_drafts")
    op.drop_table("ideation_maturity")
    op.drop_table("ideation_requirements")
    op.drop_table("ideation_messages")
    op.drop_table("ideation_sessions")
