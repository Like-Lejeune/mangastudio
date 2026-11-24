"""Parrainage, missions et recharge hebdomadaire."""
import pytest
from sqlalchemy import update

from app import ratelimit
from app.db import SessionLocal
from app.models import CreditLedger, User
from tests.test_flow import wait_done
from tests.trust_fake import FakeTrust

IP = {"valeur": "41.202.1.1"}


@pytest.fixture(autouse=True)
def adresse_ip(monkeypatch):
    """Chaque inscription prend l'adresse IP choisie par le test (sinon toutes viendraient de la même)."""
    monkeypatch.setattr(ratelimit, "client_ip", lambda request: IP["valeur"])


async def inscrire(client, email, ref=None, ip="41.202.1.1"):
    IP["valeur"] = ip
    body = {"email": email, "display_name": email.split("@")[0].title(), "password": "motdepasse", **({"ref": ref} if ref else {})}
    r = await client.post("/auth/register", json=body)
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


async def solde(client, h):
    return (await client.get("/me", headers=h)).json()["credits"]


async def premier_episode(client, h):
    sid = (await client.post("/series", headers=h, json={"premise": "Une coursière de Yaoundé arrête le temps."})).json()["id"]
    cid = (await client.post(f"/series/{sid}/characters", headers=h, json={"name": "Nadia"})).json()["id"]
    eid = (await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 4, "character_ids": [cid]})).json()["id"]
    assert (await wait_done(client, h, eid))["status"] == "done"
    return eid


async def test_parcours_parrainage(client, monkeypatch):
    awa = await inscrire(client, "awa.parrain@test.cm", ip="41.202.1.1")
    g = (await client.get("/me/gagner", headers=awa)).json()
    code = g["code"]
    assert len(code) == 7 and g["link"].endswith(f"/inscription?ref={code}")
    depart_awa = await solde(client, awa)

    # Le filleul (autre adresse IP) reçoit +5 en plus de ses crédits de bienvenue.
    kofi = await inscrire(client, "kofi.filleul@test.cm", ref=code.lower(), ip="102.244.7.8")
    base = await solde(client, kofi)
    assert base == 12 + 5
    assert await solde(client, awa) == depart_awa                      # rien tant que le filleul n'a pas créé

    # Premier épisode du filleul : parrain +10, filleul +3 (mission), une seule fois.
    await premier_episode(client, kofi)
    assert await solde(client, awa) == depart_awa + 10
    g = (await client.get("/me/gagner", headers=awa)).json()
    assert g["referrals"][0]["name"] == "Kofi.Filleul" and g["referrals"][0]["status"] == "qualified" and g["earned"] == 10
    assert "kofi.filleul@test.cm" not in str(g)                        # jamais l'adresse du filleul
    await premier_episode(client, kofi)
    assert await solde(client, awa) == depart_awa + 10

    # Premier achat du filleul : parrain +25, une seule fois.
    fake = FakeTrust(monkeypatch)
    for _ in range(2):
        ref = (await client.post("/billing/checkout", headers=kofi, json={"product": "pack15", "phone": "699000000", "operator": "MTN_CM"})).json()["reference"]
        fake.finish(ref)
        body, headers = fake.webhook(ref)
        await client.post("/billing/webhooks/trust", content=body, headers=headers)
    assert await solde(client, awa) == depart_awa + 10 + 25


async def test_code_inconnu_ou_le_sien(client):
    h = await inscrire(client, "seul@test.cm", ref="ZZZZZZZ", ip="10.0.0.9")
    assert await solde(client, h) == 12                                 # code inconnu : inscription normale, sans bonus


