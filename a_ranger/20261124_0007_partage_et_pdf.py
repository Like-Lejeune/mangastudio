"""partage d'un chapitre par lien et téléchargements PDF

Révision : 0007
Précédente : 0006
Créée le : 2026-11-24
"""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("episodes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("share_token", sa.String(length=32), nullable=True))
        batch_op.create_unique_constraint("uq_episodes_share_token", ["share_token"])
    op.create_table(
        "pdf_downloads",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("episode_id", sa.String(length=32), nullable=False),
        sa.Column("watermark", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("pdf_downloads", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_pdf_downloads_user_id"), ["user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_pdf_downloads_created_at"), ["created_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("pdf_downloads", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_pdf_downloads_created_at"))
        batch_op.drop_index(batch_op.f("ix_pdf_downloads_user_id"))
    op.drop_table("pdf_downloads")
    with op.batch_alter_table("episodes", schema=None) as batch_op:
        batch_op.drop_constraint("uq_episodes_share_token", type_="unique")
        batch_op.drop_column("share_token")
