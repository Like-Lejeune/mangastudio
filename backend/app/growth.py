"""Crédits gratuits : parrainage, missions et recharge hebdomadaire.

Chaque récompense n'est versée qu'une fois (date enregistrée ou ligne unique), et seulement à des
comptes à l'adresse confirmée. Un parrainage douteux (même adresse IP que le parrain, inscriptions
en série) est mis de côté : l'administration le valide ou l'annule.
"""
import secrets
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import usage
from app.config import get_settings
from app.models import Episode, Referral, Series, User, UserMission
from app.plans import (
    MISSIONS,
    REFERRAL_INVITEE,
    REFERRAL_MAX,
    REFERRAL_PURCHASE,
    REFERRAL_REFERRER,
    WEEKLY_REFILL,
)
from app.services import current_plan

ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"    # sans 0/O ni 1/I/L : se dicte au téléphone


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def new_code(session: AsyncSession) -> str:
    while True:
        code = "".join(secrets.choice(ALPHABET) for _ in range(7))
        if not (await session.execute(select(User.id).where(User.referral_code == code))).first():
            return code


async def ensure_code(session: AsyncSession, user: User) -> str:
    if not user.referral_code:
        user.referral_code = await new_code(session)
        await session.flush()
    return user.referral_code


# ---------- Parrainage ----------

async def attach(session: AsyncSession, user: User, code: str | None, ip: str) -> None:
    """À l'inscription : relie le compte à son parrain et repère les cas douteux."""
    user.signup_ip = ip[:45]
    code = (code or "").strip().upper()
    if not code:
        return
    parrain = (await session.execute(select(User).where(User.referral_code == code))).scalar_one_or_none()
    if not parrain or parrain.id == user.id or not parrain.is_active:
        return
    user.referred_by_id = parrain.id
    raison = ""
    if parrain.signup_ip and parrain.signup_ip == user.signup_ip:
        raison = "même adresse IP que le parrain"
    else:
        recents = (await session.execute(
            select(func.count()).select_from(Referral).join(User, User.id == Referral.referee_id)
            .where(Referral.referrer_id == parrain.id, User.signup_ip == user.signup_ip,
                   Referral.created_at >= _now() - timedelta(hours=24))
        )).scalar_one()
        if recents >= 2:
            raison = "plusieurs filleuls depuis la même adresse IP en 24 h"
    session.add(Referral(referrer_id=parrain.id, referee_id=user.id,
                         status="flagged" if raison else "pending", flag_reason=raison))
    await session.flush()


async def _referral_of(session: AsyncSession, referee_id: str) -> Referral | None:
    return (await session.execute(select(Referral).where(Referral.referee_id == referee_id))).scalar_one_or_none()


async def on_verified(session: AsyncSession, user: User) -> None:
    """Adresse confirmée : bonus de l'invité."""
    r = await _referral_of(session, user.id)
    if r and r.status in ("pending", "qualified") and not r.invitee_rewarded_at:
        await usage.grant(session, user.id, REFERRAL_INVITEE, "pack", "parrainage : bienvenue d'un ami")
        r.invitee_rewarded_at = _now()


async def _rewarded_count(session: AsyncSession, referrer_id: str) -> int:
    return (await session.execute(select(func.count()).select_from(Referral).where(
        Referral.referrer_id == referrer_id, Referral.referrer_rewarded_at.is_not(None)))).scalar_one()


async def _first_episode_done(session: AsyncSession, user_id: str) -> bool:
    return bool((await session.execute(select(Episode.id).join(Series).where(
        Series.owner_id == user_id, Episode.status == "done").limit(1))).first())


async def on_episode_done(session: AsyncSession, user_id: str) -> None:
    """Épisode terminé : mission « premier épisode », et récompense du parrain au premier épisode du filleul."""
    await mission(session, user_id, "first_episode")
    r = await _referral_of(session, user_id)
    if not r or r.status != "pending" or r.referrer_rewarded_at:
        return
    filleul = await session.get(User, user_id)
    if not filleul or not filleul.email_verified:
        return
    r.status = "qualified"
    if await _rewarded_count(session, r.referrer_id) < REFERRAL_MAX:
        await usage.grant(session, r.referrer_id, REFERRAL_REFERRER, "pack", f"parrainage : {filleul.display_name} a terminé son 1er épisode")
        r.referrer_rewarded_at = _now()


