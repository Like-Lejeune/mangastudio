"""Liste de contrôle de sécurité avant la mise en ligne.

    Sur votre machine, depuis backend :   python -m scripts.controle_securite --env ../.env.production
    Sur le VPS, depuis mangastudio :      docker compose run --rm --no-deps --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD:/repo:ro" api \\
                                            python -m scripts.controle_securite --racine /repo --env /repo/.env.production

Vérifie : secrets hors du dépôt git, aucune clé écrite en dur dans le code, configuration de
production (clé de signature, HTTPS, CORS, admins, plafond IA, webhook signé), en-têtes Caddy.
Code de sortie 1 si un point bloquant échoue.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

from app import checks
from app.config import Settings

IGNORES = ("node_modules", "dist", ".venv", "__pycache__", ".git", "storage", ".logs", ".tanstack", ".pytest_cache", ".ruff_cache")
SECRETS = [
    (re.compile(r"tc_live_[A-Za-z0-9]{8,}"), "clé TrustChange de production"),
    (re.compile(r"tc_test_[A-Za-z0-9]{12,}"), "clé TrustChange de test"),
    (re.compile(r"sk_live_[A-Za-z0-9]{12,}"), "clé Stripe de production"),
    (re.compile(r"whsec_[A-Za-z0-9]{12,}"), "secret de webhook Stripe"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "clé privée"),
    (re.compile(r"(?im)^[ \t]*(?:META_API_KEY|SECRET_KEY|POSTGRES_PASSWORD|TRUSTCHANGE_API_KEY|TRUSTCHANGE_WEBHOOK_SECRET|OPENAI_COMPAT_API_KEY)[ \t]*=[ \t]*['\"]?(?!change-moi)[A-Za-z0-9_\-]{16,}"), "secret renseigné"),
]
GITIGNORE = [".env", "*.db", "storage"]

ok_count = fail_count = 0


def point(ok: bool, texte: str, bloquant: bool = True) -> None:
    global ok_count, fail_count
    if ok:
        ok_count += 1
        print(f"  [OK]     {texte}")
    elif bloquant:
        fail_count += 1
        print(f"  [ÉCHEC]  {texte}")
    else:
        print(f"  [ATTENTION] {texte}")


def fichiers_du_depot(racine: Path) -> tuple[list[Path], bool]:
    """Fichiers suivis par git si c'est un dépôt, sinon tous les fichiers du projet."""
    try:
        out = subprocess.run(["git", "ls-files"], cwd=racine, capture_output=True, text=True, check=True).stdout
        return [racine / f for f in out.splitlines()], True
    except (OSError, subprocess.CalledProcessError):
        return [p for p in racine.rglob("*") if p.is_file() and not any(part in IGNORES for part in p.parts)], False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--racine", default="..", help="dossier mangastudio")
    ap.add_argument("--env", help="fichier .env.production à contrôler")
    args = ap.parse_args()
    racine = Path(args.racine).resolve()

    print("\n1. Secrets hors du dépôt")
    gi = (racine / ".gitignore").read_text(encoding="utf-8") if (racine / ".gitignore").exists() else ""
    for motif in GITIGNORE:
        point(motif in gi, f".gitignore exclut {motif}")
    fichiers, git = fichiers_du_depot(racine)
    if not git:
        print("  (pas de dépôt git ici : tous les fichiers du projet sont examinés)")
    suivis_interdits = [f for f in fichiers if re.search(r"(^|/)\.env(\.production)?$|\.db$", f.as_posix()) and git]
    point(not suivis_interdits, "aucun .env ni base de données suivi par git" + (f" ({', '.join(str(f.relative_to(racine)) for f in suivis_interdits)})" if suivis_interdits else ""))
    trouves = []
    for f in fichiers:
        if f.suffix in (".png", ".jpg", ".webp", ".ico", ".woff", ".woff2", ".zip", ".db") or not f.exists():
            continue
        if not git and re.search(r"(^|/)\.env(\.production)?$", f.as_posix()):
            continue   # hors git, les vrais .env sont normaux : ils ne partent pas sur GitHub
        try:
            texte = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for motif, nom in SECRETS:
            if motif.search(texte):
                trouves.append(f"{f.relative_to(racine)} : {nom}")
    point(not trouves, "aucune clé écrite dans le code" + ("".join(f"\n             - {t}" for t in trouves) if trouves else ""))

    print("\n2. Configuration de production")
    if args.env:
        env = Path(args.env)
        if not env.exists():
            point(False, f"{env} introuvable")
        else:
            s = Settings(_env_file=str(env), environment="production")
            if not re.search(r"(?m)^DATABASE_URL=", env.read_text(encoding="utf-8")):
                # docker-compose.yml fournit l'adresse PostgreSQL : rien à écrire dans le fichier.
                s.database_url = "postgresql+asyncpg://manga@db/manga"
            erreurs, alertes = checks.problems(s)
            for e in erreurs:
                point(False, e)
            for a in alertes:
                point(False, a, bloquant=False)
            if not erreurs:
                point(True, "clé de signature, HTTPS, base PostgreSQL, fournisseurs IA, webhook signé")
            point(all(o.startswith("https://") for o in s.frontend_url.split(",")), "CORS limité aux adresses https:// de FRONTEND_URL")
    else:
        print("  (passez --env ../.env.production pour contrôler la configuration)")

    print("\n3. Serveur web")
    caddy = (racine / "Caddyfile").read_text(encoding="utf-8") if (racine / "Caddyfile").exists() else ""
    for entete in ("Strict-Transport-Security", "Content-Security-Policy", "X-Content-Type-Options", "frame-ancestors 'none'"):
        point(entete in caddy, f"Caddy envoie {entete}")
    point("max_size" in caddy, "Caddy limite la taille des envois")
    compose = (racine / "docker-compose.yml").read_text(encoding="utf-8") if (racine / "docker-compose.yml").exists() else ""
    api = compose.split("  api:")[1].split("\n  worker:")[0] if "  api:" in compose else ""
    point("ports:" not in api, "l'API n'est pas exposée directement (seulement via Caddy)")

    print(f"\nRésultat : {ok_count} points validés, {fail_count} à corriger.")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())