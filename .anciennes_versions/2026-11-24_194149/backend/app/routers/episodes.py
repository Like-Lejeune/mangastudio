"""Épisodes : lancement (admission), suivi, compteur d'usage, reprise, redessin."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import budget, storage, usage
from app.config import get_settings
from app.db import get_session
from app.models import Episode, EpisodeCharacter, Page, Series, User
from app.pipeline.runner import delivered_images, remaining_images
from app.plans import MIN_PAGES
from app.queue import enqueue
from app.routers.series import owned_series, refuse_blocked, refuse_protected
from app.schemas import EpisodeIn, RedrawIn
from app.security import verified_user
from app.services import current_plan

router = APIRouter(tags=["épisodes"])
RUNNING = ("queued", "designing", "writing", "moderating", "drawing")


def limit(message: str) -> HTTPException:
    return HTTPException(403, {"code": "plan_limit", "message": message})


async def owned_episode(session: AsyncSession, user: User, episode_id: str) -> Episode:
    episode = (await session.execute(
        select(Episode).join(Series).where(Episode.id == episode_id, Series.owner_id == user.id)
        .options(selectinload(Episode.pages), selectinload(Episode.series),
                 selectinload(Episode.cast).selectinload(EpisodeCharacter.character))
    )).scalar_one_or_none()
    if not episode:
        raise HTTPException(404, "Épisode introuvable.")
    return episode


async def reserve_or_402(session: AsyncSession, user: User, episode: Episode) -> None:
    try:
        await usage.reserve(session, user.id, episode.id, await remaining_images(session, episode))
    except usage.InsufficientCredits as e:
        await session.rollback()
        raise HTTPException(402, {"code": "insufficient_credits", "message": str(e), "needed": e.needed, "balance": e.balance}) from None


@router.post("/series/{series_id}/episodes", status_code=202)
async def create_episode(series_id: str, body: EpisodeIn, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """Admission d'un nouvel épisode : limites du plan, modération du texte saisi, réserve de crédits, puis file d'attente."""
    series = await owned_series(session, user, series_id)
    if any(e.status in RUNNING for e in series.episodes):
        raise HTTPException(409, "Un épisode de cette série est déjà en cours de génération.")
    if any(e.status == "failed" for e in series.episodes):
        raise HTTPException(409, {"code": "episode_failed", "message": "Un épisode de cette série est interrompu : reprenez-le ou abandonnez-le (page de l'épisode) avant d'en lancer un nouveau."})

    plan, _ = await current_plan(session, user.id)
    if not MIN_PAGES <= body.page_count <= plan.max_pages:
        raise limit(f"Le plan {plan.name} permet de {MIN_PAGES} à {plan.max_pages} pages par épisode.")
    ids = list(dict.fromkeys(body.character_ids))
    if len(ids) > plan.max_characters:
        raise limit(f"Le plan {plan.name} permet {plan.max_characters} personnages par épisode.")
    if series.palette == "color" and not plan.color:
        raise limit(f"La couleur n'est pas incluse dans le plan {plan.name}.")
    cast = [c for c in series.characters if c.id in ids]
    if len(cast) != len(ids):
        raise HTTPException(422, "Un des personnages n'appartient pas à cette série.")

    await refuse_blocked(session, user, body.direction)
    refuse_protected(body.direction)
    await budget.guard(session)

    number = (await session.execute(select(func.coalesce(func.max(Episode.number), 0)).where(Episode.series_id == series.id))).scalar_one() + 1
    episode = Episode(series_id=series.id, number=number, direction=body.direction, page_count=body.page_count)
    session.add(episode)
    await session.flush()
    session.add_all(EpisodeCharacter(episode_id=episode.id, character_id=c.id) for c in cast)
    await session.flush()
    await reserve_or_402(session, user, episode)
    await session.commit()
    await enqueue("run_episode", episode.id)
    return {"id": episode.id, "number": number, "status": episode.status}


async def episode_out(session: AsyncSession, e: Episode) -> dict:
    """État complet d'un épisode (épisode chargé avec ses pages, sa série et sa distribution)."""
    return {
        "id": e.id, "series_id": e.series_id, "number": e.number, "title": e.title, "status": e.status, "error": e.error,
        "page_count": e.page_count, "direction": e.direction, "summary": e.summary,
        "cast": [{"id": ec.character.id, "name": ec.character.name, "sheet_url": storage.url(ec.character.sheet_path)} for ec in e.cast],
        "pages": [{"id": p.id, "number": p.number, "status": p.status, "url": storage.url(p.image_path), "attempts": p.attempts,
                   "editor_note": p.editor_note} for p in e.pages],
        "usage": await usage.episode_usage(session, e.id),
        "share_url": f"{get_settings().frontend_url.split(',')[0].strip().rstrip('/')}/lire/{e.share_token}" if e.share_token else None,
    }


