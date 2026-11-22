"""Tableau de bord d'administration : vue d'ensemble, utilisateurs, épisodes, paiements, journal.

Toutes les routes exigent un compte administrateur. Chaque action qui modifie quelque
chose (crédits, plan, suspension, rôle) est inscrite dans le journal `admin_actions`."""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import budget, usage
from app.db import get_session
from app.models import (
    AdminAction,
    CreditLedger,
    Episode,
    EpisodeCharacter,
    ModerationEvent,
    Payment,
    PaymentIntent,
    Series,
    Subscription,
    UsageEvent,
    User,
    now,
)
from app.plans import PLANS
from app.routers.episodes import episode_out
from app.schemas import AdminCreditsIn, AdminPlanIn, AdminRoleIn, AdminStatusIn
from app.security import admin_user
from app.services import aware, current_plan

router = APIRouter(prefix="/admin", tags=["administration"], dependencies=[Depends(admin_user)])
PAGE_SIZE = 25
DAYS = 30


def page_of(items: list, total: int, page: int) -> dict:
    return {"items": items, "total": total, "page": page, "size": PAGE_SIZE, "pages": max(1, -(-total // PAGE_SIZE))}


def log(session: AsyncSession, admin: User, action: str, target_type: str, target_id: str, detail: str) -> None:
    session.add(AdminAction(admin_id=admin.id, admin_email=admin.email, action=action,
                            target_type=target_type, target_id=target_id, detail=detail[:1000]))


def iso(dt: datetime | None) -> str | None:
    return aware(dt).isoformat() if dt else None


async def credits_by_user(session: AsyncSession, user_ids: list[str]) -> dict[str, int]:
    if not user_ids:
        return {}
    rows = await session.execute(select(CreditLedger.user_id, func.sum(CreditLedger.delta))
                                 .where(CreditLedger.user_id.in_(user_ids)).group_by(CreditLedger.user_id))
    return {u: int(t or 0) for u, t in rows}


async def cost_by_episode(session: AsyncSession, episode_ids: list[str]) -> dict[str, dict]:
    if not episode_ids:
        return {}
    rows = await session.execute(
        select(UsageEvent.episode_id, func.sum(UsageEvent.cost_micro_usd), func.sum(UsageEvent.images),
               func.sum(UsageEvent.input_tokens + UsageEvent.output_tokens))
        .where(UsageEvent.episode_id.in_(episode_ids)).group_by(UsageEvent.episode_id))
    return {e: {"cost_usd": (c or 0) / 1e6, "images": int(i or 0), "tokens": int(t or 0)} for e, c, i, t in rows}


# ─── Vue d'ensemble ───────────────────────────────────────────────────────────

@router.get("/overview")
async def overview(session: AsyncSession = Depends(get_session)):
    """Les chiffres clés de la plateforme et leur évolution jour par jour sur 30 jours."""
    t = now()
    since, week = t - timedelta(days=DAYS), t - timedelta(days=7)
    scalar = lambda q: session.scalar(q)  # noqa: E731

    users_total = await scalar(select(func.count()).select_from(User))
    users_suspended = await scalar(select(func.count()).select_from(User).where(User.is_active.is_(False)))
    subs = (await session.execute(select(Subscription.plan, Subscription.period_end))).all()
    paying = Counter(p for p, end in subs if aware(end) > t)

    revenue = defaultdict(lambda: {"all": 0, "month": 0, "count": 0})
    donations = {"all": 0, "month": 0, "count": 0}   # dons en FCFA, hors chiffre d'affaires
    for amount, currency, created, product in (await session.execute(select(Payment.amount, Payment.currency, Payment.created_at, Payment.product))).all():
        r = donations if product == "don" else revenue[currency]
        r["all"] += amount
        r["count"] += 1
        if aware(created) >= since:
            r["month"] += amount
    intents = Counter(s for s, in (await session.execute(select(PaymentIntent.status).where(PaymentIntent.created_at >= since))).all())

    ep_status = Counter(s for s, in (await session.execute(select(Episode.status))).all())
    debited = -(await scalar(select(func.coalesce(func.sum(CreditLedger.delta), 0)).where(CreditLedger.episode_id.is_not(None))))
    outstanding = await scalar(select(func.coalesce(func.sum(CreditLedger.delta), 0)))
    cost_all = await scalar(select(func.coalesce(func.sum(UsageEvent.cost_micro_usd), 0))) / 1e6
    cost_month = await scalar(select(func.coalesce(func.sum(UsageEvent.cost_micro_usd), 0)).where(UsageEvent.created_at >= since)) / 1e6
    images_all = await scalar(select(func.coalesce(func.sum(UsageEvent.images), 0)))
    mod_week = Counter(a for a, in (await session.execute(select(ModerationEvent.action).where(ModerationEvent.created_at >= week))).all())

    # Séries quotidiennes, regroupées ici : le même code marche sur SQLite et PostgreSQL.
    days = [(t - timedelta(days=DAYS - 1 - i)).date() for i in range(DAYS)]
    daily = {d: {"date": d.isoformat(), "signups": 0, "episodes": 0, "revenue_xaf": 0, "cost_usd": 0.0} for d in days}

    def bump(when: datetime, key: str, value: float = 1) -> None:
        d: date = aware(when).date()
        if d in daily:
            daily[d][key] += value
    for (c,) in (await session.execute(select(User.created_at).where(User.created_at >= since))).all():
        bump(c, "signups")
    for (c,) in (await session.execute(select(Episode.created_at).where(Episode.created_at >= since))).all():
        bump(c, "episodes")
    for c, amount, cur in (await session.execute(select(Payment.created_at, Payment.amount, Payment.currency).where(Payment.created_at >= since, Payment.product != "don"))).all():
        if cur == "XAF":
            bump(c, "revenue_xaf", amount)
    for c, cost in (await session.execute(select(UsageEvent.created_at, UsageEvent.cost_micro_usd).where(UsageEvent.created_at >= since))).all():
        bump(c, "cost_usd", (cost or 0) / 1e6)

    problems = (await session.execute(
        select(Episode, Series.title, User.email).join(Series, Episode.series_id == Series.id).join(User, Series.owner_id == User.id)
        .where(Episode.status.in_(("failed", "blocked"))).order_by(Episode.created_at.desc()).limit(6))).all()
    events = (await session.execute(
        select(ModerationEvent, User.email).join(User, ModerationEvent.user_id == User.id, isouter=True)
        .order_by(ModerationEvent.created_at.desc()).limit(6))).all()

    return {
        "users": {"total": users_total, "suspended": users_suspended,
                  "new_7d": await scalar(select(func.count()).select_from(User).where(User.created_at >= week)),
                  "new_30d": await scalar(select(func.count()).select_from(User).where(User.created_at >= since)),
                  "paying": {p: paying.get(p, 0) for p in ("creator", "studio")}},
        "revenue": dict(revenue),
        "donations": donations,
        "payments": {"pending_30d": intents.get("pending", 0), "failed_30d": intents.get("failed", 0), "paid_30d": intents.get("paid", 0)},
        "episodes": {"total": sum(ep_status.values()), "by_status": dict(ep_status),
                     "running": sum(ep_status.get(s, 0) for s in ("queued", "designing", "writing", "moderating", "drawing"))},
        "credits": {"debited": debited, "outstanding": outstanding, "images": images_all},
        "ai": {"cost_usd_all": round(cost_all, 4), "cost_usd_30d": round(cost_month, 4),
               "cost_per_credit_usd": round(cost_all / debited, 4) if debited else None},
        "moderation": {"blocked_7d": mod_week.get("block", 0), "flagged_7d": mod_week.get("flag", 0)},
        "daily": list(daily.values()),
        "problems": [{"id": e.id, "number": e.number, "title": e.title, "status": e.status, "error": e.error,
                      "series_title": st, "owner_email": em, "created_at": iso(e.created_at)} for e, st, em in problems],
        "moderation_events": [{"id": m.id, "checkpoint": m.checkpoint, "action": m.action, "rule": m.rule, "excerpt": m.excerpt,
                               "user_email": em, "created_at": iso(m.created_at)} for m, em in events],
        "budget": await budget.status(session),
        "generated_at": t.isoformat(),
    }


# ─── Utilisateurs ─────────────────────────────────────────────────────────────

@router.get("/users")
async def users(q: str = "", status: str = Query("all", pattern="^(all|active|suspended|admin)$"), page: int = Query(1, ge=1),
                session: AsyncSession = Depends(get_session)):
    query = select(User)
    if q.strip():
        like = f"%{q.strip().lower()}%"
        query = query.where(or_(func.lower(User.email).like(like), func.lower(User.display_name).like(like)))
    if status == "active":
        query = query.where(User.is_active.is_(True))
    elif status == "suspended":
        query = query.where(User.is_active.is_(False))
    elif status == "admin":
        query = query.where(User.is_admin.is_(True))
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = (await session.execute(query.order_by(User.created_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).scalars().all()
    ids = [u.id for u in rows]
    credits = await credits_by_user(session, ids)
    eps = dict((await session.execute(select(Series.owner_id, func.count(Episode.id)).join(Episode, Episode.series_id == Series.id)
                                      .where(Series.owner_id.in_(ids)).group_by(Series.owner_id))).all()) if ids else {}
    last = dict((await session.execute(select(Series.owner_id, func.max(Episode.created_at)).join(Episode, Episode.series_id == Series.id)
                                       .where(Series.owner_id.in_(ids)).group_by(Series.owner_id))).all()) if ids else {}
    items = []
    for u in rows:
        plan, _ = await current_plan(session, u.id)
        items.append({"id": u.id, "email": u.email, "display_name": u.display_name, "is_admin": u.is_admin, "is_active": u.is_active,
                      "plan": plan.id, "plan_name": plan.name, "credits": credits.get(u.id, 0), "episodes": eps.get(u.id, 0),
                      "last_episode_at": iso(last.get(u.id)), "created_at": iso(u.created_at)})
    return page_of(items, total, page)


async def get_user_or_404(session: AsyncSession, user_id: str) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(404, "Utilisateur introuvable.")
    return user


@router.get("/users/{user_id}")
async def user_detail(user_id: str, session: AsyncSession = Depends(get_session)):
    u = await get_user_or_404(session, user_id)
    plan, sub = await current_plan(session, u.id)
    buckets = dict((await session.execute(select(CreditLedger.bucket, func.sum(CreditLedger.delta))
                                          .where(CreditLedger.user_id == u.id).group_by(CreditLedger.bucket))).all())
    ledger = (await session.execute(select(CreditLedger).where(CreditLedger.user_id == u.id)
                                    .order_by(CreditLedger.created_at.desc()).limit(60))).scalars().all()
    payments = (await session.execute(select(Payment).where(Payment.user_id == u.id).order_by(Payment.created_at.desc()))).scalars().all()
    intents = (await session.execute(select(PaymentIntent).where(PaymentIntent.user_id == u.id)
                                     .order_by(PaymentIntent.created_at.desc()).limit(20))).scalars().all()
    episodes = (await session.execute(select(Episode, Series.title).join(Series).where(Series.owner_id == u.id)
                                      .order_by(Episode.created_at.desc()).limit(50))).all()
    costs = await cost_by_episode(session, [e.id for e, _ in episodes])
    mods = (await session.execute(select(ModerationEvent).where(ModerationEvent.user_id == u.id)
                                  .order_by(ModerationEvent.created_at.desc()).limit(30))).scalars().all()
    actions = (await session.execute(select(AdminAction).where(AdminAction.target_type == "user", AdminAction.target_id == u.id)
                                     .order_by(AdminAction.created_at.desc()).limit(30))).scalars().all()
    return {
        "id": u.id, "email": u.email, "display_name": u.display_name, "is_admin": u.is_admin, "is_active": u.is_active,
        "created_at": iso(u.created_at),
        "plan": {"id": plan.id, "name": plan.name},
        "subscription": {"plan": sub.plan, "status": sub.status, "provider": sub.provider, "period_end": iso(sub.period_end)} if sub else None,
        "credits": {"total": sum(int(v or 0) for v in buckets.values()), "monthly": int(buckets.get("monthly") or 0), "pack": int(buckets.get("pack") or 0)},
        "ledger": [{"id": c.id, "delta": c.delta, "bucket": c.bucket, "kind": c.kind, "episode_id": c.episode_id, "note": c.note,
                    "created_at": iso(c.created_at)} for c in ledger],
        "payments": [{"id": p.id, "provider": p.provider, "product": p.product, "amount": p.amount, "currency": p.currency,
                      "external_ref": p.external_ref, "created_at": iso(p.created_at)} for p in payments],
        "payment_intents": [{"reference": i.reference, "product": i.product, "amount": i.amount, "currency": i.currency,
                             "operator": i.operator, "status": i.status, "error": i.error, "created_at": iso(i.created_at)} for i in intents],
        "episodes": [{"id": e.id, "number": e.number, "title": e.title, "series_title": st, "status": e.status, "page_count": e.page_count,
                      "created_at": iso(e.created_at), **costs.get(e.id, {"cost_usd": 0, "images": 0, "tokens": 0})} for e, st in episodes],
        "moderation_events": [{"id": m.id, "checkpoint": m.checkpoint, "action": m.action, "rule": m.rule, "excerpt": m.excerpt,
                               "created_at": iso(m.created_at)} for m in mods],
        "admin_actions": [{"id": a.id, "action": a.action, "detail": a.detail, "admin_email": a.admin_email,
                           "created_at": iso(a.created_at)} for a in actions],
    }


@router.post("/users/{user_id}/credits")
async def adjust_credits(user_id: str, body: AdminCreditsIn, admin: User = Depends(admin_user), session: AsyncSession = Depends(get_session)):
    """Ajoute des crédits (compartiment pack : ils n'expirent pas) ou en retire, sans descendre sous zéro."""
    u = await get_user_or_404(session, user_id)
    if body.amount == 0:
        raise HTTPException(422, "Le montant ne peut pas être nul.")
    note = f"admin : {body.reason}"
    if body.amount > 0:
        await usage.grant(session, u.id, body.amount, "pack", note)
    else:
        balance = await usage.balance(session, u.id)
        take = -body.amount
        if take > balance:
            raise HTTPException(422, f"Le solde n'est que de {balance} crédits.")
        buckets = dict((await session.execute(select(CreditLedger.bucket, func.sum(CreditLedger.delta))
                                              .where(CreditLedger.user_id == u.id).group_by(CreditLedger.bucket))).all())
        for bucket in ("monthly", "pack"):
            part = min(take, max(0, int(buckets.get(bucket) or 0)))
            if part:
                session.add(CreditLedger(user_id=u.id, delta=-part, bucket=bucket, kind="expire", note=note))
                take -= part
    log(session, admin, "credits", "user", u.id, f"{body.amount:+d} crédits — {body.reason}")
    await session.commit()
    return {"credits": await usage.balance(session, u.id)}


@router.post("/users/{user_id}/plan")
async def set_plan(user_id: str, body: AdminPlanIn, admin: User = Depends(admin_user), session: AsyncSession = Depends(get_session)):
    """Offre un plan pour une durée donnée (partenaire, geste commercial), ou ramène au plan gratuit."""
    u = await get_user_or_404(session, user_id)
    sub = await session.get(Subscription, u.id)
    if body.plan == "free":
        if sub:
            sub.status, sub.period_end = "canceled", now()
        log(session, admin, "plan", "user", u.id, f"retour au plan gratuit — {body.reason}")
    else:
        plan = PLANS[body.plan]
        if sub is None:
            sub = Subscription(user_id=u.id, plan=plan.id, provider="admin", period_end=now())
            session.add(sub)
        sub.plan, sub.status, sub.provider = plan.id, "active", "admin"
        sub.period_end = now() + timedelta(days=body.days)
        if body.grant_credits:
            await usage.renew_monthly(session, u.id, plan.credits, f"plan {plan.name} offert")
        log(session, admin, "plan", "user", u.id,
            f"plan {plan.name} pour {body.days} j{', avec ' + str(plan.credits) + ' crédits' if body.grant_credits else ''} — {body.reason}")
    await session.commit()
    return {"ok": True}


@router.post("/users/{user_id}/status")
async def set_status(user_id: str, body: AdminStatusIn, admin: User = Depends(admin_user), session: AsyncSession = Depends(get_session)):
    u = await get_user_or_404(session, user_id)
    if u.id == admin.id and not body.active:
        raise HTTPException(422, "Vous ne pouvez pas suspendre votre propre compte.")
    u.is_active = body.active
    log(session, admin, "reactivate" if body.active else "suspend", "user", u.id, body.reason)
    await session.commit()
    return {"is_active": u.is_active}


@router.post("/users/{user_id}/role")
async def set_role(user_id: str, body: AdminRoleIn, admin: User = Depends(admin_user), session: AsyncSession = Depends(get_session)):
    u = await get_user_or_404(session, user_id)
    if u.id == admin.id and not body.is_admin:
        raise HTTPException(422, "Vous ne pouvez pas retirer vos propres droits d'administrateur.")
    u.is_admin = body.is_admin
    log(session, admin, "role", "user", u.id, "devient administrateur" if body.is_admin else "n'est plus administrateur")
    await session.commit()
    return {"is_admin": u.is_admin}


# ─── Épisodes ─────────────────────────────────────────────────────────────────

@router.get("/episodes")
async def episodes(status: str = "", q: str = "", page: int = Query(1, ge=1), session: AsyncSession = Depends(get_session)):
    query = select(Episode, Series.title, User.email, User.id).join(Series, Episode.series_id == Series.id).join(User, Series.owner_id == User.id)
    if status == "running":
        query = query.where(Episode.status.in_(("queued", "designing", "writing", "moderating", "drawing")))
    elif status:
        query = query.where(Episode.status == status)
    if q.strip():
        like = f"%{q.strip().lower()}%"
        query = query.where(or_(func.lower(User.email).like(like), func.lower(Series.title).like(like), func.lower(Episode.title).like(like)))
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = (await session.execute(query.order_by(Episode.created_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).all()
    costs = await cost_by_episode(session, [e.id for e, *_ in rows])
    credits = dict((await session.execute(select(CreditLedger.episode_id, func.sum(CreditLedger.delta))
                                          .where(CreditLedger.episode_id.in_([e.id for e, *_ in rows])).group_by(CreditLedger.episode_id))).all()) if rows else {}
    items = [{"id": e.id, "number": e.number, "title": e.title, "status": e.status, "error": e.error, "page_count": e.page_count,
              "series_title": st, "owner_email": em, "owner_id": uid, "created_at": iso(e.created_at),
              "credits": -int(credits.get(e.id) or 0), **costs.get(e.id, {"cost_usd": 0, "images": 0, "tokens": 0})}
             for e, st, em, uid in rows]
    return page_of(items, total, page)


@router.get("/episodes/{episode_id}")
async def episode_detail(episode_id: str, session: AsyncSession = Depends(get_session)):
    """Un épisode de n'importe quel utilisateur, avec son coût réel par étape et ses refus de modération."""
    e = (await session.execute(select(Episode).where(Episode.id == episode_id).options(
        selectinload(Episode.series), selectinload(Episode.pages),
        selectinload(Episode.cast).selectinload(EpisodeCharacter.character)))).scalar_one_or_none()
    if not e:
        raise HTTPException(404, "Épisode introuvable.")
    owner = await session.get(User, e.series.owner_id)
    cost = (await session.execute(select(UsageEvent.stage, UsageEvent.model, func.count(), func.sum(UsageEvent.cost_micro_usd))
                                  .where(UsageEvent.episode_id == e.id).group_by(UsageEvent.stage, UsageEvent.model))).all()
    mods = (await session.execute(select(ModerationEvent).where(ModerationEvent.episode_id == e.id)
                                  .order_by(ModerationEvent.created_at.desc()))).scalars().all()
    return {**await episode_out(session, e), "series_title": e.series.title, "premise": e.series.premise,
            "owner": {"id": owner.id, "email": owner.email} if owner else None, "created_at": iso(e.created_at),
            "cost": [{"stage": s, "model": m, "calls": n, "cost_usd": (c or 0) / 1e6} for s, m, n, c in cost],
            "cost_usd": sum((c or 0) for *_, c in cost) / 1e6,
            "moderation_events": [{"id": m.id, "checkpoint": m.checkpoint, "action": m.action, "rule": m.rule, "excerpt": m.excerpt,
                                   "created_at": iso(m.created_at)} for m in mods]}


# ─── Paiements ────────────────────────────────────────────────────────────────

@router.get("/payments")
async def payments(page: int = Query(1, ge=1), session: AsyncSession = Depends(get_session)):
    query = select(Payment, User.email).join(User, Payment.user_id == User.id)
    total = await session.scalar(select(func.count()).select_from(Payment))
    rows = (await session.execute(query.order_by(Payment.created_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).all()
    return page_of([{"id": p.id, "user_id": p.user_id, "user_email": em, "provider": p.provider, "product": p.product, "amount": p.amount,
                     "currency": p.currency, "external_ref": p.external_ref, "created_at": iso(p.created_at)} for p, em in rows], total, page)


@router.get("/payment-intents")
async def payment_intents(status: str = Query("", pattern="^(|pending|paid|failed)$"), page: int = Query(1, ge=1),
                          session: AsyncSession = Depends(get_session)):
    """Toutes les demandes de paiement, y compris celles restées en attente ou refusées."""
    query = select(PaymentIntent, User.email).join(User, PaymentIntent.user_id == User.id)
    if status:
        query = query.where(PaymentIntent.status == status)
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = (await session.execute(query.order_by(PaymentIntent.created_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).all()
    stale = now() - timedelta(minutes=15)
    return page_of([{"reference": i.reference, "user_id": i.user_id, "user_email": em, "product": i.product, "amount": i.amount,
                     "currency": i.currency, "operator": i.operator, "provider_ref": i.provider_ref, "status": i.status, "error": i.error,
                     "stale": i.status == "pending" and aware(i.created_at) < stale, "created_at": iso(i.created_at)}
                    for i, em in rows], total, page)


# ─── Journal d'administration ─────────────────────────────────────────────────

@router.get("/actions")
async def actions(page: int = Query(1, ge=1), session: AsyncSession = Depends(get_session)):
    total = await session.scalar(select(func.count()).select_from(AdminAction))
    rows = (await session.execute(select(AdminAction).order_by(AdminAction.created_at.desc())
                                  .offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).scalars().all()
    return page_of([{"id": a.id, "admin_email": a.admin_email, "action": a.action, "target_type": a.target_type, "target_id": a.target_id,
                     "detail": a.detail, "created_at": iso(a.created_at)} for a in rows], total, page)


@router.get("/healthcheck")
async def healthcheck():
    """Permet au front de vérifier les droits d'administrateur sans rien charger d'autre."""
    return {"ok": True, "at": datetime.now(timezone.utc).isoformat()}
