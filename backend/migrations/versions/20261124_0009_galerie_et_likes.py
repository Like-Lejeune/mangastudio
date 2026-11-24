"""galerie publique : publications et likes

Révision : 0009
Précédente : 0008
Créée le : 2026-11-24
"""
import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "publications",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("episode_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=False),
        sa.Column("featured", sa.Boolean(), nullable=False),
        sa.Column("likes", sa.Integer(), nullable=False),
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("episode_id"),
    )
    with op.batch_alter_table("publications", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_publications_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_publications_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_publications_published_at"), ["published_at"], unique=False)
    op.create_table(
        "likes",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("publication_id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["publication_id"], ["publications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "publication_id"),
    )
    with op.batch_alter_table("likes", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_likes_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_likes_publication_id"), ["publication_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_likes_created_at"), ["created_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("likes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_likes_created_at"))
        batch_op.drop_index(batch_op.f("ix_likes_publication_id"))
        batch_op.drop_index(batch_op.f("ix_likes_user_id"))
    op.drop_table("likes")
    with op.batch_alter_table("publications", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_publications_published_at"))
        batch_op.drop_index(batch_op.f("ix_publications_status"))
        batch_op.drop_index(batch_op.f("ix_publications_user_id"))
    op.drop_table("publications")
