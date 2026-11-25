"""Indicateurs pour investisseurs et acheteurs : croissance, rétention, conversion, revenus, marge.

Lecture seule : rien n'est écrit en base. Tout est calculé à partir des tables existantes
(comptes, épisodes, « j'aime », paiements, abonnements, appels IA, parrainages).

Une personne est « active » une semaine donnée si elle a lancé un épisode, aimé une histoire
ou payé quelque chose cette semaine-là.
"""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Episode,
    Like,
    Payment,
    Publication,
    Referral,
    Series,
    Subscription,
    UsageEvent,
    User,
    now,
)
from app.plans import PLANS
from app.services import aware

# Taux indicatif pour comparer le chiffre d'affaires en FCFA au coût IA payé en dollars.
# Le FCFA est arrimé à l'euro ; le dollar varie. À ajuster si besoin.
XAF_PER_USD = 600
COHORT_WEEKS = 8


def _monday(d: datetime | date) -> date:
    d = d.date() if isinstance(d, datetime) else d
    return d - timedelta(days=d.weekday())


def _pct(a: float, b: float) -> float | None:
    return round(100 * a / b, 1) if b else None


async def compute(session: AsyncSession, cohort_count: int = 8) -> dict:
    t = now()
    d30, d60 = t - timedelta(days=30), t - timedelta(days=60)

    users = [(uid, aware(c), v, ref, adm) for uid, c, v, ref, adm in (await session.execute(
        select(User.id, User.created_at, User.email_verified, User.referred_by_id, User.is_admin))).all()]
    staff = {u for u, *_, adm in users if adm}
    users = [u for u in users if u[0] not in staff]           # l'équipe ne compte pas
    created = {u: c for u, c, *_ in users}

    # Activité datée par personne
    episodes = [(o, aware(c), s) for o, c, s in (await session.execute(
        select(Series.owner_id, Episode.created_at, Episode.status).join(Series, Series.id == Episode.series_id))).all() if o in created]
    likes = [(u, aware(c)) for u, c in (await session.execute(select(Like.user_id, Like.created_at))).all() if u in created]
    payments = [(u, aware(c), a, cur, p) for u, c, a, cur, p in (await session.execute(
        select(Payment.user_id, Payment.created_at, Payment.amount, Payment.currency, Payment.product))).all() if u in created]
    sales = [p for p in payments if p[4] != "don"]
    activity: dict[str, list[datetime]] = defaultdict(list)
    for u, c, _ in episodes:
        activity[u].append(c)
    for u, c in likes:
        activity[u].append(c)
    for u, c, *_ in payments:
        activity[u].append(c)

    def active_between(a: datetime, b: datetime) -> set[str]:
        return {u for u, ds in activity.items() if any(a <= d < b for d in ds)}

    # ---- Chiffres clés : 30 derniers jours, comparés aux 30 précédents
    def window(a: datetime, b: datetime) -> dict:
        ep_done = sum(1 for _, c, s in episodes if a <= c < b and s == "done")
        rev_xaf = sum(a_ for _, c, a_, cur, _p in sales if a <= c < b and cur.upper() == "XAF")
        rev_usd = sum(a_ for _, c, a_, cur, _p in sales if a <= c < b and cur.upper() == "USD") / 100
        return {
            "signups": sum(1 for _, c, *_ in users if a <= c < b),
            "signups_verified": sum(1 for _, c, v, *_ in users if a <= c < b and v),
            "active": len(active_between(a, b)),
            "creators": len({u for u, c, _ in episodes if a <= c < b}),
            "episodes_done": ep_done,
            "revenue_xaf": rev_xaf, "revenue_usd": round(rev_usd, 2),
            "payers": len({u for u, c, *_ in sales if a <= c < b}),
        }

    usage = [(aware(c), cost, e) for c, cost, e in (await session.execute(
        select(UsageEvent.created_at, UsageEvent.cost_micro_usd, UsageEvent.user_id))).all() if e in created]

    def cost_between(a: datetime, b: datetime) -> float:
        return round(sum(c for d, c, _ in usage if a <= d < b) / 1e6, 2)

    cur, prev = window(d30, t), window(d60, d30)
    for w, (a, b) in ((cur, (d30, t)), (prev, (d60, d30))):
        w["ai_cost_usd"] = cost_between(a, b)
        w["ai_cost_per_episode_usd"] = round(w["ai_cost_usd"] / w["episodes_done"], 3) if w["episodes_done"] else None
        revenue_usd_equiv = w["revenue_xaf"] / XAF_PER_USD + w["revenue_usd"]
        w["gross_margin_pct"] = _pct(revenue_usd_equiv - w["ai_cost_usd"], revenue_usd_equiv)
    wau = len(active_between(t - timedelta(days=7), t))
    mau = cur["active"]

    # ---- Revenu récurrent : abonnements payés en cours (les mois offerts sont comptés à part)
    subs = (await session.execute(select(Subscription.user_id, Subscription.plan, Subscription.status,
                                         Subscription.provider, Subscription.period_end))).all()
    running = [(u, p, prov) for u, p, st, prov, end in subs if st == "active" and aware(end) > t and u in created]
    paid_subs = Counter(p for _, p, prov in running if prov != "admin")
    mrr_xaf = sum(PLANS[p].price_xaf * n for p, n in paid_subs.items() if p in PLANS)

    # ---- Entonnoir, depuis le début
    owners = {o for o, *_ in (await session.execute(select(Series.owner_id))).all() if o in created}
    done_owners = {u for u, _, s in episodes if s == "done"}
    publishers = {u for u, in (await session.execute(select(Publication.user_id))).all() if u in created}
    payers = {u for u, *_ in sales}
    funnel = [
        ("Inscrits", len(users)),
        ("Adresse confirmée", sum(1 for _, _, v, *_ in users if v)),
        ("Ont créé une série", len(owners)),
        ("Ont terminé un épisode", len(done_owners)),
        ("Ont publié dans la galerie", len(publishers)),
        ("Ont payé", len(payers)),
    ]

    # ---- Rétention par semaine d'inscription
    this_monday = _monday(t)
    cohorts = []
    for k in range(cohort_count - 1, -1, -1):
        start = this_monday - timedelta(weeks=k)
        members = [u for u, c, *_ in users if _monday(c) == start]
        row = {"week": start.isoformat(), "size": len(members), "retention": []}
        for w in range(min(COHORT_WEEKS, k + 1)):
            a = datetime.combine(start + timedelta(weeks=w), datetime.min.time(), tzinfo=t.tzinfo)
            b = a + timedelta(weeks=1)
            n = sum(1 for u in members if any(a <= d < b for d in activity.get(u, [])))
            row["retention"].append(_pct(n, len(members)))
        cohorts.append(row)

    # ---- Parrainage
    referred_30 = sum(1 for _, c, _, ref, _ in users if c >= d30 and ref)
    refs = (await session.execute(select(Referral.referrer_id, Referral.status, Referral.created_at))).all()
    referrers_30 = {r for r, _, c in refs if aware(c) >= d30}
    referral = {
        "referred_signups_30d": referred_30,
        "share_of_signups_pct": _pct(referred_30, cur["signups"]),
        "active_referrers_30d": len(referrers_30),
        "invites_per_referrer": round(referred_30 / len(referrers_30), 2) if referrers_30 else None,
        # Facteur viral approché : nouveaux inscrits parrainés par personne active sur la période.
        "k_factor": round(referred_30 / mau, 3) if mau else None,
        "qualified_pct": _pct(sum(1 for _, s, _ in refs if s == "qualified"), len(refs)),
    }

    # ---- Tableau mensuel (6 derniers mois)
    months = []
    y, m = t.year, t.month
    for _ in range(6):
        months.append((y, m))
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    monthly = []
    for y, m in reversed(months):
        a = datetime(y, m, 1, tzinfo=t.tzinfo)
        b = datetime(y + (m == 12), 1 if m == 12 else m + 1, 1, tzinfo=t.tzinfo)
        w = window(a, b)
        monthly.append({"month": f"{y}-{m:02d}", **w, "ai_cost_usd": cost_between(a, b)})

    return {
        "generated_at": t.isoformat(), "xaf_per_usd": XAF_PER_USD,
        "last_30d": cur, "previous_30d": prev, "wau": wau, "mau": mau,
        "stickiness_pct": _pct(wau, mau),
        "mrr": {"xaf": mrr_xaf, "subscribers": dict(paid_subs), "gifted": sum(1 for *_, prov in running if prov == "admin")},
        "conversion_pct": _pct(len(payers), sum(1 for _, _, v, *_ in users if v)),
        "funnel": [{"step": s, "users": n, "pct_of_signups": _pct(n, len(users))} for s, n in funnel],
        "cohorts": cohorts, "referral": referral, "monthly": monthly,
        "totals": {"users": len(users), "episodes_done": sum(1 for *_, s in episodes if s == "done"),
                   "likes": len(likes), "publications": len(publishers)},
    }


def monthly_csv(data: dict) -> str:
    cols = [("month", "Mois"), ("signups", "Inscrits"), ("signups_verified", "Inscrits confirmés"), ("active", "Actifs"),
            ("creators", "Créateurs"), ("episodes_done", "Épisodes terminés"), ("payers", "Payeurs"),
            ("revenue_xaf", "Chiffre d'affaires (FCFA)"), ("revenue_usd", "Chiffre d'affaires (USD)"), ("ai_cost_usd", "Coût IA (USD)")]
    lines = [";".join(label for _, label in cols)]
    for row in data["monthly"]:
        lines.append(";".join(str(row.get(k, "")).replace(".", ",") if isinstance(row.get(k), float) else str(row.get(k, "")) for k, _ in cols))
    return "﻿" + "\r\n".join(lines) + "\r\n"     # BOM + ; : s'ouvre proprement dans Excel en français

