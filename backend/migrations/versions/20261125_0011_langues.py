"""langues : langue du compte et version anglaise des concours

Révision : 0011
Précédente : 0010
Créée le : 2026-11-25

Ajouts seulement : aucune donnée existante n'est modifiée.
"""
import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("locale", sa.String(length=5), nullable=True))
    with op.batch_alter_table("contests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("title_en", sa.String(length=120), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("theme_en", sa.String(length=300), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("description_en", sa.Text(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("rules_en", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table("contests", schema=None) as batch_op:
        batch_op.drop_column("rules_en")
        batch_op.drop_column("description_en")
        batch_op.drop_column("theme_en")
        batch_op.drop_column("title_en")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("locale")
