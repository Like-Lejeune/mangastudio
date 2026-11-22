"""Vérification de l'adresse : pas de crédit ni de génération avant le code, adresses jetables refusées."""
import pytest

from app import mailer
from app.config import get_settings


@pytest.fixture
def boite(monkeypatch):
    """Active la vérification et capture les codes envoyés au lieu de les poster."""
    monkeypatch.setattr(get_settings(), "email_verification", True)
    recus: dict[str, str] = {}

    async def faux_envoi(to, name, code, minutes):
        recus[to] = code
    monkeypatch.setattr(mailer, "send_code", faux_envoi)
    return recus


async def inscrire(client, email):
    r = await client.post("/auth/register", json={"email": email, "display_name": "Nadia", "password": "motdepasse"})
    return r, {"Authorization": f"Bearer {r.json().get('token', '')}"}


async def test_adresse_jetable_refusee(client, boite):
    for email in ("bot@yopmail.com", "x@mailinator.com", "y@sub.guerrillamail.com"):
        r, _ = await inscrire(client, email)
        assert r.status_code == 422 and r.json()["detail"]["code"] == "disposable_email", email


async def test_rien_avant_verification_puis_credits(client, boite):
    r, h = await inscrire(client, "nadia.verif@test.cm")
    assert r.status_code == 201 and r.json()["email_verified"] is False
    me = (await client.get("/me", headers=h)).json()
    assert me["email_verified"] is False and me["credits"] == 0

    # Tout ce qui coûte est fermé.
    r = await client.post("/series", json={"premise": "Une coursière de Yaoundé arrête le temps."}, headers=h)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "email_unverified"
    assert (await client.post("/billing/checkout", json={"product": "pack", "phone": "699000000", "operator": "MTN_CM"}, headers=h)).status_code == 403

    # Mauvais code : refusé, essais comptés.
    code = boite["nadia.verif@test.cm"]
    faux = "000000" if code != "000000" else "111111"
    r = await client.post("/auth/verify", json={"code": faux}, headers=h)
    assert r.status_code == 422 and "4 essais" in r.json()["detail"]["message"]

    # Bon code : vérifié, crédits de bienvenue, création possible.
    assert (await client.post("/auth/verify", json={"code": code}, headers=h)).json() == {"email_verified": True}
    me = (await client.get("/me", headers=h)).json()
    assert me["email_verified"] is True and me["credits"] > 0
    assert (await client.post("/series", json={"premise": "Une coursière de Yaoundé arrête le temps."}, headers=h)).status_code == 201
    # Vérifier deux fois ne redonne pas de crédits.
    await client.post("/auth/verify", json={"code": code}, headers=h)
    assert (await client.get("/me", headers=h)).json()["credits"] == me["credits"]


async def test_cinq_essais_puis_nouveau_code(client, boite):
    _, h = await inscrire(client, "essais@test.cm")
    premier = boite["essais@test.cm"]
    faux = "000000" if premier != "000000" else "111111"
    for _ in range(5):
        await client.post("/auth/verify", json={"code": faux}, headers=h)
    r = await client.post("/auth/verify", json={"code": premier}, headers=h)
    assert r.status_code == 429                                   # même le bon code ne passe plus
    assert (await client.post("/auth/resend-code", headers=h)).json() == {"sent": True}
    assert (await client.post("/auth/resend-code", headers=h)).status_code == 429   # une fois par minute
    nouveau = boite["essais@test.cm"]
    assert (await client.post("/auth/verify", json={"code": nouveau}, headers=h)).status_code == 200


async def test_admin_peut_confirmer(client, boite):
    from sqlalchemy import update

    from app.db import SessionLocal
    from app.models import User
    _, h = await inscrire(client, "sans.mail@test.cm")
    _, a = await inscrire(client, "chef.verif@test.cm")
    async with SessionLocal() as s:
        await s.execute(update(User).where(User.email == "chef.verif@test.cm").values(is_admin=True, email_verified=True))
        await s.commit()
    uid = (await client.get("/me", headers=h)).json()["id"]
    liste = (await client.get("/admin/users?status=unverified", headers=a)).json()["items"]
    assert any(u["id"] == uid for u in liste)
    assert (await client.post(f"/admin/users/{uid}/verify-email", headers=a)).status_code == 200
    me = (await client.get("/me", headers=h)).json()
    assert me["email_verified"] and me["credits"] > 0


async def test_adresse_non_confirmee_reprenable(client, boite):
    """Quelqu'un inscrit l'adresse d'un autre sans la confirmer : le vrai propriétaire peut quand même s'inscrire."""
    r1, _ = await inscrire(client, "awa.vraie@test.cm")
    r2, h2 = await inscrire(client, "awa.vraie@test.cm")
    assert r1.status_code == 201 and r2.status_code == 201
    assert (await client.post("/auth/verify", json={"code": boite["awa.vraie@test.cm"]}, headers=h2)).status_code == 200
    r3, _ = await inscrire(client, "awa.vraie@test.cm")          # une fois confirmée, l'adresse est prise
    assert r3.status_code == 409


def test_production_exige_smtp():
    from app import checks
    from app.config import Settings
    s = Settings(environment="production", email_verification=True, smtp_host="", _env_file=None)
    assert any("SMTP" in e for e in checks.problems(s)[0])
