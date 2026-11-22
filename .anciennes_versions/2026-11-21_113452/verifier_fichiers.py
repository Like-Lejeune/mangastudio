"""Vérifie que les fichiers du projet sont ceux de la dernière version livrée.

    python verifier_fichiers.py        (depuis le dossier mangastudio)
"""
import hashlib
import os
import sys

ATTENDUS = {
    ".dockerignore": "95888391a7bfdc19",
    ".env.production.example": "31a8504ae25de007",
    ".gitattributes": "83d39627ed864dda",
    ".gitignore": "46ff76ba1988f067",
    "Caddyfile": "b494d7f8c9816d78",
    "Caddyfile.proxy": "f7e27076c4012f8e",
    "DEPLOIEMENT.md": "6573de55c47fcbdb",
    "README.md": "d470eb36f41a1c43",
    "TEST_LOCAL.md": "4a2d2d87672a1e86",
    "backend/.dockerignore": "1ee897f5df60df4d",
    "backend/.env.example": "b57f14003ed870d5",
    "backend/Dockerfile": "357b995868f03368",
    "backend/README.md": "9e728d01aedd3659",
    "backend/alembic.ini": "3ba1b0861b8e4f5b",
    "backend/app/billing/base.py": "2d694bd3c65b897b",
    "backend/app/billing/stripe_provider.py": "223707e5efe40e1c",
    "backend/app/billing/trust.py": "6cdf4e79c71010c2",
    "backend/app/billing/trustchange_client.py": "56877826ee67dcb5",
    "backend/app/budget.py": "d7649e7e5c55d979",
    "backend/app/checks.py": "f90f961b284c32f2",
    "backend/app/config.py": "6e80d9a320b5040d",
    "backend/app/db.py": "b1f556d202a92600",
    "backend/app/main.py": "6843a659d4ea0a8c",
    "backend/app/models.py": "6778937b281f449c",
    "backend/app/moderation.py": "e3912a72e9ae8445",
    "backend/app/moderation_defaults.py": "f8842773332c0c01",
    "backend/app/pipeline/prompts.py": "dd0cbbb8e16864b9",
    "backend/app/pipeline/runner.py": "84a53f122c14cba7",
    "backend/app/pipeline/script.py": "fbd7e9341f4f91d9",
    "backend/app/plans.py": "5f3b2ac981dba7a2",
    "backend/app/providers/__init__.py": "a9da7894ee368785",
    "backend/app/providers/base.py": "92dc198d1fc9adc5",
    "backend/app/providers/fake.py": "17d416319ec37d1b",
    "backend/app/providers/meta_muse.py": "1f73d874726b4fa3",
    "backend/app/providers/openai_compat.py": "6161a2c197657303",
    "backend/app/queue.py": "d3425f14a9707ff5",
    "backend/app/ratelimit.py": "95c33811db3886b1",
    "backend/app/routers/admin.py": "03f5d1d8663846e6",
    "backend/app/routers/admin_ops.py": "b44bbeed756ca12d",
    "backend/app/routers/auth.py": "ced0d25f26592259",
    "backend/app/routers/billing.py": "d73d918d5edfb2d4",
    "backend/app/routers/episodes.py": "7c41545a89c996c1",
    "backend/app/routers/series.py": "c44ee01284a0a7d8",
    "backend/app/schemas.py": "6ada3559099e4d83",
    "backend/app/security.py": "5755d92593d1ed79",
    "backend/app/services.py": "1ffc7817c194c386",
    "backend/app/storage.py": "2777055f53019443",
    "backend/app/usage.py": "07eb8487e460fd2d",
    "backend/app/worker.py": "63a7983ac40b5dae",
    "backend/migrations/env.py": "432bb969134d9f64",
    "backend/migrations/script.py.mako": "076c1ca8f3e31329",
    "backend/migrations/versions/20261116_0001_schema_initial.py": "669c99607bd269e1",
    "backend/migrations/versions/20261116_0002_admin_suspension_et_journal.py": "8a426189a1270361",
    "backend/migrations/versions/20261118_0003_moderation_liste_initiale.py": "5e1b552fa20e95d8",
    "backend/pytest.ini": "40b68664e0888847",
    "backend/requirements.txt": "4a906c86317d03b2",
    "backend/scripts/banc_essai.py": "22eabe1195632fa2",
    "backend/scripts/controle_securite.py": "b6313f80617fc357",
    "backend/scripts/parcours_local.py": "d6d6f47ef24c16f2",
    "backend/scripts/test_scenes.py": "80a73dd938112afc",
    "backend/tests/conftest.py": "4685d06b73c1b4ed",
    "backend/tests/test_admin.py": "a701f6739a4cb309",
    "backend/tests/test_flow.py": "d432bd56428f3a1e",
    "backend/tests/test_moderation.py": "5556dd794381a7c2",
    "backend/tests/test_moderation_liste.py": "59cc4311be2c28f2",
    "backend/tests/test_muse.py": "7df8f05535a59ccb",
    "backend/tests/test_securite.py": "887617b59a7c7dfb",
    "backend/tests/test_trust.py": "834bd0b7dd3d4a9e",
    "backend/tests/trust_fake.py": "f66c50b7abc3de75",
    "deploy.bat": "88952071cbf06845",
    "deploy.ps1": "6767010284b6da5d",
    "deploy.sh": "8ab91870f5c4f0c0",
    "docker-compose.yml": "f6490d9c6fc928a1",
    "frontend/.env.example": "eaa8503379c11ade",
    "frontend/Dockerfile": "c9d09ff88c361dda",
    "frontend/index.html": "2d760d9159cc40df",
    "frontend/package.json": "5a62729040c19a34",
    "frontend/public/brand/logo-inverse.svg": "a2ee887c47d15410",
    "frontend/public/brand/logo.svg": "ae535d2b7f384481",
    "frontend/public/brand/symbole.svg": "0c2acfaa6f0f697c",
    "frontend/src/components/AuthForm.tsx": "b0567a1e0ee36bc1",
    "frontend/src/components/Footer.tsx": "bce250969ecb43eb",
    "frontend/src/components/MobileMoneyCheckout.tsx": "bf96a269975ce126",
    "frontend/src/components/TopBar.tsx": "3fefe1107a3b263f",
    "frontend/src/components/accueil/Accueil.tsx": "b7a624b3808a62c6",
    "frontend/src/components/accueil/Planche.tsx": "a6d9eddf1f92e1ad",
    "frontend/src/components/admin.tsx": "4c7825363bb035f8",
    "frontend/src/components/ink.tsx": "ceb0ba64787be615",
    "frontend/src/content/accueil.ts": "6c9c84bbbfeeec1d",
    "frontend/src/content/contact.ts": "14e3fcb8d77ebc1b",
    "frontend/src/content/faq.ts": "4b0849ee542e93b7",
    "frontend/src/lib/admin.ts": "7b9831d1c84acfc3",
    "frontend/src/lib/api.ts": "58f7e66894787b9b",
    "frontend/src/lib/contact.ts": "9135b49c2f1ce6fb",
    "frontend/src/lib/session.ts": "199cef6538e618d9",
    "frontend/src/lib/utils.ts": "64fc84c1be627f0d",
    "frontend/src/main.tsx": "edaa9c4b08c6b96c",
    "frontend/src/routeTree.gen.ts": "3b5857098acd33dc",
    "frontend/src/routes/__root.tsx": "19066aa3f6563359",
    "frontend/src/routes/abonnements.tsx": "f512214adb259891",
    "frontend/src/routes/admin.tsx": "8ad2de8f8d0db026",
    "frontend/src/routes/admin/episodes.$id.tsx": "be471f89781675c4",
    "frontend/src/routes/admin/episodes.index.tsx": "f5cac4217616e775",
    "frontend/src/routes/admin/index.tsx": "34a925de67d016b1",
    "frontend/src/routes/admin/journal.tsx": "9d486ab68796c84d",
    "frontend/src/routes/admin/moderation.tsx": "01bc643be1eb02f0",
    "frontend/src/routes/admin/paiements.tsx": "9e816a1a84ca8c2a",
    "frontend/src/routes/admin/utilisateurs.$id.tsx": "e2d2c5b9db61f709",
    "frontend/src/routes/admin/utilisateurs.index.tsx": "396bd183d962b83b",
    "frontend/src/routes/connexion.tsx": "d223b750523970ca",
    "frontend/src/routes/contact.tsx": "831fac9ec305bac0",
    "frontend/src/routes/episodes.$id.tsx": "855778d7a1d8d411",
    "frontend/src/routes/faq.tsx": "063b93d02f463069",
    "frontend/src/routes/index.tsx": "ee16eb04545a8b79",
    "frontend/src/routes/inscription.tsx": "2a5eda423e16bd39",
    "frontend/src/routes/series.$id.tsx": "654b530bcac2ca95",
    "frontend/src/routes/soutenir.tsx": "2d069a68608a4228",
    "frontend/src/styles.css": "6b5e9e7a6b094abc",
    "frontend/tsconfig.json": "357e4358413314b2",
    "frontend/vite.config.ts": "08ce304175bfa22a",
    "vps/deployer.sh": "7e8075552cb9e1d7",
    "vps/nginx-mangastudio.conf": "ed5ad50dc85dc4f5",
    "vps/sauvegarde.sh": "d0af29dacde2516e"
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
