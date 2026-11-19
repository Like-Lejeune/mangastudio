"""Console d'administration : mots bloqués, scènes interdites, journal de modération, coûts."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import moderation
from app.db import get_session
from app.models import BlockedTerm, ModerationEvent, SceneRule, UsageEvent
from app.schemas import SceneRuleIn, TermIn
from app.security import admin_user

router = APIRouter(prefix="/admin", tags=["administration"], dependencies=[Depends(admin_user)])


@router.get("/terms")
async def list_terms(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(BlockedTerm).order_by(BlockedTerm.term))).scalars()
    return [{"id": t.id, "term": t.term, "action": t.action} for t in rows]


@router.post("/terms", status_code=201)
async def add_term(body: TermIn, session: AsyncSession = Depends(get_session)):
    """Le terme est stocké normalisé : « S3xe », « sèxe » et « sexe » donnent la même entrée."""
    term = moderation.normalize(body.term)
    if len(term) < 2:
        raise HTTPException(422, "Terme trop court après normalisation.")
    existing = (await session.execute(select(BlockedTerm).where(BlockedTerm.term == term))).scalar_one_or_none()
    if existing:
        existing.action = body.action
    else:
        existing = BlockedTerm(term=term, action=body.action)
        session.add(existing)
    await session.commit()
    return {"id": existing.id, "term": existing.term, "action": existing.action}


@router.delete("/terms/{term_id}", status_code=204)
async def delete_term(term_id: str, session: AsyncSession = Depends(get_session)):
    await session.execute(delete(BlockedTerm).where(BlockedTerm.id == term_id))
    await session.commit()


@router.get("/scene-rules")
async def list_rules(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(SceneRule).order_by(SceneRule.label))).scalars()
    return {
        "baseline": [{"label": label, "description": d} for label, d in moderation.BASELINE_RULES],   # non modifiables
        "custom": [{"id": r.id, "label": r.label, "description": r.description, "active": r.active} for r in rows],
    }


@router.post("/scene-rules", status_code=201)
async def add_rule(body: SceneRuleIn, session: AsyncSession = Depends(get_session)):
    rule = (await session.execute(select(SceneRule).where(SceneRule.label == body.label))).scalar_one_or_none()
    if rule:
        rule.description, rule.active = body.description, body.active
    else:
        rule = SceneRule(**body.model_dump())
        session.add(rule)
    await session.commit()
    return {"id": rule.id, "label": rule.label, "description": rule.description, "active": rule.active}


@router.delete("/scene-rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: str, session: AsyncSession = Depends(get_session)):
    await session.execute(delete(SceneRule).where(SceneRule.id == rule_id))
    await session.commit()


@router.get("/moderation-events")
async def events(limit: int = 100, session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(ModerationEvent).order_by(ModerationEvent.created_at.desc()).limit(min(limit, 500)))).scalars()
    return [{"id": e.id, "user_id": e.user_id, "episode_id": e.episode_id, "checkpoint": e.checkpoint, "action": e.action,
             "rule": e.rule, "excerpt": e.excerpt, "created_at": e.created_at.isoformat()} for e in rows]


@router.get("/costs")
async def costs(session: AsyncSession = Depends(get_session)):
    """Coût réel par modèle (interne) : sert à vérifier la marge de chaque crédit vendu."""
    rows = (await session.execute(
        select(UsageEvent.model, func.sum(UsageEvent.input_tokens), func.sum(UsageEvent.output_tokens),
               func.sum(UsageEvent.images), func.sum(UsageEvent.cost_micro_usd)).group_by(UsageEvent.model)
    )).all()
    return [{"model": m, "input_tokens": i or 0, "output_tokens": o or 0, "images": im or 0, "cost_usd": (c or 0) / 1e6} for m, i, o, im, c in rows]
