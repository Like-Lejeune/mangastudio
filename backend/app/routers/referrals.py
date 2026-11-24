"""Écran « Gagner des crédits » et suivi des parrainages dans l'administration."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app import growth
from app.db import get_session
from app.models import Referral, User
from app.routers.admin_ops import PAGE_SIZE, iso, log, page_of
from app.security import admin_user, verified_user

router = APIRouter(tags=["parrainage"])


@router.get("/me/gagner")
async def gagner(user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    data = await growth.summary(session, user)
    await session.commit()
    return data


@router.get("/admin/referrals", dependencies=[Depends(admin_user)])
async def admin_referrals(status: str = "", page: int = 1, session: AsyncSession = Depends(get_session)):
    page = max(1, page)
    parrain, filleul = aliased(User), aliased(User)
    where = [Referral.status == status] if status in ("pending", "qualified", "flagged", "cancelled") else []
    total = (await session.execute(select(func.count()).select_from(Referral).where(*where))).scalar_one()
    rows = (await session.execute(
        select(Referral, parrain.email, parrain.id, filleul.email, filleul.email_verified, filleul.signup_ip)
        .join(parrain, parrain.id == Referral.referrer_id).join(filleul, filleul.id == Referral.referee_id)
        .where(*where).order_by(Referral.created_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    )).all()
    items = [{
        "id": r.id, "status": r.status, "flag_reason": r.flag_reason, "created_at": iso(r.created_at),
        "referrer_id": pid, "referrer_email": pmail, "referee_id": r.referee_id, "referee_email": fmail,
        "referee_verified": fverif, "referee_ip": fip,
        "invitee_rewarded": bool(r.invitee_rewarded_at), "referrer_rewarded": bool(r.referrer_rewarded_at),
        "purchase_rewarded": bool(r.purchase_rewarded_at),
    } for r, pmail, pid, fmail, fverif, fip in rows]
    flagged = (await session.execute(select(func.count()).select_from(Referral).where(Referral.status == "flagged"))).scalar_one()
    res = page_of(items, total, page)
    res["flagged"] = flagged
    return res


@router.post("/admin/referrals/{referral_id}/{action}")
async def admin_decide(referral_id: str, action: str, admin: User = Depends(admin_user), session: AsyncSession = Depends(get_session)):
    """approve : un parrainage mis de côté est validé (les récompenses dues sont versées).
    cancel : plus aucune récompense future ; celles déjà versées se retirent à la main (fiche du compte)."""
    if action not in ("approve", "cancel"):
        raise HTTPException(404, "Action inconnue.")
    r = await session.get(Referral, referral_id)
    if not r:
        raise HTTPException(404, "Parrainage introuvable.")
    if action == "approve":
        if r.status != "flagged":
            raise HTTPException(409, "Seul un parrainage mis de côté peut être validé.")
        await growth.approve(session, r)
        log(session, admin, "referral", "user", r.referrer_id, "Parrainage validé après vérification")
    else:
        r.status = "cancelled"
        log(session, admin, "referral", "user", r.referrer_id, "Parrainage annulé")
    await session.commit()
    return {"status": r.status}
