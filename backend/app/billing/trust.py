"""Paiement mobile money via TrustChange : logique métier MangaStudio.

Parcours :
  1. start()   : crée une intention de paiement (référence unique), puis demande
                 l'encaissement à TrustChange. Le client valide sur son téléphone.
  2. webhook   : TrustChange notifie le résultat. Après vérification de la
                 signature, on ne se fie PAS au corps : on relit la transaction
                 chez TrustChange (reconcile) avant de créditer.
  3. reconcile : aussi appelé par le front qui interroge l'état du paiement, donc
                 une notification perdue n'empêche pas l'activation du plan.

Le crédit passe par apply_event(), protégé contre les doublons : webhook rejoué,
webhook et interrogation simultanés ne créditent qu'une fois.

À CONFIRMER avec la documentation TrustChange (non visible dans le client Cashnut) :
  - les libellés de statut final, réglables par TRUSTCHANGE_SUCCESS_STATUSES et
    TRUSTCHANGE_FAILURE_STATUSES ; seul PROCESSING est certain ;
  - les noms des champs `status` et `amount` dans la réponse de /transaction.
"""
import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing import trustchange_client as tc
from app.billing.base import PaymentEvent, apply_event
from app.config import get_settings
from app.models import PaymentIntent, User, new_id
from app.plans import PACKS, PLANS

log = logging.getLogger("billing.trust")


def price_xaf(product: str) -> int:
    return PACKS[product].price_xaf if product in PACKS else PLANS[product].price_xaf


def _status(transaction: dict) -> str:
    return str(transaction.get("status") or "").upper()


async def start(session: AsyncSession, user: User, product: str, phone: str, operator: str, amount: int | None = None) -> PaymentIntent:
    """Crée l'intention puis lance l'encaissement. L'intention est enregistrée AVANT
    l'appel : si le réseau coupe, on garde la référence pour vérifier plus tard."""
    s = get_settings()
    intent = PaymentIntent(reference=f"ms{new_id()}", user_id=user.id, product=product, amount=amount if product == "don" else price_xaf(product),
                           currency="XAF", provider="trust", operator=operator)
    session.add(intent)
    await session.commit()
    try:
        data = await tc.collect_mobile_money(
            payment_code=operator, phone_number=phone, amount=intent.amount, external_reference=intent.reference,
            callback_url=f"{s.public_base_url}/billing/webhooks/trust",
            metadata={"user_id": user.id, "product": product},
        )
        intent.provider_ref = str(data.get("transactionId") or "") or None
    except tc.Unreachable:
        # Issue inconnue : l'intention reste « pending », reconcile() tranchera.
        log.warning("TrustChange injoignable pour %s : issue à vérifier", intent.reference)
    except tc.TrustChangeError as e:
        intent.status, intent.error = "failed", e.message[:255]
        await session.commit()
        raise
    await session.commit()
    return intent


async def reconcile(session: AsyncSession, intent: PaymentIntent) -> PaymentIntent:
    """Relit la transaction chez TrustChange et applique son issue. Sans effet si l'intention est déjà close."""
    if intent.status != "pending":
        return intent
    s = get_settings()
    try:
        transaction = await tc.get_transaction(intent.reference)
    except tc.TrustChangeError as e:
        if e.status_code == 404 and not intent.provider_ref:
            # TrustChange ne connaît pas la référence : la demande n'est jamais partie.
            intent.status, intent.error = "failed", "La demande de paiement n'a pas abouti. Réessayez."
            await session.commit()
        return intent
    status = _status(transaction)
    if status in s.trustchange_success_statuses:
        paid = int(float(transaction.get("amount") or 0))
        if paid < intent.amount:
            intent.status, intent.error = "failed", f"Montant reçu ({paid}) inférieur au prix ({intent.amount})."
            log.error("montant inattendu pour %s : %s", intent.reference, paid)
        else:
            await apply_event(session, PaymentEvent("paid", "trust", intent.reference, intent.user_id, intent.product, paid, intent.currency))
            intent.status = "paid"
    elif status in s.trustchange_failure_statuses:
        intent.status = "failed"
        intent.error = str(transaction.get("failureReason") or transaction.get("message") or "Paiement refusé ou annulé.")[:255]
    await session.commit()
    return intent


async def handle_webhook(session: AsyncSession, raw_body: bytes, headers: dict[str, str]) -> bool:
    """Vérifie la signature, retrouve l'intention, puis reconcile. Renvoie True si un paiement a été appliqué."""
    s = get_settings()
    tc.verify_webhook(raw_body, headers.get(s.trustchange_signature_header.lower()), headers.get(s.trustchange_timestamp_header.lower()))
    body = json.loads(raw_body)
    data = body.get("data") if isinstance(body.get("data"), dict) else body
    reference = data.get("externalReference") or data.get("external_reference")
    if not reference:
        return False
    intent = (await session.execute(select(PaymentIntent).where(PaymentIntent.reference == str(reference)))).scalar_one_or_none()
    if intent is None:
        return False   # référence d'un autre produit branché sur le même compte TrustChange
    before = intent.status
    await reconcile(session, intent)
    return before == "pending" and intent.status == "paid"


def intent_out(intent: PaymentIntent) -> dict:
    return {"reference": intent.reference, "product": intent.product, "amount": intent.amount, "currency": intent.currency,
            "status": intent.status, "error": intent.error}
