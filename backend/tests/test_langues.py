"""Français / anglais : le français reste le défaut, l'anglais est servi quand le site le demande."""
import re
from pathlib import Path

from app import i18n
from tests.test_admin import account, admin  # noqa: F401  (fixture)

EN = {"Accept-Language": "en"}


def test_catalogue_complet():
    """Chaque message fixe renvoyé aux utilisateurs a sa traduction (les routes d'administration restent en français)."""
    racine = Path(__file__).resolve().parents[1] / "app"
    exclus = {"admin_ops.py", "admin.py", "metrics.py", "checks.py", "referrals.py", "trustchange_client.py"}
    motif = re.compile(r'HTTPException\(\d+, "([^"{}]+)"\)|"message": "([^"{}]+)"')
    manquants = []
    for f in racine.rglob("*.py"):
        if f.name in exclus or "providers" in f.parts:
            continue
        for a, b in motif.findall(f.read_text(encoding="utf-8")):
            texte = a or b
            if i18n.tr(texte, "en") == texte:
                manquants.append(f"{f.name}: {texte}")
    assert manquants == []


def test_motifs_dynamiques():
    assert i18n.tr("Code incorrect. Encore 2 essais.", "en") == "Wrong code. 2 attempts left."
    assert i18n.tr("Code incorrect. Encore 1 essai.", "en") == "Wrong code. 1 attempt left."
    assert i18n.tr("Le plan Découverte permet 3 personnages par épisode.", "en") == "The Discovery plan allows 3 characters per episode."
    assert i18n.tr("Il faut 7 crédits, il en reste 2.", "en") == "You need 7 credits; you have 2 left."
    assert i18n.tr("Trop de tentatives. Réessayez dans 15 minutes.", "en") == "Too many attempts. Try again in 15 minutes."
    assert i18n.tr("Pages à refaire : 2, 4.", "en") == "Pages to redo: 2, 4."
    assert i18n.tr("Message inconnu.", "en") == "Message inconnu."          # inconnu : reste en français
    assert i18n.tr("Code incorrect. Encore 2 essais.", "fr") == "Code incorrect. Encore 2 essais."
    assert i18n.parse_accept_language("en-US,en;q=0.9,fr;q=0.8") == "en"
    assert i18n.parse_accept_language("fr-CM,fr;q=0.9") == "fr" and i18n.parse_accept_language(None) == "fr"


async def test_erreurs_traduites(client):
    r = await client.post("/auth/login", json={"email": "personne@test.cm", "password": "mauvais-mdp"})
    assert r.json()["detail"] == "Adresse ou mot de passe incorrect."                # sans en-tête : français, comme avant
    r = await client.post("/auth/login", json={"email": "personne@test.cm", "password": "mauvais-mdp"}, headers=EN)
    assert r.json()["detail"] == "Wrong email or password."
    h = await account(client, "langue.erreurs@test.cm")
    sid = (await client.post("/series", headers=h, json={"premise": "Un coureur de Douala."})).json()["id"]
    r = await client.post(f"/series/{sid}/characters", headers=h | EN, json={"name": "Naruto"})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "protected_character"
    assert r.json()["detail"]["message"].startswith("“Naruto” is a copyrighted character")
    assert (await client.get("/series/inconnue", headers=h | EN)).json()["detail"] == "Series not found."


async def test_langue_du_compte(client):
    h = await account(client, "langue.compte@test.cm")
    assert (await client.get("/me", headers=h)).json()["locale"] == "fr"
    assert (await client.patch("/me", headers=h, json={"locale": "en"})).json() == {"locale": "en"}
    assert (await client.get("/me", headers=h)).json()["locale"] == "en"
    assert (await client.patch("/me", headers=h, json={"locale": "de"})).status_code == 422
    r = await client.post("/auth/register", headers=EN, json={"email": "anglo@test.cm", "display_name": "Ann", "password": "motdepasse"})
    tok = {"Authorization": "Bearer " + r.json()["token"]}
    assert (await client.get("/me", headers=tok)).json()["locale"] == "en"


async def test_concours_en_anglais(client, admin):  # noqa: F811
    from datetime import datetime, timedelta, timezone
    t = datetime.now(timezone.utc)
    body = {"title": "Contes d'Afrique", "title_en": "African Tales", "theme": "Un conte", "theme_en": "",
            "rules": "Règlement", "rules_en": "Rules", "visible": True,
            "starts_at": (t - timedelta(hours=1)).isoformat(), "ends_at": (t + timedelta(days=1)).isoformat(),
            "prizes": [{"rank": 1, "credits": 100, "studio_days": 30}]}
    c = (await client.post("/admin/contests", headers=admin, json=body)).json()
    assert c["title"] == "Contes d'Afrique" and c["title_en"] == "African Tales"
    fr = (await client.get(f"/contests/{c['slug']}")).json()
    en = (await client.get(f"/contests/{c['slug']}", headers=EN)).json()
    assert fr["title"] == "Contes d'Afrique" and fr["phase_label"] == "En cours" and fr["prizes"][0]["label"] == "100 crédits + 30 jours de plan Studio"
    assert en["title"] == "African Tales" and en["rules"] == "Rules" and en["phase_label"] == "Open"
    assert en["theme"] == "Un conte"                     # pas de version anglaise : le français reste
    assert en["prizes"][0]["label"] == "100 credits + 30 days of Studio plan"
    # L'administration voit toujours les deux versions, même avec un navigateur en anglais.
    adm = (await client.get(f"/admin/contests/{c['id']}", headers=admin | EN)).json()
    assert adm["title"] == "Contes d'Afrique" and adm["title_en"] == "African Tales"


async def test_partage_dans_la_langue_de_l_histoire(client):
    from tests.test_partage import episode_termine
    h, eid = await episode_termine(client, "langue.partage@test.cm")
    from sqlalchemy import update

    from app.db import SessionLocal
    from app.models import Episode, Series
    async with SessionLocal() as s:
        sid = (await s.get(Episode, eid)).series_id
        await s.execute(update(Series).where(Series.id == sid).values(language="en"))
        await s.commit()
    url = (await client.post(f"/episodes/{eid}/share", headers=h, json={"enabled": True})).json()["url"]
    page = (await client.get("/lire/" + url.rsplit("/", 1)[-1])).text
    assert '<html lang="en">' in page and "Create my manga for free" in page and "Episode 1" in page
    introuvable = await client.get("/lire/inconnu", headers=EN)
    assert introuvable.status_code == 404 and "no longer shared" in introuvable.text
