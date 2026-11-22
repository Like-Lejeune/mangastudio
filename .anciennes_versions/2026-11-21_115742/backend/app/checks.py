"""Contrôles de configuration au démarrage.

En production (ENVIRONMENT=production), une erreur empêche l'API de démarrer : mieux vaut un
service arrêté qu'un service ouvert avec une clé de signature connue de tous."""
import logging

from app.config import Settings

log = logging.getLogger("mangastudio.config")

DEFAULT_SECRETS = {"dev-secret-a-changer-en-production-0123456789", "change-moi-par-une-longue-chaine-aleatoire", ""}


def problems(s: Settings) -> tuple[list[str], list[str]]:
    """(erreurs bloquantes en production, avertissements)."""
    errors, warnings = [], []
    if s.secret_key in DEFAULT_SECRETS or len(s.secret_key) < 32:
        errors.append("SECRET_KEY absente, trop courte (32 caractères minimum) ou laissée à sa valeur d'exemple : openssl rand -hex 32")
    origins = [o.strip() for o in s.frontend_url.split(",") if o.strip()]
    if not origins or any(not o.startswith("https://") for o in origins):
        errors.append("FRONTEND_URL doit lister les adresses https:// du site (séparées par des virgules).")
    if not s.public_base_url.startswith("https://"):
        errors.append("PUBLIC_BASE_URL doit être l'adresse https:// de l'API.")
    if s.database_url.startswith("sqlite"):
        errors.append("DATABASE_URL pointe vers SQLite : utilisez PostgreSQL en production.")
    if "fake" in (s.writer_provider, s.checker_provider, s.image_provider):
        errors.append("Un fournisseur IA est resté sur « fake » : les clients recevraient des pages vides.")
    if "meta_muse" in (s.writer_provider, s.checker_provider, s.image_provider) and not s.meta_api_key:
        errors.append("META_API_KEY est vide alors que Muse est utilisé.")
    if not s.admin_email_set:
        warnings.append("ADMIN_EMAILS est vide : personne ne pourra ouvrir l'administration.")
    if s.trustchange_api_key and not s.trustchange_webhook_secret:
        errors.append("TRUSTCHANGE_WEBHOOK_SECRET est vide : les notifications de paiement ne seraient pas vérifiées.")
    if s.trustchange_api_key.startswith("tc_test_"):
        warnings.append("TrustChange est en mode test (tc_test_) : aucun argent réel n'est encaissé.")
    if s.ai_daily_budget_usd <= 0:
        warnings.append("AI_DAILY_BUDGET_USD n'est pas réglé : aucune limite de dépense IA par jour.")
    if not s.prices:
        warnings.append("PRICES est vide : le coût IA et le plafond de dépense resteront à 0.")
    return errors, warnings


def run(s: Settings) -> None:
    if not s.is_production:
        return
    errors, warnings = problems(s)
    for w in warnings:
        log.warning("Configuration : %s", w)
    if errors:
        raise RuntimeError("Configuration de production refusée :\n- " + "\n- ".join(errors))
