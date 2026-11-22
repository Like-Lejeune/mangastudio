"""Configuration lue dans l'environnement (.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # utf-8 explicite : sous Windows, le .env serait sinon lu en cp1252 et les accents le casseraient.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # "production" active les contrôles de démarrage et ferme l'API aux origines locales.
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    secret_key: str = "dev-secret-a-changer-en-production-0123456789"
    public_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    storage_dir: str = "./storage"
    redis_url: str | None = None
    # Comptes administrateurs : adresses séparées par des virgules. Ils le deviennent à l'inscription
    # ou à la connexion suivante. Aucun autre moyen de devenir administrateur que celui-ci ou l'admin.
    admin_emails: str = ""

    # Vérification de l'adresse e-mail : code à 6 chiffres envoyé à l'inscription. Pas de crédit ni de
    # génération avant vérification. À ne désactiver que pour les tests automatiques.
    email_verification: bool = True
    # Envoi des e-mails (SMTP). Hostinger : smtp.hostinger.com, port 465 (SSL).
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""                 # ex. MangaStudio <noreply@psikalab.space> ; vide = SMTP_USER
    smtp_starttls: bool = False         # True pour le port 587 (STARTTLS), False pour 465 (SSL direct)
    # Domaines d'adresses jetables refusés en plus de la liste intégrée (séparés par des virgules).
    blocked_email_domains: str = ""

    # Limites de tentatives (par adresse IP du visiteur)
    login_max_failures: int = 5          # échecs pour un même compte, puis attente
    login_max_failures_ip: int = 30      # échecs tous comptes confondus
    login_window_minutes: int = 15
    register_max_per_hour: int = 10
    # Photo d'un personnage, une fois décodée
    max_photo_bytes: int = 3_000_000

    # Plafond de dépense IA par jour (dollars, coût calculé avec PRICES). 0 = pas de plafond.
    # Au-delà, les nouveaux épisodes et redessins sont refusés jusqu'au lendemain ; ceux en cours se terminent.
    ai_daily_budget_usd: float = 0
    ai_alert_ratio: float = 0.8          # première alerte à 80 % du plafond
    budget_timezone: str = "Africa/Douala"
    # Adresse qui reçoit les alertes en JSON {"text", "content"} : webhook Slack, Discord, Google Chat…
    alert_webhook_url: str = ""

    # Un fournisseur et un modèle par rôle : on change de modèle sans toucher au code.
    writer_provider: str = "fake"
    writer_model: str = "fake-writer"
    checker_provider: str = "fake"
    checker_model: str = "fake-checker"
    image_provider: str = "fake"
    image_model: str = "fake-image"
    # Nombre maximal d'images de référence acceptées par le dessinateur.
    image_max_refs: int = 8
    meta_api_base: str = "https://api.meta.ai/v1"
    meta_api_key: str = ""
    openai_compat_base_url: str = ""
    openai_compat_api_key: str = ""
    # {"modele": {"in": $/Mtok, "out": $/Mtok, "image": $/image}}
    prices: dict[str, dict[str, float]] = {}

    # Pipeline
    single_pass_max_pages: int = 8   # au-delà : plan puis lots
    script_batch_size: int = 4
    page_concurrency: int = 4

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_creator: str = ""
    stripe_price_studio: str = ""
    stripe_price_pack: str = ""

    # TrustChange (mobile money). Clé `tc_test_…` = compte fictif, opérations simulées.
    trustchange_base_url: str = "https://api.trustchange.fr"
    trustchange_api_key: str = ""
    trustchange_webhook_secret: str = ""
    # À confirmer avec la documentation TrustChange : noms des en-têtes du webhook et libellés des statuts finaux.
    trustchange_signature_header: str = "X-TrustChange-Signature"
    trustchange_timestamp_header: str = "X-TrustChange-Timestamp"
    trustchange_success_statuses: list[str] = ["SUCCESS", "SUCCESSFUL", "COMPLETED"]
    trustchange_failure_statuses: list[str] = ["FAILED", "CANCELLED", "CANCELED", "EXPIRED", "REJECTED"]


    @property
    def admin_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.admin_emails.split(",") if e.strip()}

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")


@lru_cache
def get_settings() -> Settings:
    return Settings()
