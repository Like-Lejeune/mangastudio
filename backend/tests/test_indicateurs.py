"""Indicateurs pour investisseurs : lecture seule, chiffres justes, réservés à l'administration."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Payment, Subscription, User
from tests.test_admin import account, admin  # noqa: F401  (fixture)
from tests.test_partage import episode_termine


async def _compte_lignes() -> dict:
    from app.models import CreditLedger, Episode, Like, UsageEvent
    async with SessionLocal() as s:
        return {m.__name__: (await s.execute(select(func.count()).select_from(m))).scalar_one()
                for m in (User, Episode, Like, Payment, Subscription, CreditLedger, UsageEvent)}


async def test_indicateurs(client, admin):  # noqa: F811
    avant = (await client.get("/admin/metrics", headers=admin)).json()
    await episode_termine(client, "metrique.a@test.cm")
    hb = await account(client, "metrique.b@test.cm")
    async with SessionLocal() as s:
        uid = (await s.execute(select(User.id).where(User.email == "metrique.a@test.cm"))).scalar_one()
        s.add(Payment(user_id=uid, provider="trust", external_ref="metrique-1", product="creator", amount=6000, currency="XAF"))
        s.add(Payment(user_id=uid, provider="trust", external_ref="metrique-don", product="don", amount=1000, currency="XAF"))
        existing = await s.get(Subscription, uid)
        if existing is None:
            s.add(Subscription(user_id=uid, plan="creator", status="active", provider="trust",
                               period_end=datetime.now(timezone.utc) + timedelta(days=30)))
        await s.commit()

    lignes = await _compte_lignes()
    m = (await client.get("/admin/metrics", headers=admin)).json()
    assert await _compte_lignes() == lignes                        # rien n'est écrit
    c, p = m["last_30d"], avant["last_30d"]
    assert c["signups"] == p["signups"] + 2
    assert c["episodes_done"] == p["episodes_done"] + 1
    assert c["revenue_xaf"] == p["revenue_xaf"] + 6000             # le don n'est pas du chiffre d'affaires
    assert c["payers"] >= 1 and c["ai_cost_usd"] > 0 and c["ai_cost_per_episode_usd"] > 0
    assert m["mrr"]["xaf"] >= 6000 and m["mrr"]["subscribers"]["creator"] >= 1
    assert m["mau"] >= 1 and m["wau"] >= 1
    etapes = [f["step"] for f in m["funnel"]]
    assert etapes[0] == "Inscrits" and etapes[-1] == "Ont payé"
    assert m["funnel"][0]["users"] >= m["funnel"][-1]["users"]
    assert len(m["cohorts"]) == 8 and m["cohorts"][-1]["size"] >= 2 and m["cohorts"][-1]["retention"][0] is not None
    assert len(m["monthly"]) == 6 and m["monthly"][-1]["signups"] >= 2
    # L'équipe n'est pas comptée parmi les utilisateurs.
    assert all(f["users"] <= m["totals"]["users"] for f in m["funnel"])

    csv = (await client.get("/admin/metrics.csv", headers=admin))
    assert csv.status_code == 200 and "Chiffre d'affaires (FCFA)" in csv.text and csv.text.count("\n") == 7
    # Réservé à l'administration.
    assert (await client.get("/admin/metrics", headers=hb)).status_code == 403
    assert (await client.get("/admin/metrics.csv")).status_code == 401


async def test_mois_offerts_hors_revenu_recurrent(client, admin):  # noqa: F811
    await account(client, "metrique.offert@test.cm")
    avant = (await client.get("/admin/metrics", headers=admin)).json()["mrr"]
    async with SessionLocal() as s:
        uid = (await s.execute(select(User.id).where(User.email == "metrique.offert@test.cm"))).scalar_one()
        s.add(Subscription(user_id=uid, plan="studio", status="active", provider="admin",
                           period_end=datetime.now(timezone.utc) + timedelta(days=30)))
        await s.commit()
    apres = (await client.get("/admin/metrics", headers=admin)).json()["mrr"]
    assert apres["xaf"] == avant["xaf"] and apres["gifted"] == avant["gifted"] + 1
