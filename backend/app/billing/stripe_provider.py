"""Stripe : abonnement récurrent (Checkout) et pack à l'unité.

Événements écoutés :
  - invoice.paid                  → chaque facture d'abonnement payée (première et renouvellements)
  - checkout.session.completed    → pack (mode « payment ») uniquement
  - customer.subscription.deleted → résiliation
À vérifier avec la version d'API de votre compte : l'emplacement des métadonnées
d'abonnement dans la facture a changé entre versions (les deux sont lus ici)."""
import stripe

from app.billing.base import PaymentEvent
from app.config import get_settings
from app.models import User


class StripeProvider:
    name = "stripe"

    def __init__(self) -> None:
        s = get_settings()
        stripe.api_key = s.stripe_secret_key
        self.prices = {"creator": s.stripe_price_creator, "studio": s.stripe_price_studio, "pack": s.stripe_price_pack}

    async def checkout(self, user: User, product: str, phone: str | None = None) -> dict:
        s = get_settings()
        meta = {"user_id": user.id, "product": product}
        params: dict = {
            "mode": "payment" if product == "pack" else "subscription",
            "line_items": [{"price": self.prices[product], "quantity": 1}],
            "customer_email": user.email,
            "client_reference_id": user.id,
            "metadata": meta,
            "success_url": f"{s.frontend_url}/compte?paiement=ok",
            "cancel_url": f"{s.frontend_url}/abonnements",
        }
        if product != "pack":
            params["subscription_data"] = {"metadata": meta}
        session = await stripe.checkout.Session.create_async(**params)
        return {"url": session.url}

    def parse_webhook(self, body: bytes, headers: dict[str, str]) -> PaymentEvent | None:
        # Lève une exception si la signature est fausse : le routeur répond 400.
        event = stripe.Webhook.construct_event(body, headers.get("stripe-signature", ""), get_settings().stripe_webhook_secret)
        obj = event["data"]["object"]
        if event["type"] == "checkout.session.completed" and obj.get("mode") == "payment":
            meta = obj.get("metadata") or {}
            return PaymentEvent("paid", "stripe", obj["id"], meta.get("user_id", ""), meta.get("product", ""),
                                obj.get("amount_total") or 0, (obj.get("currency") or "usd").upper())
        if event["type"] == "invoice.paid":
            details = (obj.get("parent") or {}).get("subscription_details") or obj.get("subscription_details") or {}
            meta = details.get("metadata") or {}
            if not meta.get("user_id"):
                return None
            return PaymentEvent("paid", "stripe", obj["id"], meta["user_id"], meta.get("product", ""),
                                obj.get("amount_paid") or 0, (obj.get("currency") or "usd").upper(),
                                subscription_id=details.get("subscription") or obj.get("subscription"))
        if event["type"] == "customer.subscription.deleted":
            meta = obj.get("metadata") or {}
            if meta.get("user_id"):
                return PaymentEvent("canceled", "stripe", obj["id"], meta["user_id"])
        return None
