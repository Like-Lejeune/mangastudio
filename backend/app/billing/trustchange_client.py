"""Client asynchrone de l'API TrustChange (https://api.trustchange.fr).

Portage de `services/trustchange_service.py` de Cashnut : mêmes endpoints, même
enveloppe, mêmes exceptions, même vérification de webhook. Seules différences :
appels asynchrones (httpx.AsyncClient, pour ne pas bloquer l'API pendant un
appel lent) et encaissement seulement — MangaStudio ne fait pas de décaissement.

Ce module ne connaît rien du métier MangaStudio : il ne touche pas à la base.
La logique (plans, crédits, intentions de paiement) est dans billing/trust.py.

Deux garde-fous de TrustChange exploités ici :
  - `externalReference` est unique par compte : rejouer la même référence
    renvoie 409 sans rien créer (voir AlreadySubmitted).
  - les webhooks sont signés en HMAC-SHA256 sur `timestamp + "." + corps brut`.
"""
import hashlib
import hmac
import json
import time
from typing import Any

import httpx

from app.config import get_settings

API_PREFIX = "/api/Integrator"
WEBHOOK_MAX_AGE_SECONDS = 300   # au-delà, rejeu probable (recommandation TrustChange)
HTTP_TIMEOUT_SECONDS = 20


class TrustChangeError(Exception):
    """Erreur renvoyée par TrustChange ou survenue en tentant de le joindre."""

    def __init__(self, message: str, status_code: int | None = None, payload: dict | None = None):
        super().__init__(message)
        self.message, self.status_code, self.payload = message, status_code, payload or {}


class Unreachable(TrustChangeError):
    """Réseau, DNS, TLS ou délai dépassé : on ne sait PAS si l'opération est partie.
    L'appelant la laisse en suspens et vérifie par référence, sans jamais rejouer à l'aveugle."""


class AlreadySubmitted(TrustChangeError):
    """409 : référence déjà utilisée. Rien n'a été créé ; l'opération d'origine existe.
    Aller lire son état avec get_transaction() plutôt que réessayer."""


class NotConfigured(TrustChangeError):
    """Aucune clé API renseignée."""


def is_enabled() -> bool:
    return bool(get_settings().trustchange_api_key)


def is_test_mode() -> bool:
    """Une clé `tc_test_…` opère sur un compte fictif aux opérations simulées."""
    return get_settings().trustchange_api_key.startswith("tc_test_")


async def _request(method: str, path: str, *, json_body: dict | None = None) -> dict[str, Any]:
    """Appelle l'API et renvoie le contenu de `data`.
    Enveloppe commune : {"data": {...}, "message": "...", "statut": "success"|"error", "statusCode": ...}."""
    s = get_settings()
    if not is_enabled():
        raise NotConfigured("TRUSTCHANGE_API_KEY non configurée.")
    url = f"{s.trustchange_base_url.rstrip('/')}{API_PREFIX}{path}"
    headers = {"X-Api-Key": s.trustchange_api_key, "Accept": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.request(method, url, json=json_body, headers=headers)
    except httpx.RequestError as exc:
        raise Unreachable(f"TrustChange injoignable : {exc}") from exc

    try:
        envelope = response.json()
    except ValueError:
        raise TrustChangeError(f"Réponse illisible de TrustChange (HTTP {response.status_code}).", response.status_code) from None

    message = envelope.get("message") or f"HTTP {response.status_code}"
    data = envelope.get("data") or {}
    if response.status_code == 409:
        raise AlreadySubmitted(message, 409, data)
    if response.status_code == 401:
        raise TrustChangeError(f"Clé API refusée : {message} (clé révoquée, invalide, ou IP non autorisée).", 401, data)
    if response.status_code >= 400 or envelope.get("statut") == "error":
        raise TrustChangeError(message, response.status_code, data)
    return data


def national_phone_number(phone: str | None, country_prefix: str = "237") -> str:
    """TrustChange attend un numéro NATIONAL, sans indicatif (« 699000000 »)."""
    if not phone:
        raise TrustChangeError("Numéro de téléphone manquant.")
    digits = "".join(c for c in phone if c.isdigit())
    if digits.startswith(country_prefix) and len(digits) > len(country_prefix):
        digits = digits[len(country_prefix):]
    if not digits:
        raise TrustChangeError(f"Numéro de téléphone inexploitable : {phone}")
    return digits


async def collect_mobile_money(*, payment_code: str, phone_number: str, amount: int, external_reference: str,
                               callback_url: str | None = None, metadata: dict | None = None) -> dict[str, Any]:
    """Demande un paiement au client, qui valide sur son téléphone.
    Réponse 202 : `transactionId`, `status` (PROCESSING), `fees`, `netAmount`. Le résultat arrive par webhook."""
    body: dict[str, Any] = {
        "paymentMethod": "MOBILE_MONEY", "paymentCode": payment_code,
        "phoneNumber": national_phone_number(phone_number), "amount": int(amount),
        "externalReference": external_reference,
    }
    if callback_url:
        body["callbackUrl"] = callback_url
    if metadata:
        body["metadata"] = json.dumps(metadata)   # texte libre, restitué tel quel dans le webhook
    return await _request("POST", "/collect", json_body=body)


async def get_transaction(reference: str) -> dict[str, Any]:
    """État d'une transaction, par `transactionId` TrustChange ou par notre référence externe."""
    return await _request("GET", f"/transaction/{reference}")


async def get_operators() -> dict[str, Any]:
    """Opérateurs Mobile Money : code, pays, devise, bornes, format du numéro."""
    return await _request("GET", "/operators")


async def resend_webhook(reference: str) -> dict[str, Any]:
    return await _request("POST", f"/transaction/{reference}/callback/resend")


def verify_webhook(raw_body: bytes, signature: str | None, timestamp: str | None) -> None:
    """Valide un webhook ; lève TrustChangeError s'il doit être refusé.
    La signature porte sur le CORPS BRUT (jamais re-sérialisé) et se compare en temps constant.
    L'horodatage est vérifié aussi : sans cela, un message capté resterait rejouable."""
    secret = get_settings().trustchange_webhook_secret
    if not secret:
        raise TrustChangeError("TRUSTCHANGE_WEBHOOK_SECRET non configuré : webhook refusé.")
    if not signature or not timestamp:
        raise TrustChangeError("Webhook sans signature ou sans horodatage.")
    try:
        sent_at = int(timestamp)
    except (TypeError, ValueError):
        raise TrustChangeError(f"Horodatage de webhook invalide : {timestamp}") from None
    age = abs(int(time.time()) - sent_at)
    if age > WEBHOOK_MAX_AGE_SECONDS:
        raise TrustChangeError(f"Webhook périmé ({age} s) — rejeu probable.")
    if not hmac.compare_digest(sign_webhook(raw_body, timestamp, secret), signature.strip().lower()):
        raise TrustChangeError("Signature de webhook invalide.")


def sign_webhook(raw_body: bytes, timestamp: str, secret: str) -> str:
    """Signature d'un corps donné (utilisée aussi par les tests)."""
    return hmac.new(secret.encode(), timestamp.encode() + b"." + raw_body, hashlib.sha256).hexdigest()
