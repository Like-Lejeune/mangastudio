"""Plans d'abonnement : limites créatives et crédits. Prix = hypothèses à valider."""
from dataclasses import dataclass

MIN_PAGES = 4


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    credits: int            # par mois (plan gratuit : une seule fois, à l'inscription)
    max_characters: int     # par épisode
    max_pages: int          # par épisode
    color: bool
    redraw: bool
    price_usd_cents: int
    price_xaf: int


PLANS: dict[str, Plan] = {
    "free": Plan("free", "Découverte", 12, 3, 5, False, False, 0, 0),
    "creator": Plan("creator", "Créateur", 100, 6, 12, True, True, 999, 6000),
    "studio": Plan("studio", "Studio", 300, 10, 24, True, True, 2999, 18000),
}

@dataclass(frozen=True)
class Pack:
    id: str
    credits: int
    price_xaf: int
    price_usd_cents: int


# Packs de crédits à l'unité (n'expirent pas). Du plus petit au plus grand ; les petits packs
# coûtent un peu plus cher au crédit pour que les gros et les abonnements restent avantageux.
PACKS: dict[str, Pack] = {
    "pack15": Pack("pack15", 15, 1500, 249),
    "pack25": Pack("pack25", 25, 2000, 349),
    "pack": Pack("pack", 50, 3500, 599),      # identifiant historique : le pack de 50
}
# Compatibilité avec l'ancien code et les anciens paiements.
PACK_CREDITS = PACKS["pack"].credits
PACK_PRICE_USD_CENTS = PACKS["pack"].price_usd_cents
PACK_PRICE_XAF = PACKS["pack"].price_xaf

PERIOD_DAYS = 30


def get_plan(plan_id: str | None) -> Plan:
    return PLANS.get(plan_id or "free", PLANS["free"])


# ---------- Crédits gratuits ----------
REFERRAL_INVITEE = 5        # l'invité, à la confirmation de son adresse
REFERRAL_REFERRER = 10      # le parrain, quand l'invité termine son 1er épisode
REFERRAL_PURCHASE = 25      # le parrain, au 1er achat de son filleul
REFERRAL_MAX = 20           # parrainages récompensés au plus par compte
WEEKLY_REFILL = 5           # chaque semaine, un compte gratuit actif remonte à ce solde (sans cumul)
MISSIONS = {                # mission -> (crédits, libellé)
    "first_episode": (3, "Terminer votre premier épisode"),
    "first_share": (2, "Partager un chapitre par lien"),
    "testimonial": (2, "Donner un avis publié sur l'accueil"),
}
