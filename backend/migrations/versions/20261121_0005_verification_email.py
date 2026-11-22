"""vérification de l'adresse e-mail

Révision : 0005
Précédente : 0004
Créée le : 2026-11-21

Les comptes existants sont marqués vérifiés (server_default true) ; l'application crée les
nouveaux comptes non vérifiés.
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("email_verified", sa.Boolean(), server_default=sa.true(), nullable=False))
        batch_op.add_column(sa.Column("verify_code_hash", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("verify_expires_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("verify_attempts", sa.Integer(), server_default="0", nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("verify_attempts")
        batch_op.drop_column("verify_expires_at")
        batch_op.drop_column("verify_code_hash")
        batch_op.drop_column("email_verified")
