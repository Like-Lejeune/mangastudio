"""Parcours complet contre l'API lancée en local : vérifie en une minute que tout tient ensemble.

    python -m scripts.parcours_local                      # API sur http://localhost:8000
    python -m scripts.parcours_local --api http://...     # autre adresse

Crée un compte de test, une série, trois personnages, lance un épisode de 4 pages,
attend la fin et contrôle le compteur et le solde. Avec les modèles factices, c'est
gratuit ; avec les vrais modèles du .env, l'épisode est réellement dessiné (et payé).
"""
import argparse
import sys
import time
import uuid

import httpx

OK, KO = "  [OK]", "  [ÉCHEC]"


def main(base: str) -> int:
    failures = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal failures
        print(f"{OK if condition else KO} {label}{'' if condition else ' — ' + detail}")
        failures += 0 if condition else 1

    with httpx.Client(base_url=base, timeout=60) as c:
        try:
            check("L'API répond", c.get("/health").json() == {"ok": True})
        except httpx.HTTPError as e:
            print(f"{KO} L'API ne répond pas sur {base} ({e}). Lancez-la d'abord avec demarrer.ps1.")
            return 1

        email = f"test-{uuid.uuid4().hex[:8]}@local.test"
        r = c.post("/auth/register", json={"email": email, "display_name": "Test local", "password": "motdepasse"})
        check("Inscription", r.status_code == 201, r.text)
        c.headers["Authorization"] = f"Bearer {r.json()['token']}"
        me = c.get("/me").json()
        check("Compte : plan gratuit et 12 crédits offerts", me["plan"]["id"] == "free" and me["credits"] == 12, str(me))

        r = c.post("/series", json={"premise": "Trois amis ratent le dernier bus et la ville change après minuit.", "style": "shonen", "palette": "bw", "language": "fr"})
        check("Création d'une série", r.status_code == 201, r.text)
        sid = r.json()["id"]
        r = c.post("/series", json={"premise": "Une série en couleur sur le plan gratuit.", "palette": "color"})
        check("La couleur est refusée sur le plan gratuit", r.status_code == 403, r.text)

        ids = []
        for name, role in (("Awa", "la meneuse"), ("Brice", "le rival"), ("Chantal", "la mécano"), ("Didier", "le chauffeur")):
            r = c.post(f"/series/{sid}/characters", json={"name": name, "role": role, "description": f"{name}, {role}, blouson en jean"})
            ids.append(r.json().get("id"))
        check("Ajout de quatre personnages", all(ids), str(ids))

        r = c.post(f"/series/{sid}/episodes", json={"page_count": 4, "character_ids": ids})
        check("Quatre personnages refusés sur le plan gratuit (limite : 3)", r.status_code == 403, r.text)
        r = c.post(f"/series/{sid}/episodes", json={"page_count": 4, "character_ids": ids[:3], "direction": "Le bus revient sans chauffeur."})
        check("Lancement d'un épisode de 4 pages", r.status_code == 202, r.text)
        if r.status_code != 202:
            return 1
        eid = r.json()["id"]

        print("  ... génération en cours", end="", flush=True)
        start, ep = time.monotonic(), {}
        while time.monotonic() - start < 600:
            ep = c.get(f"/episodes/{eid}").json()
            if ep["status"] in ("done", "failed", "blocked"):
                break
            print(".", end="", flush=True)
            time.sleep(2)
        print(f" {time.monotonic() - start:.0f} s")

        check("Épisode terminé", ep.get("status") == "done", f"statut {ep.get('status')} : {ep.get('error')}")
        pages = ep.get("pages", [])
        check("Quatre pages dessinées", len(pages) == 4 and all(p["url"] for p in pages), str([p["status"] for p in pages]))
        if pages and pages[0]["url"]:
            check("L'image de la page 1 se télécharge", httpx.get(pages[0]["url"], timeout=30).status_code == 200, pages[0]["url"])
        u = ep.get("usage", {})
        check("Compteur : 8 images (3 fiches, 4 pages, 1 couverture) et 8 crédits", u.get("images", 0) >= 8 and u.get("credits") == 8, str(u))
        check("Compteur : des tokens sont comptés", u.get("input_tokens", 0) > 0 and u.get("output_tokens", 0) > 0, str(u))
        check("Solde : 12 - 8 = 4 crédits", c.get("/me").json()["credits"] == 4)

        r = c.post(f"/series/{sid}/episodes", json={"page_count": 5, "character_ids": ids[:3]})
        check("Un second épisode est refusé faute de crédits", r.status_code == 402, r.text)
        r = c.get("/plans")
        check("Plans : trois plans et un pack", r.status_code == 200 and len(r.json()["plans"]) == 3 and "pack" in r.json(), r.text)
        r = c.get("/billing/operators")
        if r.status_code == 503:
            print("  [INFO] Paiement TrustChange non configuré (pas de TRUSTCHANGE_API_KEY) : étape sautée.")
        else:
            check("TrustChange : la liste des opérateurs se charge", r.status_code == 200, r.text[:300])
            if r.status_code == 200:
                print(f"         Réponse brute (à m'envoyer pour caler le front) : {r.text[:400]}")

    print("\nTout est bon." if not failures else f"\n{failures} vérification(s) en échec.")
    print(f"Épisode : {base}/episodes/{eid}  ·  compte de test : {email} / motdepasse")
    return 1 if failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    sys.exit(main(parser.parse_args().api.rstrip("/")))
