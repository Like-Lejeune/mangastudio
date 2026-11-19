"""Séries et personnages."""
import base64
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import moderation, storage
from app.db import get_session
from app.models import Character, Series, User
from app.schemas import CharacterIn, SeriesIn
from app.security import current_user
from app.services import current_plan

router = APIRouter(tags=["séries"])
_PHOTO = re.compile(r"^data:(image/(?:jpeg|png|webp));base64,(.+)$", re.S)


async def refuse_blocked(session: AsyncSession, user: User, text: str) -> None:
    """Point de contrôle n° 1 : le texte saisi. Refus immédiat, rien n'est débité."""
    verdict = await moderation.check_text(session, text)
    for term in verdict.flagged:
        moderation.log(session, user_id=user.id, episode_id=None, checkpoint="input", action="flag", rule=term, excerpt=text)
    for term in verdict.blocked:
        moderation.log(session, user_id=user.id, episode_id=None, checkpoint="input", action="block", rule=term, excerpt=text)
    if verdict.flagged or verdict.blocked:
        await session.commit()
    if not verdict.allowed:
        raise HTTPException(422, {"code": "blocked_terms", "message": "Ce texte contient des mots non autorisés.", "terms": verdict.blocked})


async def owned_series(session: AsyncSession, user: User, series_id: str) -> Series:
    series = (await session.execute(
        select(Series).where(Series.id == series_id, Series.owner_id == user.id)
        .options(selectinload(Series.characters), selectinload(Series.episodes))
    )).scalar_one_or_none()
    if not series:
        raise HTTPException(404, "Série introuvable.")
    return series


def character_out(c: Character) -> dict:
    return {"id": c.id, "slug": c.slug, "name": c.name, "role": c.role, "description": c.description,
            "has_photo": bool(c.photo_path), "sheet_url": storage.url(c.sheet_path)}


def series_out(s: Series, detail: bool = False) -> dict:
    out = {"id": s.id, "title": s.title or "Nouvelle série", "premise": s.premise, "style": s.style, "palette": s.palette,
           "language": s.language, "cover_url": storage.url(s.cover_path), "created_at": s.created_at.isoformat()}
    if detail:
        out["characters"] = [character_out(c) for c in s.characters]
        out["episodes"] = [{"id": e.id, "number": e.number, "title": e.title, "status": e.status, "page_count": e.page_count} for e in s.episodes]
    return out


@router.post("/series", status_code=201)
async def create_series(body: SeriesIn, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    plan, _ = await current_plan(session, user.id)
    if body.palette == "color" and not plan.color:
        raise HTTPException(403, {"code": "plan_limit", "message": f"La couleur n'est pas incluse dans le plan {plan.name}."})
    await refuse_blocked(session, user, body.premise)
    series = Series(owner_id=user.id, **body.model_dump())
    session.add(series)
    await session.commit()
    return await get_series(series.id, user, session)


@router.get("/series")
async def list_series(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Series).where(Series.owner_id == user.id).order_by(Series.created_at.desc()))).scalars()
    return [series_out(s) for s in rows]


@router.get("/series/{series_id}")
async def get_series(series_id: str, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    return series_out(await owned_series(session, user, series_id), detail=True)


@router.post("/series/{series_id}/characters", status_code=201)
async def add_character(series_id: str, body: CharacterIn, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    """Ajoute un personnage à la bibliothèque de la série. Sa fiche est dessinée au premier épisode où il joue."""
    series = await owned_series(session, user, series_id)
    await refuse_blocked(session, user, f"{body.name} {body.role} {body.description}")
    slug = base = re.sub(r"[^a-z0-9]+", "-", moderation.normalize(body.name)).strip("-") or "perso"
    taken = {c.slug for c in series.characters}
    n = 2
    while slug in taken:
        slug, n = f"{base}-{n}", n + 1
    character = Character(series_id=series.id, slug=slug, name=body.name, role=body.role, description=body.description)
    if body.photo:
        if not body.consent:
            raise HTTPException(422, {"code": "consent_required", "message": "Confirmez que vous avez l'accord de la personne sur la photo."})
        match = _PHOTO.match(body.photo)
        if not match:
            raise HTTPException(422, "Photo illisible : JPEG, PNG ou WebP attendu.")
        character.photo_path = await storage.save(f"series/{series.id}/photos/{slug}", base64.b64decode(match.group(2)), match.group(1))
    session.add(character)
    await session.commit()
    return character_out(character)
