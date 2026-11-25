"""Concours : phases, classement et remise des lots.

Classement : note du jury sur 20 (60 %) + « j'aime » reçus pendant le concours (40 %).
Les « j'aime » sont ramenés sur 20 par rapport à l'histoire la plus aimée du concours :
celle-ci obtient 20, une histoire avec moitié moins de « j'aime » obtient 10, etc.
"""
import re
import unicodedata
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import usage
from app.models import Contest, ContestEntry, Like, Publication, Subscription, now
from app.services import aware

JURY_WEIGHT, LIKES_WEIGHT = 0.6, 0.4
PHASES = {"a_venir": "À venir", "en_cours": "En cours", "deliberation": "Délibération du jury", "termine": "Terminé"}


def phase(c: Contest, at: datetime | None = None) -> str:
    t = at or now()
    if c.results_at:
        return "termine"
    if t < aware(c.starts_at):
        return "a_venir"
    if t < aware(c.ends_at):
        return "en_cours"
    return "deliberation"


def slugify(text: str) -> str:
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:70] or "concours"


async def contest_likes(session: AsyncSession, c: Contest, publication_ids: list[str]) -> dict[str, int]:
    """« J'aime » reçus par chaque histoire entre l'ouverture et la clôture du concours."""
    if not publication_ids:
        return {}
    rows = (await session.execute(
        select(Like.publication_id, func.count()).where(
            Like.publication_id.in_(publication_ids), Like.created_at >= c.starts_at, Like.created_at < c.ends_at)
        .group_by(Like.publication_id)
    )).all()
    return {pid: int(n) for pid, n in rows}


def score(jury: float, likes: int, max_likes: int) -> float:
    likes_on_20 = 20 * likes / max_likes if max_likes else 0.0
    return round(JURY_WEIGHT * jury + LIKES_WEIGHT * likes_on_20, 2)


def prize_label(p: dict) -> str:
    parts = []
    if p.get("credits"):
        parts.append(f"{p['credits']} crédits")
    if p.get("studio_days"):
        parts.append(f"{p['studio_days']} jours de plan Studio")
    return " + ".join(parts)


def rank_label(rank: int) -> str:
    return "1er prix" if rank == 1 else f"{rank}e prix"


async def eligible_entries(session: AsyncSession, c: Contest) -> list[ContestEntry]:
    """En lice : non disqualifiées et dont l'histoire est publiée dans la galerie."""
    return list((await session.execute(
        select(ContestEntry).join(Publication, Publication.id == ContestEntry.publication_id)
        .where(ContestEntry.contest_id == c.id, ContestEntry.disqualified == "", Publication.status == "published")
        .order_by(ContestEntry.created_at)
    )).scalars())


async def proclaim(session: AsyncSession, c: Contest) -> list[ContestEntry]:
    """Calcule le classement, remet les lots et fige le tout. À appeler une seule fois, après la clôture."""
    entries = await eligible_entries(session, c)
    likes = await contest_likes(session, c, [e.publication_id for e in entries])
    top = max(likes.values(), default=0)
    for e in entries:
        e.likes = likes.get(e.publication_id, 0)
        e.score = score(e.jury_score or 0.0, e.likes, top)
    # Égalité : le plus de « j'aime », puis la première inscrite.
    entries.sort(key=lambda e: (-(e.score or 0), -e.likes, aware(e.created_at)))
    prizes = {int(p["rank"]): p for p in (c.prizes or []) if p.get("rank")}
    for i, e in enumerate(entries, start=1):
        e.rank = i
        p = prizes.get(i)
        if not p:
            continue
        e.prize = prize_label(p)
        if p.get("credits"):
            await usage.grant(session, e.user_id, int(p["credits"]), "pack", f"concours : {c.title} — {rank_label(i)}")
        if p.get("studio_days"):
            await _offer_studio(session, e.user_id, int(p["studio_days"]))
    c.results_at = now()
    return entries


async def _offer_studio(session: AsyncSession, user_id: str, days: int) -> None:
    """Jours de plan Studio offerts.
    - Pas d'abonnement en cours : Studio à partir d'aujourd'hui.
    - Studio en cours : prolongé d'autant.
    - Créateur en cours : on ne rétrograde ni ne coupe rien ; il passe Studio, prolongé d'autant."""
    sub = await session.get(Subscription, user_id)
    t = now()
    if sub is None:
        session.add(Subscription(user_id=user_id, plan="studio", status="active", provider="admin", period_end=t + timedelta(days=days)))
        return
    running = sub.status == "active" and aware(sub.period_end) > t
    start = aware(sub.period_end) if running else t
    sub.plan, sub.status = "studio", "active"
    if not running:
        sub.provider = "admin"
    sub.period_end = start + timedelta(days=days)
