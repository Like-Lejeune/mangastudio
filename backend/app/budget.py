"""Plafond de dépense IA par jour, avec alertes.

Le coût est celui du journal d'usage (UsageEvent.cost_micro_usd, calculé avec PRICES).
- Avant d'admettre un épisode, une reprise ou un redessin : refus (503) si le plafond du jour est atteint.
  Rien n'est réservé ni débité. Les épisodes déjà lancés se terminent (le client les a payés).
- Alertes à AI_ALERT_RATIO (80 % par défaut) puis à 100 % : une seule fois par niveau et par jour,
  notée au journal d'administration et envoyée à ALERT_WEBHOOK_URL si elle est réglée.
"""
import logging
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import httpx
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import AdminAction, UsageEvent

log = logging.getLogger("mangastudio.budget")
SYSTEM = "système"


def _day_start() -> tuple[datetime, str]:
    """Début du jour en cours dans le fuseau de la plateforme, en UTC, et la date affichée."""
    tz = ZoneInfo(get_settings().budget_timezone)
    today = datetime.now(tz).date()
    return datetime.combine(today, time.min, tz).astimezone(timezone.utc), today.isoformat()


async def spent_today(session: AsyncSession) -> float:
    start, _ = _day_start()
    micro = (await session.execute(
        select(func.coalesce(func.sum(UsageEvent.cost_micro_usd), 0)).where(UsageEvent.created_at >= start)
    )).scalar_one()
    return micro / 1e6


async def status(session: AsyncSession) -> dict:
    limit = get_settings().ai_daily_budget_usd
    spent = await spent_today(session)
    return {"limit_usd": limit, "spent_today_usd": round(spent, 4), "ratio": round(spent / limit, 4) if limit > 0 else None}


async def guard(session: AsyncSession) -> None:
    """À appeler avant toute nouvelle dépense IA demandée par un client."""
    s = get_settings()
    if s.ai_daily_budget_usd <= 0:
        return
    spent = await spent_today(session)
    await alert_if_needed(session, spent)
    if spent >= s.ai_daily_budget_usd:
        raise HTTPException(503, {
            "code": "daily_budget_reached",
            "message": "Le studio a atteint sa capacité de dessin pour aujourd'hui. Réessayez demain : aucun crédit n'a été utilisé.",
        })


async def alert_if_needed(session: AsyncSession, spent: float | None = None) -> None:
    """Envoie l'alerte de chaque niveau franchi aujourd'hui, une seule fois."""
    s = get_settings()
    limit = s.ai_daily_budget_usd
    if limit <= 0:
        return
    spent = await spent_today(session) if spent is None else spent
    _, day = _day_start()
    for level, ratio in (("100", 1.0), (str(round(s.ai_alert_ratio * 100)), s.ai_alert_ratio)):
        if spent < limit * ratio:
            continue
        target = f"{day}:{level}"
        if (await session.execute(select(AdminAction.id).where(AdminAction.action == "budget_alert", AdminAction.target_id == target))).first():
            return   # niveau déjà signalé (et donc le niveau inférieur aussi)
        msg = (f"MangaStudio : dépense IA du {day} à {spent:.2f} $ sur un plafond de {limit:.2f} $ ({level} %)."
               + (" Les nouveaux épisodes sont refusés jusqu'à demain." if ratio >= 1 else ""))
        session.add(AdminAction(admin_id=SYSTEM, admin_email=SYSTEM, action="budget_alert", target_type="platform", target_id=target, detail=msg))
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return
        log.warning(msg)
        await _send(msg)
        return   # le niveau le plus haut suffit


async def _send(msg: str) -> None:
    url = get_settings().alert_webhook_url
    if not url:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"text": msg, "content": msg})
    except httpx.HTTPError:
        log.exception("alerte non envoyée")
