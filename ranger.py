"""Range les fichiers livrés à leur place dans le projet.

    1. Déposez les fichiers reçus dans le dossier  a_ranger  (à la racine de mangastudio).
    2. Depuis le dossier mangastudio :   python ranger.py

Autres usages :
    python ranger.py --essai                       montre ce qui serait fait, sans rien toucher
    python ranger.py --depuis "C:\\Users\\FAYA COMPUTER\\Downloads"
                                                   range directement depuis un autre dossier

Comment le script sait où va chaque fichier : verifier_fichiers.py contient l'empreinte de
chaque fichier de la dernière livraison. Un fichier dont le contenu correspond à une empreinte
va exactement à cet endroit, même si deux fichiers portent le même nom (contact.ts) ou si
Windows l'a renommé au téléchargement (« Dockerfile (1) », « Caddyfile.proxy.txt »).
Si verifier_fichiers.py fait partie des fichiers déposés, c'est sa version (la plus récente)
qui sert de référence ; il est rangé en premier.

L'ancienne version de chaque fichier remplacé est gardée dans .anciennes_versions/<date>/,
au même chemin. Un fichier que le script ne sait pas placer reste dans le dossier de dépôt,
avec l'explication.
"""
import argparse
import ast
import hashlib
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent
DEPOT = RACINE / "a_ranger"
ARCHIVES = RACINE / ".anciennes_versions"
MANIFESTE = "verifier_fichiers.py"


def empreinte(data: bytes) -> str:
    """Même calcul que verifier_fichiers.py : fins de ligne et BOM ignorés."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n").lstrip(b"\xef\xbb\xbf")).hexdigest()[:16]


def lire_manifeste(fichier: Path) -> dict[str, str]:
    texte = fichier.read_text(encoding="utf-8")
    m = re.search(r"ATTENDUS = (\{.*?\n\})", texte, re.S)
    if not m:
        sys.exit(f"Manifeste illisible dans {fichier}")
    return ast.literal_eval(m.group(1))


def nom_d_origine(nom: str, connus: set[str]) -> str:
    """Défait les renommages du navigateur : « contact (1).ts », « Caddyfile.proxy.txt »."""
    nom = re.sub(r" \(\d+\)(?=\.[^.]+$|$)", "", nom)
    if nom.endswith(".txt") and nom not in connus and nom[:-4] in connus:
        nom = nom[:-4]
    return nom


def destination(fichier: Path, attendus: dict[str, str]) -> tuple[str | None, str]:
    """(chemin dans le projet, explication). Chemin None : le fichier reste dans le dépôt."""
    par_nom: dict[str, list[str]] = {}
    for chemin in attendus:
        par_nom.setdefault(chemin.rsplit("/", 1)[-1], []).append(chemin)
    nom = nom_d_origine(fichier.name, set(par_nom))
    e = empreinte(fichier.read_bytes())
    exacts = [c for c, h in attendus.items() if h == e]
    meme_nom = [c for c in exacts if c.endswith("/" + nom) or c == nom]
    if len(meme_nom) == 1:
        return meme_nom[0], "contenu reconnu"
    if len(exacts) == 1:
        return exacts[0], "contenu reconnu (nom différent)"
    candidats = par_nom.get(nom, [])
    if not candidats:
        return None, "nom inconnu du projet : fichier d'un autre projet, ou manifeste pas à jour (ajoutez verifier_fichiers.py au dépôt)"
    if len(candidats) == 1:
        return candidats[0], "nom reconnu, mais contenu différent de la dernière livraison (version plus récente ou modifiée ?)"
    return None, "plusieurs fichiers portent ce nom (" + ", ".join(candidats) + ") et le contenu ne correspond à aucun : déposez aussi le verifier_fichiers.py livré avec"


def main() -> int:
    for flux in (sys.stdout, sys.stderr):   # console Windows : jamais d'erreur sur un caractère accentué
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description="Range les fichiers livrés à leur place dans le projet.")
    ap.add_argument("--depuis", type=Path, default=DEPOT, help="dossier où se trouvent les fichiers (par défaut : a_ranger)")
    ap.add_argument("--essai", action="store_true", help="montrer sans rien modifier")
    args = ap.parse_args()
    depot: Path = args.depuis.resolve()

    if not depot.exists():
        depot.mkdir(parents=True)
        print(f"Dossier créé : {depot}\nDéposez-y les fichiers reçus, puis relancez : python ranger.py")
        return 0
    fichiers = sorted(p for p in depot.iterdir() if p.is_file() and not p.name.startswith(".") and p.suffix.lower() != ".zip")
    if not fichiers:
        print(f"Aucun fichier dans {depot}.")
        return 0

    # Le manifeste déposé (le plus récent) sert de référence et passe en premier.
    manifeste_depose = next((p for p in fichiers if nom_d_origine(p.name, {MANIFESTE}) == MANIFESTE), None)
    attendus = lire_manifeste(manifeste_depose or RACINE / MANIFESTE)
    if manifeste_depose:
        fichiers.remove(manifeste_depose)
        fichiers.insert(0, manifeste_depose)

    horodatage = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    ranges, restes = [], []
    print(("ESSAI : rien ne sera modifié\n" if args.essai else "") + f"Fichiers trouvés dans {depot} : {len(fichiers)}\n")

    for f in fichiers:
        if f is manifeste_depose:
            cible, pourquoi = MANIFESTE, "manifeste de la livraison"
        else:
            cible, pourquoi = destination(f, attendus)
        if cible is None:
            restes.append((f.name, pourquoi))
            continue
        chemin = RACINE / cible
        etat = "remplacé" if chemin.exists() else "nouveau"
        if chemin.exists() and empreinte(chemin.read_bytes()) == empreinte(f.read_bytes()):
            etat = "déjà à jour"
        ranges.append((f.name, cible, etat, pourquoi))
        if args.essai:
            continue
        if etat == "remplacé":
            sauvegarde = ARCHIVES / horodatage / cible
            sauvegarde.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(chemin, sauvegarde)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        if etat == "déjà à jour":
            f.unlink()
        else:
            shutil.move(str(f), str(chemin))

    largeur = max((len(n) for n, *_ in ranges), default=10)
    for nom, cible, etat, pourquoi in ranges:
        alerte = "  ⚠ " + pourquoi if "différent" in pourquoi else ""
        print(f"  {etat:<12} {nom:<{largeur}}  →  {cible}{alerte}")
    if restes:
        print(f"\nRestés dans {depot.name} (à placer à la main ou à me signaler) :")
        for nom, pourquoi in restes:
            print(f"  ✘ {nom} : {pourquoi}")
    if ranges and not args.essai:
        nb = sum(1 for *_, e, _ in ranges if e == "remplacé")
        if nb:
            print(f"\nAnciennes versions gardées dans .anciennes_versions/{horodatage}/ ({nb} fichier(s)).")
        print("\nÉtape suivante : python verifier_fichiers.py, puis git add -A, git commit, git push.")
    return 1 if restes else 0


if __name__ == "__main__":
    sys.exit(main())
