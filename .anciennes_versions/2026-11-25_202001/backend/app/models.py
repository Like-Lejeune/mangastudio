"""Tables de la V1. Identifiants texte générés par l'application."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def new_id() -> str:
    return uuid.uuid4().hex


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(60))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    # Un compte suspendu ne peut plus se connecter ni appeler l'API ; ses données sont gardées.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # Adresse vérifiée par code. Les comptes créés avant la vérification sont considérés comme vérifiés.
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=true())
    verify_code_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verify_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verify_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    # Mot de passe oublié : code à 6 chiffres envoyé par e-mail.
    reset_code_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reset_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reset_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    # Augmenté à chaque changement de mot de passe : les sessions ouvertes avant sont fermées.
    session_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    # Parrainage et crédits gratuits
    referral_code: Mapped[str | None] = mapped_column(String(12), unique=True, nullable=True)
    referred_by_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    signup_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    last_refill_week: Mapped[str | None] = mapped_column(String(8), nullable=True)   # ex. 2026-W48
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Subscription(Base):
    """Un abonnement par utilisateur ; absent ou expiré = plan gratuit."""
    __tablename__ = "subscriptions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    plan: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | canceled | past_due
    provider: Mapped[str] = mapped_column(String(20))                  # trust | stripe
    external_id: Mapped[str | None] = mapped_column(String(255))       # id d'abonnement Stripe
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CreditLedger(Base):
    """Mouvements de crédits. Le solde est la somme de `delta` ; on n'écrit jamais un solde."""
    __tablename__ = "credit_ledger"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    delta: Mapped[int] = mapped_column(Integer)
    bucket: Mapped[str] = mapped_column(String(10))   # monthly (expire au renouvellement) | pack
    kind: Mapped[str] = mapped_column(String(10))     # grant | reserve | refund | expire
    episode_id: Mapped[str | None] = mapped_column(String(32), index=True)
    note: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(20))
    # Unique : un webhook rejoué ne crédite pas deux fois.
    external_ref: Mapped[str] = mapped_column(String(255), unique=True)
    product: Mapped[str] = mapped_column(String(20))  # creator | studio | pack
    amount: Mapped[int] = mapped_column(Integer)      # plus petite unité de la devise
    currency: Mapped[str] = mapped_column(String(3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class PaymentIntent(Base):
    """Une demande de paiement en cours. Créée avant l'appel au prestataire, close par
    le webhook ou par une relecture de la transaction (billing/trust.py)."""
    __tablename__ = "payment_intents"
    reference: Mapped[str] = mapped_column(String(40), primary_key=True)   # notre externalReference
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product: Mapped[str] = mapped_column(String(20))      # creator | studio | pack
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    provider: Mapped[str] = mapped_column(String(20))     # trust
    operator: Mapped[str] = mapped_column(String(40), default="")
    provider_ref: Mapped[str | None] = mapped_column(String(80))   # transactionId TrustChange
    status: Mapped[str] = mapped_column(String(10), default="pending")   # pending | paid | failed
    error: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Series(Base):
    __tablename__ = "series"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120), default="")
    premise: Mapped[str] = mapped_column(Text)
    style: Mapped[str] = mapped_column(String(20), default="shonen")
    palette: Mapped[str] = mapped_column(String(10), default="bw")   # bw | color
    language: Mapped[str] = mapped_column(String(5), default="fr")   # langue des dialogues
    setting: Mapped[str] = mapped_column(Text, default="")
    cover_path: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    characters: Mapped[list["Character"]] = relationship(back_populates="series", order_by="Character.created_at")
    episodes: Mapped[list["Episode"]] = relationship(back_populates="series", order_by="Episode.number")


