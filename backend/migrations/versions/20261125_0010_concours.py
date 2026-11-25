"""concours : contests et contest_entries

Révision : 0010
Précédente : 0009
Créée le : 2026-11-25
"""
import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contests",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("theme", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rules", sa.Text(), nullable=False),
        sa.Column("style", sa.String(length=20), nullable=False),
        sa.Column("new_only", sa.Boolean(), nullable=False),
        sa.Column("max_entries", sa.Integer(), nullable=False),
        sa.Column("prizes", sa.JSON(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("results_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "contest_entries",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("contest_id", sa.String(length=32), nullable=False),
        sa.Column("publication_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("jury_score", sa.Float(), nullable=True),
        sa.Column("likes", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("prize", sa.String(length=200), nullable=False),
        sa.Column("disqualified", sa.String(length=300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["contest_id"], ["contests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["publication_id"], ["publications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contest_id", "publication_id"),
    )
    with op.batch_alter_table("contest_entries", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_contest_entries_contest_id"), ["contest_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_contest_entries_publication_id"), ["publication_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_contest_entries_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("contest_entries", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_contest_entries_user_id"))
        batch_op.drop_index(batch_op.f("ix_contest_entries_publication_id"))
        batch_op.drop_index(batch_op.f("ix_contest_entries_contest_id"))
    op.drop_table("contest_entries")
    op.drop_table("contests")
