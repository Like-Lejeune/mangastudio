"""avis des utilisateurs

Révision : 0004
Précédente : 0003
Créée le : 2026-11-21
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "testimonials",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("episode_id", sa.String(length=32), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=60), nullable=False),
        sa.Column("role", sa.String(length=80), nullable=False),
        sa.Column("consent", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    with op.batch_alter_table("testimonials", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_testimonials_status"), ["status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("testimonials", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_testimonials_status"))
    op.drop_table("testimonials")
