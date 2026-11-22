"""Avis des utilisateurs : dépôt (connecté), lecture publique des avis validés, modération par l'administration."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Testimonial, User
from app.routers.admin_ops import PAGE_SIZE, iso, log, page_of
from app.routers.series import refuse_blocked
from app.schemas import TestimonialIn, TestimonialStatusIn
from app.security import admin_user, current_user, verified_user

router = APIRouter(tags=["avis"])
PUBLIC_LIMIT = 12


def public(t: Testimonial) -> dict:
    return {"id": t.id, "texte": t.text, "nom": t.display_name, "role": t.role, "note": t.rating}


def full(t: Testimonial, email: str | None = None) -> dict:
    return {
        "id": t.id, "text": t.text, "rating": t.rating, "display_name": t.display_name, "role": t.role,
        "status": t.status, "episode_id": t.episode_id, "user_id": t.user_id, "user_email": email,
        "created_at": iso(t.created_at), "reviewed_at": iso(t.reviewed_at),
    }


@router.get("/testimonials")
async def approved(session: AsyncSession = Depends(get_session)):
    """Les avis validés, les plus récents d'abord (page d'accueil, sans connexion)."""
    rows = (await session.execute(
        select(Testimonial).where(Testimonial.status == "approved").order_by(Testimonial.reviewed_at.desc()).limit(PUBLIC_LIMIT)
    )).scalars()
    return [public(t) for t in rows]


@router.get("/testimonials/mine")
async def mine(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    t = (await session.execute(select(Testimonial).where(Testimonial.user_id == user.id))).scalar_one_or_none()
    return full(t) if t else None


@router.put("/testimonials/mine")
async def submit(body: TestimonialIn, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """Dépose ou remplace l'avis du compte. Toute modification repasse en attente de validation."""
    if not body.consent:
        raise HTTPException(422, {"code": "consent_required", "message": "Cochez l'accord de publication pour envoyer votre avis."})
    await refuse_blocked(session, user, f"{body.text} {body.display_name} {body.role}")
    t = (await session.execute(select(Testimonial).where(Testimonial.user_id == user.id))).scalar_one_or_none()
    if t is None:
        t = Testimonial(user_id=user.id)
        session.add(t)
    t.text, t.rating, t.display_name, t.role = body.text.strip(), body.rating, body.display_name.strip(), body.role.strip()
    t.consent, t.episode_id, t.status, t.reviewed_at = True, body.episode_id, "pending", None
    t.created_at = datetime.now(timezone.utc)
    await session.commit()
    return full(t)


@router.delete("/testimonials/mine", status_code=204)
async def withdraw(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    """Retire l'avis (et donc l'accord de publication) : il disparaît aussitôt de l'accueil."""
    t = (await session.execute(select(Testimonial).where(Testimonial.user_id == user.id))).scalar_one_or_none()
    if t:
        await session.delete(t)
        await session.commit()


@router.get("/admin/testimonials", dependencies=[Depends(admin_user)])
async def admin_list(status: str = "pending", page: int = 1, session: AsyncSession = Depends(get_session)):
    page = max(1, page)
    where = [Testimonial.status == status] if status in ("pending", "approved", "rejected") else []
    total = (await session.execute(select(func.count()).select_from(Testimonial).where(*where))).scalar_one()
    rows = (await session.execute(
        select(Testimonial, User.email).join(User, User.id == Testimonial.user_id, isouter=True)
        .where(*where).order_by(Testimonial.created_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    )).all()
    return page_of([full(t, email) for t, email in rows], total, page)


@router.post("/admin/testimonials/{testimonial_id}/status")
async def admin_review(testimonial_id: str, body: TestimonialStatusIn, admin: User = Depends(admin_user), session: AsyncSession = Depends(get_session)):
    t = await session.get(Testimonial, testimonial_id)
    if not t:
        raise HTTPException(404, "Avis introuvable.")
    t.status = body.status
    t.reviewed_at = datetime.now(timezone.utc) if body.status != "pending" else None
    label = {"approved": "publié", "rejected": "refusé", "pending": "remis en attente"}[body.status]
    log(session, admin, "testimonial", "user", t.user_id, f"Avis {label} : « {t.text[:60]}… »")
    await session.commit()
    return full(t)
