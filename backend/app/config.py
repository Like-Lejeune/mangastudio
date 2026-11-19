"""Configuration lue dans l'environnement (.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # utf-8 explicite : sous Windows, le .env serait sinon lu en cp1252 et les accents le casseraient.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./dev.db"
    secret_key: str = "dev-secret-a-changer-en-production-0123456789"
    public_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    storage_dir: str = "./storage"
    redis_url: str | None = None

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
