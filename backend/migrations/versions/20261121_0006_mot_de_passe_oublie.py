"""mot de passe oublié et fermeture des sessions

Révision : 0006
Précédente : 0005
Créée le : 2026-11-21
"""
import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("reset_code_hash", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("reset_expires_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("reset_attempts", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("session_version", sa.Integer(), server_default="0", nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("session_version")
        batch_op.drop_column("reset_attempts")
        batch_op.drop_column("reset_expires_at")
        batch_op.drop_column("reset_code_hash")
