"""Journal d'usage (tokens, images, coût) et crédits (réserve puis règlement).

Crédits : 1 crédit = 1 image livrée (page, fiche modèle ou couverture).
Deux compartiments : `monthly` (expire au renouvellement) et `pack` (n'expire pas).
On dépense le mensuel d'abord ; on rembourse le pack d'abord."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import CreditLedger, UsageEvent, User
from app.providers.base import Usage


class InsufficientCredits(Exception):
    def __init__(self, needed: int, balance: int):
        super().__init__(f"Il faut {needed} crédits, il en reste {balance}.")
        self.needed, self.balance = needed, balance


# ─── Usage ────────────────────────────────────────────────────────────────────

def cost_micro_usd(model: str, usage: Usage) -> int:
    p = get_settings().prices.get(model, {})
    usd = (usage.input_tokens * p.get("in", 0) + usage.output_tokens * p.get("out", 0)) / 1e6 + usage.images * p.get("image", 0)
    return round(usd * 1e6)


def record(session: AsyncSession, *, user_id: str, episode_id: str | None, stage: str, provider: str, model: str, usage: Usage) -> None:
    """Ajoute une ligne d'usage (validée avec la transaction en cours)."""
    session.add(UsageEvent(
        user_id=user_id, episode_id=episode_id, stage=stage, provider=provider, model=model,
        input_tokens=usage.input_tokens, output_tokens=usage.output_tokens, images=usage.images,
        cost_micro_usd=cost_micro_usd(model, usage),
    ))


async def episode_usage(session: AsyncSession, episode_id: str) -> dict:
    """Le compteur montré à l'utilisateur : totaux et détail par étape (sans le coût)."""
    rows = (await session.execute(
        select(UsageEvent.stage, func.sum(UsageEvent.input_tokens), func.sum(UsageEvent.output_tokens),
               func.sum(UsageEvent.images), func.count())
        .where(UsageEvent.episode_id == episode_id).group_by(UsageEvent.stage)
    )).all()
    stages = [{"stage": s, "input_tokens": i or 0, "output_tokens": o or 0, "images": im or 0, "calls": n} for s, i, o, im, n in rows]
    credits = (await session.execute(
        select(func.coalesce(func.sum(CreditLedger.delta), 0)).where(CreditLedger.episode_id == episode_id)
    )).scalar_one()
    return {
        "input_tokens": sum(s["input_tokens"] for s in stages),
        "output_tokens": sum(s["output_tokens"] for s in stages),
        "images": sum(s["images"] for s in stages),
        "credits": -credits,
        "stages": sorted(stages, key=lambda s: s["stage"]),
    }


# ─── Crédits ──────────────────────────────────────────────────────────────────

async def _bucket_balance(session: AsyncSession, user_id: str, bucket: str) -> int:
    return (await session.execute(
        select(func.coalesce(func.sum(CreditLedger.delta), 0)).where(CreditLedger.user_id == user_id, CreditLedger.bucket == bucket)
    )).scalar_one()


async def balance(session: AsyncSession, user_id: str) -> int:
    return (await session.execute(
        select(func.coalesce(func.sum(CreditLedger.delta), 0)).where(CreditLedger.user_id == user_id)
    )).scalar_one()


async def grant(session: AsyncSession, user_id: str, amount: int, bucket: str, note: str = "") -> None:
    session.add(CreditLedger(user_id=user_id, delta=amount, bucket=bucket, kind="grant", note=note))


async def renew_monthly(session: AsyncSession, user_id: str, amount: int, note: str) -> None:
    """Nouvelle période : le reliquat mensuel expire, puis les crédits du mois arrivent."""
    left = await _bucket_balance(session, user_id, "monthly")
    if left > 0:
        session.add(CreditLedger(user_id=user_id, delta=-left, bucket="monthly", kind="expire", note="fin de période"))
    await grant(session, user_id, amount, "monthly", note)


async def reserve(session: AsyncSession, user_id: str, episode_id: str, amount: int) -> None:
    """Bloque `amount` crédits pour un épisode, ou lève InsufficientCredits.
    La ligne utilisateur est verrouillée : deux épisodes lancés en même temps ne
    peuvent pas dépenser deux fois le même solde (PostgreSQL)."""
    await session.execute(select(User.id).where(User.id == user_id).with_for_update())
    monthly = max(0, await _bucket_balance(session, user_id, "monthly"))
    pack = max(0, await _bucket_balance(session, user_id, "pack"))
    if monthly + pack < amount:
        raise InsufficientCredits(amount, monthly + pack)
    from_monthly = min(monthly, amount)
    for bucket, part in (("monthly", from_monthly), ("pack", amount - from_monthly)):
        if part:
            session.add(CreditLedger(user_id=user_id, delta=-part, bucket=bucket, kind="reserve", episode_id=episode_id))


async def settle(session: AsyncSession, user_id: str, episode_id: str, delivered: int) -> int:
    """Rend la part de la réserve non consommée. Renvoie le nombre de crédits rendus."""
    rows = (await session.execute(
        select(CreditLedger.bucket, func.sum(CreditLedger.delta)).where(CreditLedger.episode_id == episode_id).group_by(CreditLedger.bucket)
    )).all()
    held = {bucket: -total for bucket, total in rows}          # encore bloqué, par compartiment
    refund = sum(held.values()) - delivered
    if refund <= 0:
        return 0
    left = refund
    for bucket in ("pack", "monthly"):
        part = min(left, max(0, held.get(bucket, 0)))
        if part:
            session.add(CreditLedger(user_id=user_id, delta=part, bucket=bucket, kind="refund", episode_id=episode_id))
            left -= part
    return refund
