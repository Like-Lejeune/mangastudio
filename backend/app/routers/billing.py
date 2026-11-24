"""Plans et paiements : mobile money via TrustChange, carte via Stripe (après le lancement)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing import trust
from app.billing import trustchange_client as tc
from app.billing.base import apply_event
from app.config import get_settings
from app.db import get_session
from app.models import PaymentIntent, User
from app.plans import PACKS, PLANS
from app.schemas import CheckoutIn
from app.security import verified_user

router = APIRouter(tags=["facturation"])


def require_trust() -> None:
    if not tc.is_enabled():
        raise HTTPException(503, "Le paiement mobile money n'est pas encore configuré.")


@router.get("/plans")
async def plans():
    return {
        "plans": [{"id": p.id, "name": p.name, "credits": p.credits, "max_characters": p.max_characters, "max_pages": p.max_pages,
                   "color": p.color, "redraw": p.redraw, "price_usd_cents": p.price_usd_cents, "price_xaf": p.price_xaf}
                  for p in PLANS.values()],
        "pack": {"credits": PACKS["pack"].credits, "price_usd_cents": PACKS["pack"].price_usd_cents, "price_xaf": PACKS["pack"].price_xaf},
        "packs": [{"id": p.id, "credits": p.credits, "price_xaf": p.price_xaf, "price_usd_cents": p.price_usd_cents} for p in PACKS.values()],
    }


@router.get("/billing/operators")
async def operators(user: User = Depends(verified_user)):
    """Opérateurs mobile money proposés par TrustChange (code à renvoyer dans `operator` au paiement)."""
    require_trust()
    try:
        return await tc.get_operators()
    except tc.TrustChangeError as e:
        raise HTTPException(502, e.message) from None


@router.post("/billing/checkout", status_code=202)
async def checkout(body: CheckoutIn, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """Démarre un paiement. Mobile money : le client valide sur son téléphone, puis le front
    interroge GET /billing/payments/{reference} jusqu'à `paid` ou `failed`."""
    if body.product == "don" and (body.provider != "trust" or not body.amount):
        raise HTTPException(422, "Un don se fait par mobile money, avec un montant d'au moins 500 FCFA.")
    if body.provider == "stripe" and body.product in ("pack15", "pack25"):
        raise HTTPException(422, "Les petits packs se paient par mobile money.")
    if body.provider == "stripe":
        if not get_settings().stripe_secret_key:
            raise HTTPException(503, "Le paiement par carte n'est pas encore disponible.")
        from app.billing.stripe_provider import StripeProvider
        return await StripeProvider().checkout(user, body.product)
    require_trust()
    if not body.phone or not body.operator:
        raise HTTPException(422, "Indiquez le numéro de téléphone et l'opérateur.")
    try:
        intent = await trust.start(session, user, body.product, body.phone, body.operator, amount=body.amount)
    except tc.TrustChangeError as e:
        raise HTTPException(502, {"code": "payment_failed", "message": e.message}) from None
    return {**trust.intent_out(intent), "message": "Validez le paiement sur votre téléphone."}


@router.get("/billing/payments/{reference}")
async def payment_status(reference: str, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """État d'un paiement. Tant qu'il est en attente, on relit la transaction chez TrustChange :
    le plan s'active même si la notification s'est perdue."""
    intent = await session.get(PaymentIntent, reference)
    if not intent or intent.user_id != user.id:
        raise HTTPException(404, "Paiement introuvable.")
    return trust.intent_out(await trust.reconcile(session, intent))


@router.post("/billing/webhooks/trust")
async def trust_webhook(request: Request, session: AsyncSession = Depends(get_session)):
    """Notification TrustChange. Signature et horodatage vérifiés sur le corps brut ; un rejeu ne crédite pas deux fois."""
    raw = await request.body()
    try:
        applied = await trust.handle_webhook(session, raw, {k.lower(): v for k, v in request.headers.items()})
    except (tc.TrustChangeError, ValueError):
        raise HTTPException(400, "Notification refusée.") from None
    return {"received": True, "applied": applied}


@router.post("/billing/webhooks/stripe")
async def stripe_webhook(request: Request, session: AsyncSession = Depends(get_session)):
    if not get_settings().stripe_secret_key:
        raise HTTPException(404)
    from app.billing.stripe_provider import StripeProvider
    try:
        event = StripeProvider().parse_webhook(await request.body(), {k.lower(): v for k, v in request.headers.items()})
    except Exception:  # noqa: BLE001  (signature fausse ou corps illisible)
        raise HTTPException(400, "Notification refusée.") from None
    return {"received": True, "applied": bool(event) and await apply_event(session, event)}
