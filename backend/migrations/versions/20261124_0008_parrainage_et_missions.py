"""parrainage, recharge hebdomadaire et missions

Révision : 0008
Précédente : 0007
Créée le : 2026-11-24

Donne un code de parrainage à chaque compte existant.
"""
import secrets

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("referral_code", sa.String(length=12), nullable=True))
        batch_op.add_column(sa.Column("referred_by_id", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("signup_ip", sa.String(length=45), nullable=True))
        batch_op.add_column(sa.Column("last_refill_week", sa.String(length=8), nullable=True))
        batch_op.create_unique_constraint("uq_users_referral_code", ["referral_code"])
        batch_op.create_index(batch_op.f("ix_users_referred_by_id"), ["referred_by_id"], unique=False)
    op.create_table(
        "referrals",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("referrer_id", sa.String(length=32), nullable=False),
        sa.Column("referee_id", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("flag_reason", sa.String(length=120), nullable=False),
        sa.Column("invitee_rewarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("referrer_rewarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("purchase_rewarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["referee_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["referrer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("referee_id"),
    )
    with op.batch_alter_table("referrals", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_referrals_referrer_id"), ["referrer_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_referrals_status"), ["status"], unique=False)
    op.create_table(
        "user_missions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("mission", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "mission"),
    )
    with op.batch_alter_table("user_missions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_user_missions_user_id"), ["user_id"], unique=False)

    # Un code pour chaque compte existant.
    bind = op.get_bind()
    users = sa.table("users", sa.column("id", sa.String), sa.column("referral_code", sa.String))
    pris: set[str] = set()
    for (uid,) in bind.execute(sa.select(users.c.id)).all():
        code = ""
        while not code or code in pris:
            code = "".join(secrets.choice(ALPHABET) for _ in range(7))
        pris.add(code)
        bind.execute(users.update().where(users.c.id == uid).values(referral_code=code))


def downgrade() -> None:
    with op.batch_alter_table("user_missions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_missions_user_id"))
    op.drop_table("user_missions")
    with op.batch_alter_table("referrals", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_referrals_status"))
        batch_op.drop_index(batch_op.f("ix_referrals_referrer_id"))
    op.drop_table("referrals")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_referred_by_id"))
        batch_op.drop_constraint("uq_users_referral_code", type_="unique")
        batch_op.drop_column("last_refill_week")
        batch_op.drop_column("signup_ip")
        batch_op.drop_column("referred_by_id")
        batch_op.drop_column("referral_code")
