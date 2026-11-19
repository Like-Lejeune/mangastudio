"""Petites fonctions partagées par les routeurs."""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Subscription, now
from app.plans import Plan, get_plan


def aware(dt: datetime) -> datetime:
    """SQLite rend des dates sans fuseau ; PostgreSQL les rend en UTC."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def current_plan(session: AsyncSession, user_id: str) -> tuple[Plan, Subscription | None]:
    """Le plan en vigueur : celui de l'abonnement tant que la période payée court, sinon le gratuit."""
    sub = await session.get(Subscription, user_id)
    if sub and aware(sub.period_end) > now():
        return get_plan(sub.plan), sub
    return get_plan("free"), sub
