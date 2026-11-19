"""Vérifie que les fichiers du projet sont ceux de la dernière version livrée.

    python verifier_fichiers.py        (depuis le dossier mangastudio)
"""
import hashlib
import os
import sys

ATTENDUS = {
    ".dockerignore": "c229f046e7c9806a",
    ".env.production.example": "36f24555080101ab",
    ".gitignore": "c8f6d3984e60686e",
    "Caddyfile": "16704b2828f44222",
    "DEPLOIEMENT.md": "65916410a72cabc9",
    "README.md": "d470eb36f41a1c43",
    "TEST_LOCAL.md": "594c19db627ebde8",
    "backend/.dockerignore": "1ee897f5df60df4d",
    "backend/.env.example": "d9cc3de7128367a4",
    "backend/Dockerfile": "5abd6ae629ae8af3",
    "backend/README.md": "93113b3bf102fdb3",
    "backend/app/billing/base.py": "07d9545a6e168724",
    "backend/app/billing/stripe_provider.py": "223707e5efe40e1c",
    "backend/app/billing/trust.py": "4ab18ec4e9f8f909",
    "backend/app/billing/trustchange_client.py": "56877826ee67dcb5",
    "backend/app/config.py": "e457bcc82f496c50",
    "backend/app/db.py": "714cabf3c2dc9ad9",
    "backend/app/main.py": "396e521d06606d30",
    "backend/app/models.py": "96bfc1c40823ca8b",
    "backend/app/moderation.py": "e3912a72e9ae8445",
    "backend/app/pipeline/prompts.py": "dd0cbbb8e16864b9",
    "backend/app/pipeline/runner.py": "1fad64889dc66ca7",
    "backend/app/pipeline/script.py": "fbd7e9341f4f91d9",
    "backend/app/plans.py": "5f3b2ac981dba7a2",
    "backend/app/providers/__init__.py": "a9da7894ee368785",
    "backend/app/providers/base.py": "92dc198d1fc9adc5",
    "backend/app/providers/fake.py": "17d416319ec37d1b",
    "backend/app/providers/meta_muse.py": "75c5a69bc7a39858",
    "backend/app/providers/openai_compat.py": "375a22860e09dd5d",
    "backend/app/queue.py": "d3425f14a9707ff5",
    "backend/app/routers/admin.py": "407cf1ab0f761997",
    "backend/app/routers/auth.py": "ca392f2563266f30",
    "backend/app/routers/billing.py": "324404f8aa924081",
    "backend/app/routers/episodes.py": "abe5f13b1da468f9",
    "backend/app/routers/series.py": "fb800e673a60bf52",
    "backend/app/schemas.py": "2c1831d7efc39ac9",
    "backend/app/security.py": "9e0ba3bf4294cdfc",
    "backend/app/services.py": "1ffc7817c194c386",
    "backend/app/storage.py": "2777055f53019443",
    "backend/app/usage.py": "07eb8487e460fd2d",
    "backend/app/worker.py": "63a7983ac40b5dae",
    "backend/pytest.ini": "40b68664e0888847",
    "backend/requirements.txt": "b8fd2f782373fa3e",
    "backend/scripts/banc_essai.py": "030217ae6ee50b3d",
    "backend/scripts/parcours_local.py": "d6d6f47ef24c16f2",
    "backend/tests/conftest.py": "047797c20a939951",
    "backend/tests/test_flow.py": "d323c48fabba3467",
    "backend/tests/test_moderation.py": "5556dd794381a7c2",
    "backend/tests/test_muse.py": "7df8f05535a59ccb",
    "backend/tests/test_trust.py": "53841965d880569f",
    "backend/tests/trust_fake.py": "f66c50b7abc3de75",
    "deploy.bat": "88952071cbf06845",
    "deploy.ps1": "78540fb57e208ff6",
    "deploy.sh": "8ab91870f5c4f0c0",
    "docker-compose.yml": "dad210bff9dc6059",
    "frontend/.env.example": "eaa8503379c11ade",
    "frontend/Dockerfile": "ecdb3d5cf34d24f0",
    "frontend/index.html": "2d760d9159cc40df",
    "frontend/package.json": "16ecedca6c15b203",
    "frontend/public/brand/logo-inverse.svg": "a2ee887c47d15410",
    "frontend/public/brand/logo.svg": "ae535d2b7f384481",
    "frontend/public/brand/symbole.svg": "0c2acfaa6f0f697c",
    "frontend/src/components/AuthForm.tsx": "b0567a1e0ee36bc1",
    "frontend/src/components/TopBar.tsx": "fe20e970d6639ee7",
    "frontend/src/components/ink.tsx": "ceb0ba64787be615",
    "frontend/src/lib/api.ts": "8026b88ff5d603aa",
    "frontend/src/lib/session.ts": "199cef6538e618d9",
    "frontend/src/lib/utils.ts": "64fc84c1be627f0d",
    "frontend/src/main.tsx": "edaa9c4b08c6b96c",
    "frontend/src/routeTree.gen.ts": "27c4c14aac629c2f",
    "frontend/src/routes/__root.tsx": "79d0bc738d0076f4",
    "frontend/src/routes/abonnements.tsx": "2eebf8c72e63c429",
    "frontend/src/routes/connexion.tsx": "d223b750523970ca",
    "frontend/src/routes/episodes.$id.tsx": "855778d7a1d8d411",
    "frontend/src/routes/index.tsx": "e16e692a0697818c",
    "frontend/src/routes/inscription.tsx": "2a5eda423e16bd39",
    "frontend/src/routes/series.$id.tsx": "654b530bcac2ca95",
    "frontend/src/styles.css": "81180e06e8a33a21",
    "frontend/tsconfig.json": "357e4358413314b2",
    "frontend/vite.config.ts": "08ce304175bfa22a"
}
VIDES = [
    "backend/app/__init__.py",
    "backend/app/billing/__init__.py",
    "backend/app/pipeline/__init__.py",
    "backend/app/routers/__init__.py",
    "backend/scripts/__init__.py",
    "backend/tests/__init__.py"
]          # fichiers vides : créés automatiquement s'ils manquent
A_SUPPRIMER = ["backend/app/billing/mobile_money.py", "backend/demarrer.ps1", "frontend/src/pages/Login.tsx", "frontend/src/App.tsx"]


def empreinte(chemin):
    data = open(chemin, "rb").read().replace(b"\r\n", b"\n").lstrip(b"\xef\xbb\xbf")
    return hashlib.sha256(data).hexdigest()[:16]


def main():
    if not os.path.isdir("backend"):
        print("Lancez ce script depuis le dossier mangastudio (celui qui contient backend).")
        return 1
    manquants = [f for f in ATTENDUS if not os.path.exists(f)]
    perimes = [f for f in ATTENDUS if os.path.exists(f) and empreinte(f) != ATTENDUS[f]]
    en_trop = [f for f in A_SUPPRIMER if os.path.exists(f)]
    for f in VIDES:
        if not os.path.exists(f):
            os.makedirs(os.path.dirname(f), exist_ok=True)
            open(f, "w").close()
            print("créé (fichier vide) :", f)
    for titre, liste in (("MANQUANTS", manquants), ("PÉRIMÉS ou modifiés", perimes), ("À SUPPRIMER", en_trop)):
        if liste:
            print("\n" + titre + " :")
            for f in liste:
                print("  ", f)
    if manquants or perimes or en_trop:
        print("\n%d fichier(s) à corriger sur %d." % (len(manquants) + len(perimes) + len(en_trop), len(ATTENDUS)))
        return 1
    print("Les %d fichiers sont à jour." % len(ATTENDUS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
