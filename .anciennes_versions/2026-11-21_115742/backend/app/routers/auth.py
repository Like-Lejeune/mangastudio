"""Comptes : inscription, connexion, profil (plan, limites, solde)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import ratelimit, usage
from app.config import get_settings
from app.db import get_session
from app.models import User
from app.plans import PLANS
from app.schemas import Login, Register
from app.security import create_token, current_user, hash_password, verify_password
from app.services import current_plan

router = APIRouter(tags=["comptes"])


@router.post("/auth/register", status_code=201)
async def register(body: Register, request: Request, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    key = f"register:{ratelimit.client_ip(request)}"
    ratelimit.check(key, settings.register_max_per_hour, 3600)
    ratelimit.add(key)
    email = body.email.lower()
    if (await session.execute(select(User.id).where(User.email == email))).first():
        raise HTTPException(409, "Un compte existe déjà avec cette adresse.")
    # Administrateur seulement si l'adresse figure dans ADMIN_EMAILS (jamais « le premier inscrit »).
    user = User(email=email, display_name=body.display_name, password_hash=hash_password(body.password),
                is_admin=email in settings.admin_email_set)
    session.add(user)
    await session.flush()
    # Crédits de bienvenue : une seule fois, dans le compartiment qui n'expire pas.
    await usage.grant(session, user.id, PLANS["free"].credits, "pack", "bienvenue")
    await session.commit()
    return {"token": create_token(user.id)}


@router.post("/auth/login")
async def login(body: Login, request: Request, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    email = body.email.lower()
    ip = ratelimit.client_ip(request)
    window = settings.login_window_minutes * 60
    per_account, per_ip = f"login:{ip}:{email}", f"login-ip:{ip}"
    ratelimit.check(per_account, settings.login_max_failures, window)
    ratelimit.check(per_ip, settings.login_max_failures_ip, window)
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        ratelimit.add(per_account)
        ratelimit.add(per_ip)
        raise HTTPException(401, "Adresse ou mot de passe incorrect.")
    ratelimit.reset(per_account)
    if not user.is_active:
        raise HTTPException(403, {"code": "account_suspended", "message": "Ce compte est suspendu. Contactez le support."})
    if email in settings.admin_email_set and not user.is_admin:
        user.is_admin = True
        await session.commit()
    return {"token": create_token(user.id)}


@router.get("/me")
async def me(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    plan, sub = await current_plan(session, user.id)
    return {
        "id": user.id, "email": user.email, "display_name": user.display_name, "is_admin": user.is_admin,
        "credits": await usage.balance(session, user.id),
        "plan": {"id": plan.id, "name": plan.name, "max_characters": plan.max_characters, "max_pages": plan.max_pages,
                 "color": plan.color, "redraw": plan.redraw},
        "subscription": {"status": sub.status, "provider": sub.provider, "period_end": sub.period_end.isoformat()} if sub else None,
    }
