"""Partage par lien public et téléchargement PDF (filigrane et quota des comptes gratuits)."""
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.db import SessionLocal
from app.models import PdfDownload
from tests.test_flow import wait_done


async def episode_termine(client, email):
    r = await client.post("/auth/register", json={"email": email, "display_name": "Awa N.", "password": "motdepasse"})
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    sid = (await client.post("/series", headers=h, json={"premise": "Une coursière de Yaoundé arrête le temps."})).json()["id"]
    cid = (await client.post(f"/series/{sid}/characters", headers=h, json={"name": "Nadia"})).json()["id"]
    eid = (await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 4, "character_ids": [cid]})).json()["id"]
    ep = await wait_done(client, h, eid)
    assert ep["status"] == "done", ep.get("error")
    return h, eid


async def test_lien_public(client):
    h, eid = await episode_termine(client, "partage@test.cm")
    assert (await client.get(f"/episodes/{eid}", headers=h)).json()["share_url"] is None      # privé par défaut
    r = await client.post(f"/episodes/{eid}/share", json={"enabled": True}, headers=h)
    url = r.json()["url"]
    token = url.rsplit("/", 1)[-1]
    page = await client.get(f"/lire/{token}")
    assert page.status_code == 200 and "text/html" in page.headers["content-type"]
    t = page.text
    assert 'property="og:title"' in t and "Épisode 1" in t and "par Awa N." in t and t.count("<img ") == 4
    assert "partage@test.cm" not in t                                    # jamais l'adresse e-mail
    # Réactiver garde le même lien ; le couper le rend introuvable pour toujours.
    assert (await client.post(f"/episodes/{eid}/share", json={"enabled": True}, headers=h)).json()["url"] == url
    await client.post(f"/episodes/{eid}/share", json={"enabled": False}, headers=h)
    assert (await client.get(f"/lire/{token}")).status_code == 404
    nouveau = (await client.post(f"/episodes/{eid}/share", json={"enabled": True}, headers=h)).json()["url"]
    assert nouveau != url
    # Personne d'autre ne peut partager cet épisode.
    r = await client.post("/auth/register", json={"email": "intrus@test.cm", "display_name": "x", "password": "motdepasse"})
    autre = {"Authorization": f"Bearer {r.json()['token']}"}
    assert (await client.post(f"/episodes/{eid}/share", json={"enabled": True}, headers=autre)).status_code == 404


async def test_pdf_gratuit_filigrane_et_quota(client):
    h, eid = await episode_termine(client, "pdf@test.cm")
    assert (await client.get("/me/pdf-quota", headers=h)).json() == {"limit": 3, "used": 0, "watermark": True}
    r = await client.get(f"/episodes/{eid}/pdf", headers=h)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content[:5] == b"%PDF-"
    assert len(re.findall(rb"/Type\s*/Page\b", r.content)) == 4
    # Retélécharger le même chapitre ne compte pas deux fois.
    await client.get(f"/episodes/{eid}/pdf", headers=h)
    assert (await client.get("/me/pdf-quota", headers=h)).json()["used"] == 1
    # Simuler 3 autres chapitres déjà téléchargés ce mois-ci : le 4e est refusé.
    me = (await client.get("/me", headers=h)).json()
    async with SessionLocal() as s:
        for i in range(2):
            s.add(PdfDownload(user_id=me["id"], episode_id=f"autre{i}", watermark=True))
        await s.commit()
    async with SessionLocal() as s:     # un ancien téléchargement du mois dernier ne compte pas
        s.add(PdfDownload(user_id=me["id"], episode_id="vieux", watermark=True,
                          created_at=datetime.now(timezone.utc) - timedelta(days=40)))
        await s.commit()
    assert (await client.get("/me/pdf-quota", headers=h)).json()["used"] == 3
    # Le chapitre déjà téléchargé reste disponible, un nouveau non.
    assert (await client.get(f"/episodes/{eid}/pdf", headers=h)).status_code == 200
    async with SessionLocal() as s:
        await s.execute(update(PdfDownload).where(PdfDownload.episode_id == eid).values(episode_id="deplace"))
        await s.commit()
    r = await client.get(f"/episodes/{eid}/pdf", headers=h)
    assert r.status_code == 402 and r.json()["detail"]["code"] == "pdf_quota"


def test_filigrane_visible():
    """Le filigrane change bien l'image (bandeau en bas, texte en diagonale)."""
    from PIL import Image

    from app import pdf
    blanche = Image.new("RGB", (1024, 1536), "white")
    avec = pdf._filigrane(blanche, "Créé avec MangaStudio").convert("L")
    assert blanche.convert("L").getextrema()[0] == 255 and avec.getextrema()[0] < 60
    assert avec.crop((0, 1470, 1024, 1536)).getextrema()[0] < 60          # bandeau du bas
    assert avec.crop((300, 500, 724, 1036)).getextrema()[0] < 245         # texte en diagonale
    sortie = pdf.build([None, None], watermark=True, title="t", mention="m")
    assert sortie[:5] == b"%PDF-" and len(re.findall(rb"/Type\s*/Page\b", sortie)) == 2
