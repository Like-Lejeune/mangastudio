"""Avis : accord obligatoire, mots bloqués, validation par l'administration, retrait."""
from sqlalchemy import update

from app.db import SessionLocal
from app.models import User

AVIS = {"text": "Mon premier manga en dix minutes, mes enfants adorent !", "rating": 5,
        "display_name": "Awa N.", "role": "Maman, Douala", "consent": True}


async def compte(client, email):
    r = await client.post("/auth/register", json={"email": email, "display_name": "x", "password": "motdepasse"})
    return {"Authorization": f"Bearer {r.json()['token']}"}


async def test_parcours_avis(client):
    u = await compte(client, "auteur.avis@test.cm")
    adm = await compte(client, "admin.avis@test.cm")
    async with SessionLocal() as s:
        await s.execute(update(User).where(User.email == "admin.avis@test.cm").values(is_admin=True))
        await s.commit()

    # Sans accord : refusé. Avec un mot bloqué : refusé.
    assert (await client.put("/testimonials/mine", json={**AVIS, "consent": False}, headers=u)).status_code == 422
    r = await client.put("/testimonials/mine", json={**AVIS, "text": "Une histoire porno vraiment géniale"}, headers=u)
    assert r.status_code == 422 and r.json()["detail"]["code"] == "blocked_terms"

    # Déposé : en attente, invisible sur l'accueil.
    r = await client.put("/testimonials/mine", json=AVIS, headers=u)
    assert r.status_code == 200 and r.json()["status"] == "pending"
    assert (await client.get("/testimonials")).json() == []

    # Un utilisateur ordinaire ne peut pas valider.
    tid = r.json()["id"]
    assert (await client.post(f"/admin/testimonials/{tid}/status", json={"status": "approved"}, headers=u)).status_code == 403

    # L'admin voit l'avis en attente, le publie : il apparaît sur l'accueil, sans adresse e-mail.
    liste = (await client.get("/admin/testimonials?status=pending", headers=adm)).json()
    assert any(t["id"] == tid and t["user_email"] == "auteur.avis@test.cm" for t in liste["items"])
    assert (await client.get("/admin/overview", headers=adm)).json()["testimonials_pending"] >= 1
    assert (await client.post(f"/admin/testimonials/{tid}/status", json={"status": "approved"}, headers=adm)).status_code == 200
    publics = (await client.get("/testimonials")).json()
    assert publics[0] == {"id": tid, "texte": AVIS["text"], "nom": "Awa N.", "role": "Maman, Douala", "note": 5}
    assert "auteur.avis" not in str(publics)

    # Modifier l'avis le remet en attente : il disparaît de l'accueil jusqu'à nouvelle validation.
    r = await client.put("/testimonials/mine", json={**AVIS, "rating": 4}, headers=u)
    assert r.json()["status"] == "pending" and r.json()["id"] == tid
    assert (await client.get("/testimonials")).json() == []

    # Retirer l'avis le supprime.
    assert (await client.delete("/testimonials/mine", headers=u)).status_code == 204
    assert (await client.get("/testimonials/mine", headers=u)).json() is None

    # L'action est au journal d'administration.
    journal = (await client.get("/admin/actions", headers=adm)).json()["items"]
    assert any(a["action"] == "testimonial" for a in journal)
