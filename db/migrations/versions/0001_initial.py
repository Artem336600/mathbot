"""Initial migration — creates all tables.

Tables created:
- users
- topics
- questions
- user_mistakes
- user_progress
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, comment="Telegram user ID"),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("first_name", sa.String(128), nullable=False, server_default=""),
        sa.Column("xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level", sa.String(32), nullable=False, server_default="Новичок"),
        sa.Column("streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_active", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accuracy_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(128), nullable=False, unique=True),
        sa.Column("theory_text", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("topic_id", sa.Integer(), sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(512), nullable=True),
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default="1", comment="1=easy,2=medium,3=hard"),
        sa.Column("option_a", sa.String(256), nullable=False),
        sa.Column("option_b", sa.String(256), nullable=False),
        sa.Column("option_c", sa.String(256), nullable=False),
        sa.Column("option_d", sa.String(256), nullable=False),
        sa.Column("correct_option", sa.String(1), nullable=False, comment="a/b/c/d"),
        sa.Column("explanation", sa.Text(), nullable=True),
    )

    op.create_table(
        "user_mistakes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_fixed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "user_progress",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes for performance
    op.create_index("ix_questions_topic_id_difficulty", "questions", ["topic_id", "difficulty"])
    op.create_index("ix_user_mistakes_user_id", "user_mistakes", ["user_id"])
    op.create_index("ix_user_progress_user_id", "user_progress", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_progress")
    op.drop_table("user_mistakes")
    op.drop_table("questions")
    op.drop_table("topics")
    op.drop_table("users")