@router.get("/episodes/{episode_id}")
async def get_episode(episode_id: str, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """État complet de l'épisode ; le frontend l'interroge toutes les 2 s pendant la génération."""
    return await episode_out(session, await owned_episode(session, user, episode_id))


@router.get("/episodes/{episode_id}/usage")
async def get_usage(episode_id: str, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """Tokens, images et crédits de l'épisode, avec le détail par étape."""
    e = await owned_episode(session, user, episode_id)
    return await usage.episode_usage(session, e.id)


@router.post("/episodes/{episode_id}/resume", status_code=202)
async def resume(episode_id: str, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """Reprend un épisode interrompu : seul ce qui manque est réservé puis dessiné."""
    e = await owned_episode(session, user, episode_id)
    if e.status != "failed":
        raise HTTPException(409, "Seul un épisode interrompu peut être repris.")
    await budget.guard(session)
    for p in e.pages:
        if p.status == "failed":
            p.status = "pending"
    await reserve_or_402(session, user, e)
    e.status, e.error = "queued", ""
    await session.commit()
    await enqueue("run_episode", e.id)
    return {"id": e.id, "status": e.status}


async def abandon_episode(session: AsyncSession, e: Episode) -> None:
    """Abandon d'un épisode interrompu ou refusé : rien n'est plus dessiné, la réserve restante est rendue.
    Les images déjà livrées restent facturées et visibles."""
    if e.status not in ("failed", "blocked"):
        raise HTTPException(409, "Seul un épisode interrompu ou refusé peut être abandonné.")
    e.status = "canceled"
    await usage.settle(session, e.series.owner_id, e.id, await delivered_images(session, e.id))


@router.post("/episodes/{episode_id}/abandon")
async def abandon(episode_id: str, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """L'auteur abandonne un épisode bloqué pour pouvoir lancer le suivant."""
    e = await owned_episode(session, user, episode_id)
    await abandon_episode(session, e)
    await session.commit()
    return {"id": e.id, "status": e.status}


@router.post("/pages/{page_id}/redraw", status_code=202)
async def redraw(page_id: str, body: RedrawIn, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """Redessine une page avec une remarque de l'utilisateur (1 crédit, plans payants)."""
    page = await session.get(Page, page_id)
    if not page:
        raise HTTPException(404, "Page introuvable.")
    e = await owned_episode(session, user, page.episode_id)
    plan, _ = await current_plan(session, user.id)
    if not plan.redraw:
        raise limit(f"Le redessin à la demande n'est pas inclus dans le plan {plan.name}.")
    if e.status in RUNNING or e.script is None:
        raise HTTPException(409, "L'épisode est encore en cours de génération.")
    await refuse_blocked(session, user, body.note)
    await budget.guard(session)
    try:
        await usage.reserve(session, user.id, e.id, 1)
    except usage.InsufficientCredits as err:
        raise HTTPException(402, {"code": "insufficient_credits", "message": str(err)}) from None
    await session.commit()
    await enqueue("redraw_page", page.id, body.note)
    return {"id": page.id, "status": "pending"}
