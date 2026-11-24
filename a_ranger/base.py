"""Contrat commun aux moyens de paiement, et application d'un paiement confirmé."""
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import usage
from app.models import Payment, Subscription, User, now
from app.plans import PACKS, PERIOD_DAYS, PLANS
from app.services import aware

PRODUCTS = ("creator", "studio", *PACKS, "don")


@dataclass
class PaymentEvent:
    kind: str                 # paid | canceled
    provider: str             # trust | stripe
    external_ref: str         # identifiant unique chez le prestataire
    user_id: str
    product: str = ""         # creator | studio | pack
    amount: int = 0
    currency: str = ""
    subscription_id: str | None = None


class PaymentProvider(Protocol):
    name: str

    async def checkout(self, user: User, product: str, phone: str | None = None) -> dict:
        """Démarre un paiement. Renvoie {"url": ...} (redirection) ou {"message": ...} (validation sur le téléphone)."""
        ...

    def parse_webhook(self, body: bytes, headers: dict[str, str]) -> PaymentEvent | None:
        """Vérifie la signature et traduit la notification ; None si elle ne nous concerne pas."""
        ...


async def apply_event(session: AsyncSession, event: PaymentEvent) -> bool:
    """Applique un paiement une seule fois. Renvoie False si la référence a déjà été traitée."""
    if event.kind == "canceled":
        sub = await session.get(Subscription, event.user_id)
        if sub:
            sub.status = "canceled"   # le plan reste actif jusqu'à period_end
            await session.commit()
        return True
    if event.product not in PRODUCTS:
        return False
    seen = (await session.execute(select(Payment.id).where(Payment.external_ref == event.external_ref))).first()
    if seen:
        return False
    session.add(Payment(user_id=event.user_id, provider=event.provider, external_ref=event.external_ref,
                        product=event.product, amount=event.amount, currency=event.currency))
    if event.product == "don":
        pass   # un don soutient la plateforme : rien à créditer, le paiement est seulement enregistré
    elif event.product in PACKS:
        pack = PACKS[event.product]
        await usage.grant(session, event.user_id, pack.credits, "pack", f"pack de {pack.credits} crédits")
    else:
        plan = PLANS[event.product]
        sub = await session.get(Subscription, event.user_id)
        if sub is None:
            sub = Subscription(user_id=event.user_id, plan=plan.id, provider=event.provider, period_end=now())
            session.add(sub)
        # Un renouvellement payé avant l'échéance prolonge à partir de l'échéance.
        start = max(aware(sub.period_end), now())
        sub.plan, sub.status, sub.provider = plan.id, "active", event.provider
        sub.external_id = event.subscription_id or sub.external_id
        sub.period_end = start + timedelta(days=PERIOD_DAYS)
        await usage.renew_monthly(session, event.user_id, plan.credits, f"plan {plan.name}")
    try:
        await session.commit()
    except IntegrityError:       # même webhook reçu deux fois en même temps : le second s'arrête ici
        await session.rollback()
        return False
    return True