class Character(Base):
    """Bibliothèque de personnages de la série. `look` est figé après le design."""
    __tablename__ = "characters"
    __table_args__ = (UniqueConstraint("series_id", "slug"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    series_id: Mapped[str] = mapped_column(ForeignKey("series.id", ondelete="CASCADE"), index=True)
    slug: Mapped[str] = mapped_column(String(40))   # identifiant utilisé dans le scénario
    name: Mapped[str] = mapped_column(String(60))
    role: Mapped[str] = mapped_column(String(120), default="")
    description: Mapped[str] = mapped_column(Text, default="")   # mots de l'utilisateur
    look: Mapped[str] = mapped_column(Text, default="")          # design fixe, dessinable
    photo_path: Mapped[str | None] = mapped_column(String(255))
    sheet_path: Mapped[str | None] = mapped_column(String(255))  # fiche modèle
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    series: Mapped[Series] = relationship(back_populates="characters")


class Episode(Base):
    __tablename__ = "episodes"
    __table_args__ = (UniqueConstraint("series_id", "number"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    series_id: Mapped[str] = mapped_column(ForeignKey("series.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    direction: Mapped[str] = mapped_column(Text, default="")   # « ce qui se passe ensuite »
    page_count: Mapped[int] = mapped_column(Integer)
    # queued | designing | writing | moderating | drawing | done | failed | blocked
    status: Mapped[str] = mapped_column(String(20), default="queued")
    error: Mapped[str] = mapped_column(Text, default="")
    title: Mapped[str] = mapped_column(String(120), default="")
    summary: Mapped[str] = mapped_column(Text, default="")     # mémoire pour l'épisode suivant
    script: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    # Lien de lecture public : vide = chapitre privé. Couper le lien le remet à vide.
    share_token: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)

    series: Mapped[Series] = relationship(back_populates="episodes")
    pages: Mapped[list["Page"]] = relationship(back_populates="episode", order_by="Page.number")
    cast: Mapped[list["EpisodeCharacter"]] = relationship(back_populates="episode")


class EpisodeCharacter(Base):
    __tablename__ = "episode_characters"
    episode_id: Mapped[str] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), primary_key=True)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True)

    episode: Mapped[Episode] = relationship(back_populates="cast")
    character: Mapped[Character] = relationship()


class Page(Base):
    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("episode_id", "number"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    episode_id: Mapped[str] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), default="pending")  # pending | done | failed
    image_path: Mapped[str | None] = mapped_column(String(255))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    editor_note: Mapped[str] = mapped_column(Text, default="")

    episode: Mapped[Episode] = relationship(back_populates="pages")


class UsageEvent(Base):
    """Un appel à un modèle. Source du compteur de tokens par épisode."""
    __tablename__ = "usage_events"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    episode_id: Mapped[str | None] = mapped_column(String(32), index=True)
    stage: Mapped[str] = mapped_column(String(20))   # design | script | moderation | sheet | page | check | cover
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(60))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    images: Mapped[int] = mapped_column(Integer, default=0)
    cost_micro_usd: Mapped[int] = mapped_column(Integer, default=0)   # interne (marge), jamais montré à l'utilisateur
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BlockedTerm(Base):
    __tablename__ = "blocked_terms"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    term: Mapped[str] = mapped_column(String(120), unique=True)   # stocké normalisé
    action: Mapped[str] = mapped_column(String(10), default="block")  # block | flag
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SceneRule(Base):
    """Une scène interdite, décrite en langage clair pour le classeur."""
    __tablename__ = "scene_rules"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    label: Mapped[str] = mapped_column(String(60), unique=True)
    description: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ModerationEvent(Base):
    __tablename__ = "moderation_events"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    episode_id: Mapped[str | None] = mapped_column(String(32))
    checkpoint: Mapped[str] = mapped_column(String(10))   # input | script | image
    action: Mapped[str] = mapped_column(String(10))       # block | flag
    rule: Mapped[str] = mapped_column(String(120))
    excerpt: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AdminAction(Base):
    """Journal des actions d'administration : qui a fait quoi, sur quoi, quand. Jamais modifié ni effacé."""
    __tablename__ = "admin_actions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    admin_id: Mapped[str] = mapped_column(String(32), index=True)
    admin_email: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(40))        # credits | plan | suspend | reactivate | role | term | scene_rule
    target_type: Mapped[str] = mapped_column(String(20))   # user | term | scene_rule
    target_id: Mapped[str] = mapped_column(String(64), index=True)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)


class Testimonial(Base):
    """Avis laissé par un utilisateur. Publié sur l'accueil seulement après son accord et la validation d'un administrateur."""
    __tablename__ = "testimonials"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)   # un avis par compte, modifiable
    episode_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    rating: Mapped[int] = mapped_column(Integer)
    display_name: Mapped[str] = mapped_column(String(60))     # comment la personne accepte d'être citée
    role: Mapped[str] = mapped_column(String(80), default="")
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(10), default="pending", index=True)   # pending | approved | rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PdfDownload(Base):
    """Un téléchargement PDF : sert au quota mensuel des comptes gratuits."""
    __tablename__ = "pdf_downloads"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    episode_id: Mapped[str] = mapped_column(String(32))
    watermark: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)


class Referral(Base):
    """Un filleul. Les récompenses sont datées une à une : chacune n'est versée qu'une fois."""
    __tablename__ = "referrals"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    referrer_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    referee_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    # pending : en attente du 1er épisode · qualified : parrain récompensé · flagged : à vérifier · cancelled
    status: Mapped[str] = mapped_column(String(10), default="pending", index=True)
    flag_reason: Mapped[str] = mapped_column(String(120), default="")
    invitee_rewarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    referrer_rewarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    purchase_rewarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class UserMission(Base):
    """Mission accomplie (et payée) une seule fois par compte."""
    __tablename__ = "user_missions"
    __table_args__ = (UniqueConstraint("user_id", "mission"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    mission: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Publication(Base):
    """Un chapitre proposé à la galerie publique. Visible seulement une fois publié par l'administration."""
    __tablename__ = "publications"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    episode_id: Mapped[str] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # pending | published | rejected | withdrawn (retiré par l'auteur ou l'administration)
    status: Mapped[str] = mapped_column(String(10), default="pending", index=True)
    reason: Mapped[str] = mapped_column(String(300), default="")      # motif d'un refus ou d'un retrait
    featured: Mapped[bool] = mapped_column(Boolean, default=False)     # coup de cœur de l'équipe
    likes: Mapped[int] = mapped_column(Integer, default=0)            # compteur (la table Like fait foi)
    terms_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "publication_id"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    publication_id: Mapped[str] = mapped_column(ForeignKey("publications.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
