"""moderation : liste initiale de mots bloqués et de scènes interdites

Révision : 0003
Précédente : 0002
Créée le : 2026-11-18

N'ajoute que ce qui manque : un mot ou une règle déjà créés à la main ne sont pas modifiés.
"""
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

from app.moderation import normalize
from app.moderation_defaults import SCENE_RULES, TERMS

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

terms = sa.table("blocked_terms", sa.column("id", sa.String), sa.column("term", sa.String),
                 sa.column("action", sa.String), sa.column("created_at", sa.DateTime(timezone=True)))
rules = sa.table("scene_rules", sa.column("id", sa.String), sa.column("label", sa.String),
                 sa.column("description", sa.Text), sa.column("active", sa.Boolean))


def upgrade() -> None:
    bind = op.get_bind()
    have_terms = {r[0] for r in bind.execute(sa.select(terms.c.term))}
    now = datetime.now(timezone.utc)
    new_terms = {}
    for term, action in TERMS:
        t = normalize(term)
        if t and t not in have_terms and t not in new_terms:
            new_terms[t] = action
    if new_terms:
        op.bulk_insert(terms, [{"id": uuid.uuid4().hex, "term": t, "action": a, "created_at": now} for t, a in new_terms.items()])

    have_rules = {r[0] for r in bind.execute(sa.select(rules.c.label))}
    new_rules = [(label, d) for label, d in SCENE_RULES if label not in have_rules]
    if new_rules:
        op.bulk_insert(rules, [{"id": uuid.uuid4().hex, "label": label, "description": d, "active": True} for label, d in new_rules])


def downgrade() -> None:
    op.execute(terms.delete().where(terms.c.term.in_([normalize(t) for t, _ in TERMS])))
    op.execute(rules.delete().where(rules.c.label.in_([label for label, _ in SCENE_RULES])))