async def on_purchase(session: AsyncSession, user_id: str) -> None:
    """Premier achat d'un filleul : bonus du parrain (une fois par filleul)."""
    r = await _referral_of(session, user_id)
    if r and r.status in ("pending", "qualified") and not r.purchase_rewarded_at:
        filleul = await session.get(User, user_id)
        await usage.grant(session, r.referrer_id, REFERRAL_PURCHASE, "pack",
                          f"parrainage : premier achat de {filleul.display_name if filleul else 'votre filleul'}")
        r.purchase_rewarded_at = _now()


async def approve(session: AsyncSession, r: Referral) -> None:
    """Parrainage douteux validé par l'admin : on verse ce qui aurait déjà dû l'être."""
    r.status, r.flag_reason = "pending", ""
    filleul = await session.get(User, r.referee_id)
    if filleul and filleul.email_verified:
        await on_verified(session, filleul)
        if await _first_episode_done(session, filleul.id):
            await on_episode_done(session, filleul.id)


# ---------- Missions ----------

async def mission(session: AsyncSession, user_id: str, name: str) -> bool:
    """Paie la mission si elle ne l'a jamais été. Renvoie True si elle vient d'être payée."""
    if name not in MISSIONS:
        return False
    user = await session.get(User, user_id)
    if not user or not user.email_verified:
        return False
    if (await session.execute(select(UserMission.id).where(UserMission.user_id == user_id, UserMission.mission == name))).first():
        return False
    try:
        async with session.begin_nested():
            session.add(UserMission(user_id=user_id, mission=name))
    except IntegrityError:
        return False
    credits, libelle = MISSIONS[name]
    await usage.grant(session, user_id, credits, "pack", f"mission : {libelle}")
    return True


# ---------- Recharge hebdomadaire ----------

def week_key(when: datetime | None = None) -> str:
    local = (when or _now()).astimezone(ZoneInfo(get_settings().budget_timezone))
    y, w, _ = local.isocalendar()
    return f"{y}-W{w:02d}"


def next_refill() -> datetime:
    tz = ZoneInfo(get_settings().budget_timezone)
    local = _now().astimezone(tz)
    lundi = (local + timedelta(days=7 - local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return lundi


async def weekly_refill(session: AsyncSession, user: User) -> int:
    """À la première visite de la semaine : un compte gratuit confirmé remonte à WEEKLY_REFILL crédits.
    Renvoie le nombre de crédits ajoutés (0 si rien à faire)."""
    semaine = week_key()
    if user.last_refill_week == semaine or not user.email_verified or not user.is_active:
        return 0
    plan, _ = await current_plan(session, user.id)
    user.last_refill_week = semaine
    if plan.id != "free":
        return 0
    manque = WEEKLY_REFILL - await usage.balance(session, user.id)
    if manque > 0:
        await usage.grant(session, user.id, manque, "pack", "recharge hebdomadaire")
        return manque
    return 0


# ---------- Écran « Gagner des crédits » ----------

async def summary(session: AsyncSession, user: User) -> dict:
    code = await ensure_code(session, user)
    rows = (await session.execute(
        select(Referral, User.display_name).join(User, User.id == Referral.referee_id)
        .where(Referral.referrer_id == user.id).order_by(Referral.created_at.desc())
    )).all()
    gagnes = sum((REFERRAL_REFERRER if r.referrer_rewarded_at else 0) + (REFERRAL_PURCHASE if r.purchase_rewarded_at else 0) for r, _ in rows)
    faites = set((await session.execute(select(UserMission.mission).where(UserMission.user_id == user.id))).scalars())
    app = get_settings().frontend_url.split(",")[0].strip().rstrip("/")
    return {
        "code": code,
        "link": f"{app}/inscription?ref={code}",
        "rewards": {"invitee": REFERRAL_INVITEE, "referrer": REFERRAL_REFERRER, "purchase": REFERRAL_PURCHASE, "max": REFERRAL_MAX},
        "referrals": [{
            "name": nom, "created_at": r.created_at.isoformat() if r.created_at else None,
            "status": "checking" if r.status == "flagged" else r.status,
            "rewarded": bool(r.referrer_rewarded_at), "purchase_rewarded": bool(r.purchase_rewarded_at),
        } for r, nom in rows],
        "earned": gagnes,
        "rewarded_count": sum(1 for r, _ in rows if r.referrer_rewarded_at),
        "missions": [{"id": k, "label": v[1], "credits": v[0], "done": k in faites} for k, v in MISSIONS.items()],
        "weekly_refill": {"amount": WEEKLY_REFILL, "next": next_refill().isoformat()},
    }
