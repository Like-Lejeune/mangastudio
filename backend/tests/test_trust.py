"""Paiement mobile money via TrustChange : parcours nominal et cas tordus."""
import pytest

from tests.trust_fake import FakeTrust


@pytest.fixture
async def account(client):
    r = await client.post("/auth/register", json={"email": "trust@test.cm", "display_name": "Trust", "password": "motdepasse"})
    if r.status_code == 409:
        r = await client.post("/auth/login", json={"email": "trust@test.cm", "password": "motdepasse"})
    return {"Authorization": f"Bearer {r.json()['token']}"}


async def credits(client, h):
    return (await client.get("/me", headers=h)).json()["credits"]


async def pay(client, h, product="pack"):
    r = await client.post("/billing/checkout", headers=h, json={"product": product, "phone": "+237 699 000 000", "operator": "MTN_CM"})
    assert r.status_code == 202, r.text
    return r.json()["reference"]


async def test_webhook_credits_once(client, account, monkeypatch):
    fake, before = FakeTrust(monkeypatch), await credits(client, account)
    ref = await pay(client, account)
    assert fake.transactions[ref]["phoneNumber"] == "699000000"       # numéro national, sans indicatif
    assert fake.transactions[ref]["amount"] == 3500
    assert (await client.get(f"/billing/payments/{ref}", headers=account)).json()["status"] == "pending"

    fake.finish(ref)
    body, headers = fake.webhook(ref)
    assert (await client.post("/billing/webhooks/trust", content=body, headers=headers)).json()["applied"] is True
    assert (await client.post("/billing/webhooks/trust", content=body, headers=headers)).json()["applied"] is False   # rejeu
    assert await credits(client, account) == before + 50
    assert (await client.get(f"/billing/payments/{ref}", headers=account)).json()["status"] == "paid"


async def test_webhook_refused(client, account, monkeypatch):
    fake = FakeTrust(monkeypatch)
    ref = await pay(client, account)
    fake.finish(ref)
    before = await credits(client, account)
    for body, headers in (fake.webhook(ref, secret="autre"), fake.webhook(ref, age=900)):       # mauvaise signature, trop vieux
        assert (await client.post("/billing/webhooks/trust", content=body, headers=headers)).status_code == 400
    body, headers = fake.webhook(ref)
    assert (await client.post("/billing/webhooks/trust", content=body + b" ", headers=headers)).status_code == 400   # corps modifié
    assert (await client.post("/billing/webhooks/trust", content=body)).status_code == 400                          # sans en-têtes
    assert await credits(client, account) == before


async def test_forged_success_body_is_not_trusted(client, account, monkeypatch):
    """Un corps signé qui annonce un succès ne suffit pas : c'est l'état lu chez TrustChange qui compte."""
    fake = FakeTrust(monkeypatch)
    ref = await pay(client, account)
    before = await credits(client, account)
    body, headers = fake.webhook(ref)            # la transaction est encore PROCESSING côté TrustChange
    assert (await client.post("/billing/webhooks/trust", content=body, headers=headers)).json()["applied"] is False
    assert await credits(client, account) == before


async def test_lost_webhook_recovered_by_polling(client, account, monkeypatch):
    fake, before = FakeTrust(monkeypatch), await credits(client, account)
    ref = await pay(client, account, "creator")
    fake.finish(ref)                             # aucune notification reçue
    assert (await client.get(f"/billing/payments/{ref}", headers=account)).json()["status"] == "paid"
    me = (await client.get("/me", headers=account)).json()
    assert me["plan"]["id"] == "creator" and me["credits"] == before + 100
    assert (await client.get(f"/billing/payments/{ref}", headers=account)).json()["status"] == "paid"
    assert await credits(client, account) == before + 100            # interroger deux fois ne crédite pas deux fois


async def test_failed_and_underpaid(client, account, monkeypatch):
    fake, before = FakeTrust(monkeypatch), await credits(client, account)
    ref = await pay(client, account)
    fake.finish(ref, "FAILED")
    assert (await client.get(f"/billing/payments/{ref}", headers=account)).json()["status"] == "failed"
    ref = await pay(client, account)
    fake.finish(ref, "SUCCESS", amount=100)      # montant inférieur au prix
    assert (await client.get(f"/billing/payments/{ref}", headers=account)).json()["status"] == "failed"
    assert await credits(client, account) == before


async def test_network_cut_during_collect(client, account, monkeypatch):
    fake = FakeTrust(monkeypatch)
    fake.unreachable = True
    ref = await pay(client, account)             # l'intention existe, l'issue est inconnue
    fake.unreachable = False
    r = (await client.get(f"/billing/payments/{ref}", headers=account)).json()
    assert r["status"] == "failed" and "Réessayez" in r["error"]     # TrustChange ne connaît pas la référence


async def test_payment_is_private(client, account, monkeypatch):
    FakeTrust(monkeypatch)
    ref = await pay(client, account)
    other = await client.post("/auth/register", json={"email": "autre@test.cm", "display_name": "Autre", "password": "motdepasse"})
    h = {"Authorization": f"Bearer {other.json()['token']}"}
    assert (await client.get(f"/billing/payments/{ref}", headers=h)).status_code == 404
    assert (await client.post("/billing/checkout", headers=account, json={"product": "pack"})).status_code == 422


async def test_don_montant_libre_sans_credit(client, account, monkeypatch):
    fake, before = FakeTrust(monkeypatch), await credits(client, account)
    base = {"product": "don", "phone": "+237 699 000 000", "operator": "MTN_CM"}
    assert (await client.post("/billing/checkout", headers=account, json=base)).status_code == 422                      # montant manquant
    assert (await client.post("/billing/checkout", headers=account, json={**base, "amount": 100})).status_code == 422   # sous 500 FCFA
    r = await client.post("/billing/checkout", headers=account, json={**base, "amount": 2500})
    assert r.status_code == 202
    ref = r.json()["reference"]
    assert fake.transactions[ref]["amount"] == 2500
    fake.finish(ref)
    body, headers = fake.webhook(ref)
    assert (await client.post("/billing/webhooks/trust", content=body, headers=headers)).json()["applied"] is True
    assert await credits(client, account) == before          # un don ne donne pas de crédits
    assert (await client.get(f"/billing/payments/{ref}", headers=account)).json()["status"] == "paid"
