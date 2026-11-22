"""Mot de passe oublié : code par e-mail, rien de révélé sur les comptes, anciennes sessions fermées."""
import pytest

from app import mailer


@pytest.fixture
def boite(monkeypatch):
    recus: dict[str, str] = {}

    async def faux_envoi(to, name, code, minutes):
        recus[to] = code
    monkeypatch.setattr(mailer, "send_reset_code", faux_envoi)
    return recus


async def test_parcours_complet(client, boite):
    r = await client.post("/auth/register", json={"email": "oublie@test.cm", "display_name": "Paul", "password": "ancienmdp"})
    ancien = {"Authorization": f"Bearer {r.json()['token']}"}
    assert (await client.get("/me", headers=ancien)).status_code == 200

    # Même réponse pour un compte inconnu : on ne révèle pas quelles adresses sont inscrites.
    assert (await client.post("/auth/forgot-password", json={"email": "personne@test.cm"})).json() == {"sent": True}
    assert "personne@test.cm" not in boite
    assert (await client.post("/auth/forgot-password", json={"email": "Oublie@Test.cm"})).json() == {"sent": True}
    code = boite["oublie@test.cm"]
    assert (await client.post("/auth/forgot-password", json={"email": "oublie@test.cm"})).status_code == 429   # 1 par minute

    faux = "000000" if code != "000000" else "111111"
    r = await client.post("/auth/reset-password", json={"email": "oublie@test.cm", "code": faux, "password": "nouveaumdp"})
    assert r.status_code == 422
    assert (await client.post("/auth/reset-password", json={"email": "oublie@test.cm", "code": code, "password": "court"})).status_code == 422

    r = await client.post("/auth/reset-password", json={"email": "oublie@test.cm", "code": code, "password": "nouveaumdp"})
    assert r.status_code == 200
    nouveau = {"Authorization": f"Bearer {r.json()['token']}"}
    assert (await client.get("/me", headers=nouveau)).status_code == 200
    # L'ancienne session est fermée, l'ancien mot de passe ne marche plus, le code ne resert pas.
    assert (await client.get("/me", headers=ancien)).status_code == 401
    assert (await client.post("/auth/login", json={"email": "oublie@test.cm", "password": "ancienmdp"})).status_code == 401
    assert (await client.post("/auth/login", json={"email": "oublie@test.cm", "password": "nouveaumdp"})).status_code == 200
    assert (await client.post("/auth/reset-password", json={"email": "oublie@test.cm", "code": code, "password": "encoreunautre"})).status_code == 410


async def test_cinq_essais_maximum(client, boite):
    await client.post("/auth/register", json={"email": "essais.mdp@test.cm", "display_name": "x", "password": "motdepasse"})
    await client.post("/auth/forgot-password", json={"email": "essais.mdp@test.cm"})
    code = boite["essais.mdp@test.cm"]
    faux = "000000" if code != "000000" else "111111"
    for _ in range(5):
        await client.post("/auth/reset-password", json={"email": "essais.mdp@test.cm", "code": faux, "password": "nouveaumdp"})
    r = await client.post("/auth/reset-password", json={"email": "essais.mdp@test.cm", "code": code, "password": "nouveaumdp"})
    assert r.status_code == 429


async def test_compte_inconnu(client, boite):
    r = await client.post("/auth/reset-password", json={"email": "fantome@test.cm", "code": "123456", "password": "nouveaumdp"})
    assert r.status_code == 410
