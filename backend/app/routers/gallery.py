"""Galerie publique « À lire » : demande de publication, validation par l'administration, lecture et likes."""
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import ratelimit, storage
from app.db import get_session
from app.i18n import tr
from app.models import Episode, Like, Publication, User
from app.routers.admin_ops import PAGE_SIZE, iso, log, page_of
from app.routers.episodes import owned_episode
from app.security import admin_user, optional_user, verified_user

router = APIRouter(tags=["galerie"])
LIKES_PER_HOUR = 60


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------- Côté auteur ----------

class PublishIn(BaseModel):
    accept_terms: bool


def author_view(p: Publication | None) -> dict | None:
    if not p:
        return None
    return {"id": p.id, "status": p.status, "reason": tr(p.reason), "likes": p.likes, "featured": p.featured,
            "requested_at": iso(p.requested_at), "published_at": iso(p.published_at)}


async def _pub_of(session: AsyncSession, episode_id: str) -> Publication | None:
    return (await session.execute(select(Publication).where(Publication.episode_id == episode_id))).scalar_one_or_none()


@router.get("/episodes/{episode_id}/publication")
async def my_publication(episode_id: str, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    e = await owned_episode(session, user, episode_id)
    return author_view(await _pub_of(session, e.id))


@router.post("/episodes/{episode_id}/publication")
async def request_publication(episode_id: str, body: PublishIn, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """Propose le chapitre à la galerie. Il n'y apparaît qu'après validation par l'équipe."""
    e = await owned_episode(session, user, episode_id)
    if e.status != "done":
        raise HTTPException(409, "Seul un épisode terminé peut être publié.")
    if not body.accept_terms:
        raise HTTPException(422, {"code": "terms_required", "message": "Acceptez les règles de publication pour proposer votre chapitre."})
    p = await _pub_of(session, e.id)
    if p and p.status in ("pending", "published"):
        return author_view(p)
    if p is None:
        p = Publication(episode_id=e.id, user_id=user.id)
        session.add(p)
    p.status, p.reason, p.featured = "pending", "", False
    p.requested_at, p.terms_accepted_at = _now(), _now()
    await session.commit()
    return author_view(p)


@router.delete("/episodes/{episode_id}/publication")
async def withdraw_publication(episode_id: str, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """L'auteur retire son chapitre de la galerie, à tout moment. Les likes sont conservés s'il le republie."""
    e = await owned_episode(session, user, episode_id)
    p = await _pub_of(session, e.id)
    if p and p.status in ("pending", "published"):
        p.status, p.featured, p.reason = "withdrawn", False, "Retiré par l'auteur"
        await session.commit()
    return author_view(p)


# ---------- Galerie publique ----------

def _card(p: Publication, e: Episode, author: str, liked: bool) -> dict:
    pages = [pg for pg in e.pages if pg.image_path]
    cover = storage.url(e.series.cover_path) or (storage.url(pages[0].image_path) if pages else None)
    return {
        "id": p.id, "series_title": e.series.title or "Manga", "number": e.number, "title": e.title,
        "style": e.series.style, "author": author, "cover_url": cover, "pages": len(pages),
        "likes": p.likes, "liked": liked, "featured": p.featured, "published_at": iso(p.published_at),
    }


async def _liked_ids(session: AsyncSession, user: User | None, ids: list[str]) -> set[str]:
    if not user or not ids:
        return set()
    return set((await session.execute(select(Like.publication_id).where(Like.user_id == user.id, Like.publication_id.in_(ids)))).scalars())


@router.get("/gallery")
async def gallery(tri: Literal["recentes", "populaires", "semaine", "coups"] = "recentes", page: int = 1, size: int = 12,
                  user: User | None = Depends(optional_user), session: AsyncSession = Depends(get_session)):
    page, size = max(1, page), min(max(1, int(size)), 48)
    base = [Publication.status == "published"]
    if tri == "coups":
        base.append(Publication.featured.is_(True))
    q = (select(Publication, Episode, User.display_name).join(Episode, Episode.id == Publication.episode_id)
         .join(User, User.id == Publication.user_id).where(*base)
         .options(selectinload(Episode.pages), selectinload(Episode.series)))
    if tri == "semaine":
        recents = (select(Like.publication_id, func.count().label("n")).where(Like.created_at >= _now() - timedelta(days=7))
                   .group_by(Like.publication_id).subquery())
        q = q.add_columns(func.coalesce(recents.c.n, 0)).outerjoin(recents, recents.c.publication_id == Publication.id).order_by(
            func.coalesce(recents.c.n, 0).desc(), Publication.likes.desc(), Publication.published_at.desc())
    elif tri == "populaires":
        q = q.order_by(Publication.likes.desc(), Publication.published_at.desc())
    else:
        q = q.order_by(Publication.published_at.desc())
    total = (await session.execute(select(func.count()).select_from(Publication).where(*base))).scalar_one()
    rows = (await session.execute(q.offset((page - 1) * size).limit(size))).all()
    liked = await _liked_ids(session, user, [r[0].id for r in rows])
    items = []
    for r in rows:
        c = _card(r[0], r[1], r[2], r[0].id in liked)
        if tri == "semaine":
            c["likes_week"] = int(r[3])     # likes reçus ces 7 derniers jours
        items.append(c)
    return page_of(items, total, page)


@router.get("/gallery/{pub_id}")
async def gallery_item(pub_id: str, user: User | None = Depends(optional_user), session: AsyncSession = Depends(get_session)):
    row = (await session.execute(
        select(Publication, Episode, User.display_name).join(Episode, Episode.id == Publication.episode_id)
        .join(User, User.id == Publication.user_id).where(Publication.id == pub_id, Publication.status == "published")
        .options(selectinload(Episode.pages), selectinload(Episode.series))
    )).first()
    if not row:
        raise HTTPException(404, "Cette histoire n'est pas (ou plus) publiée.")
    p, e, author = row
    liked = await _liked_ids(session, user, [p.id])
    data = _card(p, e, author, p.id in liked)
    data["premise"] = e.series.premise
    data["page_urls"] = [storage.url(pg.image_path) for pg in e.pages if pg.image_path]
    data["is_author"] = bool(user and user.id == p.user_id)
    from app.routers.contests import (
        awards_for,  # import tardif : contests importe ce module
    )
    data["awards"] = await awards_for(session, p.id)
    return data


async def _recount(session: AsyncSession, p: Publication) -> None:
    p.likes = (await session.execute(select(func.count()).select_from(Like).where(Like.publication_id == p.id))).scalar_one()


@router.post("/gallery/{pub_id}/like")
async def like(pub_id: str, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """Un like par compte confirmé et par histoire ; jamais sur la sienne ; 60 par heure au plus."""
    p = await session.get(Publication, pub_id)
    if not p or p.status != "published":
        raise HTTPException(404, "Cette histoire n'est pas publiée.")
    if p.user_id == user.id:
        raise HTTPException(409, {"code": "own_story", "message": "Vous ne pouvez pas aimer votre propre histoire."})
    ratelimit.check(f"likes:{user.id}", LIKES_PER_HOUR, 3600)
    try:
        async with session.begin_nested():
            session.add(Like(user_id=user.id, publication_id=p.id))
        ratelimit.add(f"likes:{user.id}")
    except IntegrityError:
        pass        # déjà aimé : rien à faire
    await _recount(session, p)
    await session.commit()
    return {"likes": p.likes, "liked": True}


@router.delete("/gallery/{pub_id}/like")
async def unlike(pub_id: str, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    p = await session.get(Publication, pub_id)
    if not p:
        raise HTTPException(404, "Histoire introuvable.")
    lk = (await session.execute(select(Like).where(Like.user_id == user.id, Like.publication_id == p.id))).scalar_one_or_none()
    if lk:
        await session.delete(lk)
        await session.flush()
    await _recount(session, p)
    await session.commit()
    return {"likes": p.likes, "liked": False}


# ---------- Administration ----------

class DecisionIn(BaseModel):
    action: Literal["approve", "reject", "withdraw", "feature", "unfeature"]
    reason: str = Field(default="", max_length=300)


@router.get("/admin/publications", dependencies=[Depends(admin_user)])
async def admin_publications(status: str = "pending", page: int = 1, session: AsyncSession = Depends(get_session)):
    page = max(1, page)
    where = [Publication.status == status] if status in ("pending", "published", "rejected", "withdrawn") else []
    if status == "featured":
        where = [Publication.featured.is_(True), Publication.status == "published"]
    total = (await session.execute(select(func.count()).select_from(Publication).where(*where))).scalar_one()
    rows = (await session.execute(
        select(Publication, Episode, User.display_name, User.email).join(Episode, Episode.id == Publication.episode_id)
        .join(User, User.id == Publication.user_id).where(*where)
        .options(selectinload(Episode.pages), selectinload(Episode.series))
        .order_by(Publication.requested_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    )).all()
    items = []
    for p, e, author, email in rows:
        c = _card(p, e, author, False)
        c.update({"status": p.status, "reason": p.reason, "episode_id": e.id, "user_id": p.user_id, "email": email,
                  "requested_at": iso(p.requested_at),
                  "page_urls": [storage.url(pg.image_path) for pg in e.pages if pg.image_path][:4]})
        items.append(c)
    res = page_of(items, total, page)
    res["pending"] = (await session.execute(select(func.count()).select_from(Publication).where(Publication.status == "pending"))).scalar_one()
    return res


@router.post("/admin/publications/{pub_id}")
async def admin_decide(pub_id: str, body: DecisionIn, admin: User = Depends(admin_user), session: AsyncSession = Depends(get_session)):
    p = await session.get(Publication, pub_id)
    if not p:
        raise HTTPException(404, "Publication introuvable.")
    a = body.action
    if a in ("reject", "withdraw") and len(body.reason.strip()) < 3:
        raise HTTPException(422, "Indiquez un motif : il est montré à l'auteur.")
    if a == "approve":
        p.status, p.reason = "published", ""
        p.published_at = p.published_at or _now()
    elif a == "reject":
        p.status, p.reason, p.featured = "rejected", body.reason.strip(), False
    elif a == "withdraw":
        p.status, p.reason, p.featured = "withdrawn", body.reason.strip(), False
    elif a in ("feature", "unfeature"):
        if p.status != "published":
            raise HTTPException(409, "Seule une histoire publiée peut être un coup de cœur.")
        p.featured = a == "feature"
    label = {"approve": "publiée", "reject": "refusée", "withdraw": "retirée", "feature": "mise en coup de cœur", "unfeature": "retirée des coups de cœur"}[a]
    log(session, admin, "publication", "user", p.user_id, f"Histoire {label}" + (f" : {body.reason.strip()}" if body.reason.strip() else ""))
    await session.commit()
    return {"status": p.status, "featured": p.featured}
