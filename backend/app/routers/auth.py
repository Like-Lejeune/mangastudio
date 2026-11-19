"""Comptes : inscription, connexion, profil (plan, limites, solde)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import usage
from app.db import get_session
from app.models import User
from app.plans import PLANS
from app.schemas import Login, Register
from app.security import create_token, current_user, hash_password, verify_password
from app.services import current_plan

router = APIRouter(tags=["comptes"])


@router.post("/auth/register", status_code=201)
async def register(body: Register, session: AsyncSession = Depends(get_session)):
    email = body.email.lower()
    if (await session.execute(select(User.id).where(User.email == email))).first():
        raise HTTPException(409, "Un compte existe déjà avec cette adresse.")
    # Le tout premier compte créé est administrateur (pratique à l'installation).
    first = (await session.execute(select(func.count()).select_from(User))).scalar_one() == 0
    user = User(email=email, display_name=body.display_name, password_hash=hash_password(body.password), is_admin=first)
    session.add(user)
    await session.flush()
    # Crédits de bienvenue : une seule fois, dans le compartiment qui n'expire pas.
    await usage.grant(session, user.id, PLANS["free"].credits, "pack", "bienvenue")
    await session.commit()
    return {"token": create_token(user.id)}


@router.post("/auth/login")
async def login(body: Login, session: AsyncSession = Depends(get_session)):
    user = (await session.execute(select(User).where(User.email == body.email.lower()))).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Adresse ou mot de passe incorrect.")
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