async def test_meme_ip_mis_de_cote_puis_valide(client):
    paul = await inscrire(client, "paul.p@test.cm", ip="154.72.1.1")
    code = (await client.get("/me/gagner", headers=paul)).json()["code"]
    depart = await solde(client, paul)
    faux = await inscrire(client, "faux.compte@test.cm", ref=code, ip="154.72.1.1")      # même IP que le parrain
    assert await solde(client, faux) == 12                              # pas de bonus tant que ce n'est pas vérifié
    await premier_episode(client, faux)
    assert await solde(client, paul) == depart                          # parrain non récompensé
    assert (await client.get("/me/gagner", headers=paul)).json()["referrals"][0]["status"] == "checking"

    adm = await inscrire(client, "chef.parrainage@test.cm", ip="1.1.1.1")
    async with SessionLocal() as s:
        await s.execute(update(User).where(User.email == "chef.parrainage@test.cm").values(is_admin=True))
        await s.commit()
    liste = (await client.get("/admin/referrals?status=flagged", headers=adm)).json()
    item = next(i for i in liste["items"] if i["referee_email"] == "faux.compte@test.cm")
    assert "même adresse IP" in item["flag_reason"] and liste["flagged"] >= 1
    avant = await solde(client, faux)
    assert (await client.post(f"/admin/referrals/{item['id']}/approve", headers=adm)).status_code == 200
    # Validé : le bonus du filleul et celui du parrain (épisode déjà terminé) sont versés.
    assert await solde(client, faux) == avant + 5
    assert await solde(client, paul) == depart + 10


async def test_plafond_de_20(client, monkeypatch):
    monkeypatch.setattr("app.growth.REFERRAL_MAX", 1)
    p = await inscrire(client, "plafond@test.cm", ip="2.2.2.2")
    code = (await client.get("/me/gagner", headers=p)).json()["code"]
    depart = await solde(client, p)
    for i in range(2):
        f = await inscrire(client, f"filleul{i}.plafond@test.cm", ref=code, ip=f"3.3.3.{i}")
        await premier_episode(client, f)
    assert await solde(client, p) == depart + 10                        # le 2e dépasse le plafond


async def test_missions_partage_et_avis(client):
    h = await inscrire(client, "missions@test.cm", ip="5.5.5.5")
    eid = await premier_episode(client, h)
    apres_episode = await solde(client, h)
    await client.post(f"/episodes/{eid}/share", json={"enabled": True}, headers=h)
    await client.post(f"/episodes/{eid}/share", json={"enabled": False}, headers=h)
    await client.post(f"/episodes/{eid}/share", json={"enabled": True}, headers=h)
    assert await solde(client, h) == apres_episode + 2                  # le partage ne paie qu'une fois
    missions = {m["id"]: m["done"] for m in (await client.get("/me/gagner", headers=h)).json()["missions"]}
    assert missions == {"first_episode": True, "first_share": True, "testimonial": False}


async def test_recharge_hebdomadaire(client):
    h = await inscrire(client, "recharge@test.cm", ip="6.6.6.6")
    me = (await client.get("/me", headers=h)).json()
    async with SessionLocal() as s:     # solde ramené à 1 crédit, et dernière recharge il y a longtemps
        s.add(CreditLedger(user_id=me["id"], delta=-(me["credits"] - 1), bucket="pack", kind="expire", note="test"))
        await s.execute(update(User).where(User.id == me["id"]).values(last_refill_week="2020-W01"))
        await s.commit()
    me = (await client.get("/me", headers=h)).json()
    assert me["credits"] == 5 and me["weekly_refill"] == 4
    me = (await client.get("/me", headers=h)).json()
    assert me["credits"] == 5 and me["weekly_refill"] == 0             # une fois par semaine
    async with SessionLocal() as s:     # au-dessus de 5 : rien n'est ajouté (pas de cumul)
        s.add(CreditLedger(user_id=me["id"], delta=10, bucket="pack", kind="grant", note="test"))
        await s.execute(update(User).where(User.id == me["id"]).values(last_refill_week="2020-W01"))
        await s.commit()
    assert (await client.get("/me", headers=h)).json()["credits"] == 15
