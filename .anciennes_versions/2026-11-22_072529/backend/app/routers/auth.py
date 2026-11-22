"""Comptes : inscription, vérification de l'adresse, connexion, profil (plan, limites, solde)."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import mailer, ratelimit, usage
from app.config import get_settings
from app.db import get_session
from app.disposable import is_disposable
from app.models import CreditLedger, User
from app.plans import PLANS
from app.schemas import Login, Register, VerifyIn
from app.security import create_token, current_user, hash_password, verify_password
from app.services import current_plan

router = APIRouter(tags=["comptes"])
CODE_MINUTES = 30
CODE_MAX_ATTEMPTS = 5


def _hash(code: str) -> str:
    return hmac.new(get_settings().secret_key.encode(), code.encode(), hashlib.sha256).hexdigest()


def _aware(dt: datetime | None) -> datetime | None:
    return dt.replace(tzinfo=timezone.utc) if dt and dt.tzinfo is None else dt


async def welcome_credits(session: AsyncSession, user: User) -> None:
    """Crédits de bienvenue : une seule fois par compte, après vérification de l'adresse."""
    deja = (await session.execute(select(CreditLedger.id).where(CreditLedger.user_id == user.id, CreditLedger.note == "bienvenue"))).first()
    if not deja:
        await usage.grant(session, user.id, PLANS["free"].credits, "pack", "bienvenue")


async def send_new_code(session: AsyncSession, user: User) -> None:
    code = f"{secrets.randbelow(10**6):06d}"
    user.verify_code_hash = _hash(code)
    user.verify_expires_at = datetime.now(timezone.utc) + timedelta(minutes=CODE_MINUTES)
    user.verify_attempts = 0
    await session.commit()
    try:
        await mailer.send_code(user.email, user.display_name, code, CODE_MINUTES)
    except mailer.MailError:
        raise HTTPException(502, {"code": "mail_failed", "message": "L'e-mail n'a pas pu partir. Réessayez dans un instant avec « Renvoyer le code »."}) from None


@router.post("/auth/register", status_code=201)
async def register(body: Register, request: Request, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    key = f"register:{ratelimit.client_ip(request)}"
    ratelimit.check(key, settings.register_max_per_hour, 3600)
    ratelimit.add(key)
    email = body.email.strip().lower()
    if is_disposable(email):
        raise HTTPException(422, {"code": "disposable_email", "message": "Les adresses e-mail temporaires ne sont pas acceptées. Utilisez votre adresse habituelle."})
    existant = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existant and existant.email_verified:
        raise HTTPException(409, "Un compte existe déjà avec cette adresse.")
    if existant:
        # Compte jamais confirmé (adresse saisie par erreur ou par quelqu'un d'autre) : il n'a ni crédit,
        # ni série, ni paiement. Le vrai propriétaire de l'adresse peut donc le remplacer.
        await session.delete(existant)
        await session.flush()
    # Administrateur seulement si l'adresse figure dans ADMIN_EMAILS (jamais « le premier inscrit »).
    user = User(email=email, display_name=body.display_name, password_hash=hash_password(body.password),
                is_admin=email in settings.admin_email_set, email_verified=not settings.email_verification)
    session.add(user)
    await session.flush()
    if user.email_verified:
        await welcome_credits(session, user)
        await session.commit()
    else:
        await session.commit()
        try:
            await send_new_code(session, user)
        except HTTPException:
            pass   # le compte existe : la personne demandera un nouveau code depuis l'écran de vérification
    return {"token": create_token(user.id), "email_verified": user.email_verified}


@router.post("/auth/verify")
async def verify(body: VerifyIn, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    """Confirme l'adresse avec le code reçu, puis donne les crédits de bienvenue."""
    if user.email_verified:
        return {"email_verified": True}
    if not user.verify_code_hash or (_aware(user.verify_expires_at) or datetime.min.replace(tzinfo=timezone.utc)) < datetime.now(timezone.utc):
        raise HTTPException(410, {"code": "code_expired", "message": "Ce code a expiré. Demandez-en un nouveau."})
    if user.verify_attempts >= CODE_MAX_ATTEMPTS:
        raise HTTPException(429, {"code": "too_many_attempts", "message": "Trop d'essais. Demandez un nouveau code."})
    if not hmac.compare_digest(_hash(body.code.strip()), user.verify_code_hash):
        user.verify_attempts += 1
        await session.commit()
        left = CODE_MAX_ATTEMPTS - user.verify_attempts
        raise HTTPException(422, {"code": "wrong_code", "message": f"Code incorrect. Encore {left} essai{'s' if left > 1 else ''}." if left else "Code incorrect. Demandez un nouveau code."})
    user.email_verified = True
    user.verify_code_hash = None
    user.verify_expires_at = None
    await welcome_credits(session, user)
    await session.commit()
    return {"email_verified": True}


@router.post("/auth/resend-code")
async def resend_code(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)):
    if user.email_verified:
        return {"sent": False}
    ratelimit.check(f"code-minute:{user.id}", 1, 60)
    ratelimit.check(f"code-heure:{user.id}", 5, 3600)
    ratelimit.add(f"code-minute:{user.id}")
    ratelimit.add(f"code-heure:{user.id}")
    await send_new_code(session, user)
    return {"sent": True}


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
        "email_verified": user.email_verified,
        "credits": await usage.balance(session, user.id),
        "plan": {"id": plan.id, "name": plan.name, "max_characters": plan.max_characters, "max_pages": plan.max_pages,
                 "color": plan.color, "redraw": plan.redraw},
        "subscription": {"status": sub.status, "provider": sub.provider, "period_end": sub.period_end.isoformat()} if sub else None,
    }
