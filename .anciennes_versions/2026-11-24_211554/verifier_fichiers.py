"""Vérifie que les fichiers du projet sont ceux de la dernière version livrée.

    python verifier_fichiers.py        (depuis le dossier mangastudio)
"""
import hashlib
import os
import sys

ATTENDUS = {
    ".dockerignore": "95888391a7bfdc19",
    ".env.production.example": "6323e04ff0668671",
    ".gitattributes": "83d39627ed864dda",
    ".gitignore": "ad5530292d4f15d6",
    "Caddyfile": "ec67e25d32664974",
    "Caddyfile.proxy": "49d46a57b526c1f4",
    "DEPLOIEMENT.md": "3d9541cebe4782c0",
    "README.md": "d470eb36f41a1c43",
    "TEST_LOCAL.md": "4a2d2d87672a1e86",
    "backend/.dockerignore": "1ee897f5df60df4d",
    "backend/.env.example": "d09a9f55d83cb38e",
    "backend/Dockerfile": "d966de8e3ad98006",
    "backend/README.md": "9e728d01aedd3659",
    "backend/alembic.ini": "3ba1b0861b8e4f5b",
    "backend/app/billing/base.py": "fda8f21ddb6d481a",
    "backend/app/billing/stripe_provider.py": "223707e5efe40e1c",
    "backend/app/billing/trust.py": "4906933ea1fe000d",
    "backend/app/billing/trustchange_client.py": "56877826ee67dcb5",
    "backend/app/budget.py": "d7649e7e5c55d979",
    "backend/app/checks.py": "e8d762d90ef588d5",
    "backend/app/config.py": "5734396c2b074f72",
    "backend/app/db.py": "b1f556d202a92600",
    "backend/app/disposable.py": "77f69fbd9030dd4e",
    "backend/app/growth.py": "7f8da517b6a6622c",
    "backend/app/mailer.py": "96656aa741b8da34",
    "backend/app/main.py": "812f9decc1b0b5f5",
    "backend/app/models.py": "28bb877eac1fdeca",
    "backend/app/moderation.py": "e3912a72e9ae8445",
    "backend/app/moderation_defaults.py": "f8842773332c0c01",
    "backend/app/pdf.py": "2683161279e3f302",
    "backend/app/pipeline/prompts.py": "33c84f7b37a91c40",
    "backend/app/pipeline/runner.py": "ea49cb7d6c844472",
    "backend/app/pipeline/script.py": "fbd7e9341f4f91d9",
    "backend/app/plans.py": "2846f17074b30ea3",
    "backend/app/protected.py": "64c4041a168343e8",
    "backend/app/providers/__init__.py": "a9da7894ee368785",
    "backend/app/providers/base.py": "92dc198d1fc9adc5",
    "backend/app/providers/fake.py": "17d416319ec37d1b",
    "backend/app/providers/meta_muse.py": "1f73d874726b4fa3",
    "backend/app/providers/openai_compat.py": "6161a2c197657303",
    "backend/app/queue.py": "d3425f14a9707ff5",
    "backend/app/ratelimit.py": "95c33811db3886b1",
    "backend/app/routers/admin.py": "03f5d1d8663846e6",
    "backend/app/routers/admin_ops.py": "366426ae39316f57",
    "backend/app/routers/auth.py": "9352dce63941b288",
    "backend/app/routers/billing.py": "0d03e33af0d7a64e",
    "backend/app/routers/episodes.py": "85c02a8601a398a6",
    "backend/app/routers/gallery.py": "1df83cee6d39800e",
    "backend/app/routers/referrals.py": "9491338e6732a2ad",
    "backend/app/routers/series.py": "0788a5178ea9a9e0",
    "backend/app/routers/sharing.py": "31dfc01fbaa05e45",
    "backend/app/routers/testimonials.py": "42e6b70551eb0b3c",
    "backend/app/schemas.py": "b7bdb961aad776e9",
    "backend/app/security.py": "adea8076f9efb16a",
    "backend/app/services.py": "1ffc7817c194c386",
    "backend/app/storage.py": "d1113ee770f18a4a",
    "backend/app/usage.py": "07eb8487e460fd2d",
    "backend/app/worker.py": "63a7983ac40b5dae",
    "backend/migrations/env.py": "432bb969134d9f64",
    "backend/migrations/script.py.mako": "076c1ca8f3e31329",
    "backend/migrations/versions/20261116_0001_schema_initial.py": "669c99607bd269e1",
    "backend/migrations/versions/20261116_0002_admin_suspension_et_journal.py": "8a426189a1270361",
    "backend/migrations/versions/20261118_0003_moderation_liste_initiale.py": "5e1b552fa20e95d8",
    "backend/migrations/versions/20261121_0004_avis.py": "7e39ff38c2644395",
    "backend/migrations/versions/20261121_0005_verification_email.py": "aaefb8673ae9d56f",
    "backend/migrations/versions/20261121_0006_mot_de_passe_oublie.py": "783c5e65b8dcd673",
    "backend/migrations/versions/20261124_0007_partage_et_pdf.py": "e4d9b09af1875e72",
    "backend/migrations/versions/20261124_0008_parrainage_et_missions.py": "925d8504855830a8",
    "backend/migrations/versions/20261124_0009_galerie_et_likes.py": "6dc52f96287cb91f",
    "backend/pytest.ini": "40b68664e0888847",
    "backend/requirements.txt": "5859bab9ce588dc2",
    "backend/scripts/banc_essai.py": "22eabe1195632fa2",
    "backend/scripts/controle_securite.py": "b6313f80617fc357",
    "backend/scripts/exemples_styles.py": "a520cb74508cee20",
    "backend/scripts/parcours_local.py": "d6d6f47ef24c16f2",
    "backend/scripts/test_scenes.py": "80a73dd938112afc",
    "backend/tests/conftest.py": "6de6df4fd91ffb4f",
    "backend/tests/test_admin.py": "a701f6739a4cb309",
    "backend/tests/test_avis.py": "67398104d98fb859",
    "backend/tests/test_flow.py": "a5accb358b22d558",
    "backend/tests/test_galerie.py": "ef624bed4b276ed0",
    "backend/tests/test_moderation.py": "5556dd794381a7c2",
    "backend/tests/test_moderation_liste.py": "59cc4311be2c28f2",
    "backend/tests/test_mot_de_passe.py": "8aafd7549608ee3c",
    "backend/tests/test_muse.py": "7df8f05535a59ccb",
    "backend/tests/test_parrainage.py": "63b36fb242697933",
    "backend/tests/test_partage.py": "2c9b6ee0f68ef571",
    "backend/tests/test_refus_dessin.py": "f0c5ae99abb5febf",
    "backend/tests/test_securite.py": "887617b59a7c7dfb",
    "backend/tests/test_trust.py": "a53f3912e2eb27dc",
    "backend/tests/test_verification.py": "0e87685ba619a752",
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
    "frontend/src/components/AuthForm.tsx": "f868948f66c65cbf",
    "frontend/src/components/DonnerAvis.tsx": "a6372f4814a54553",
    "frontend/src/components/Footer.tsx": "3329af3498a953dd",
    "frontend/src/components/MobileMoneyCheckout.tsx": "5af74d4f6acd171d",
    "frontend/src/components/PartagerChapitre.tsx": "a397b506fdf305a5",
    "frontend/src/components/PublierChapitre.tsx": "ea18b7801ec34d21",
    "frontend/src/components/StyleManga.tsx": "58bb53ecd3770fa9",
    "frontend/src/components/TopBar.tsx": "99ecc19566d55b5d",
    "frontend/src/components/accueil/Accueil.tsx": "1e83c84e0df14c22",
    "frontend/src/components/accueil/Planche.tsx": "a6d9eddf1f92e1ad",
    "frontend/src/components/admin.tsx": "4c7825363bb035f8",
    "frontend/src/components/galerie/BoutonJaime.tsx": "e1790a93f4689352",
    "frontend/src/components/galerie/CarteHistoire.tsx": "fb6c3d13ee8a1f96",
    "frontend/src/components/ink.tsx": "d70e26f1d2442949",
    "frontend/src/content/accueil.ts": "6c9c84bbbfeeec1d",
    "frontend/src/content/contact.ts": "14e3fcb8d77ebc1b",
    "frontend/src/content/faq.ts": "21749d4cb2ea4449",
    "frontend/src/content/publication.ts": "108bdf0ac2d0133e",
    "frontend/src/content/styles.ts": "a231758cb2495498",
    "frontend/src/lib/admin.ts": "ad12bfc27ace24a0",
    "frontend/src/lib/api.ts": "32cf59a969e45cda",
    "frontend/src/lib/contact.ts": "9135b49c2f1ce6fb",
    "frontend/src/lib/galerie.ts": "a48211fc5e61ef55",
    "frontend/src/lib/parrainage.ts": "6c26be2b2a5d4c15",
    "frontend/src/lib/session.ts": "199cef6538e618d9",
    "frontend/src/lib/utils.ts": "64fc84c1be627f0d",
    "frontend/src/main.tsx": "469efd888ad1637f",
    "frontend/src/routeTree.gen.ts": "a60cae687f1e7e93",
    "frontend/src/routes/__root.tsx": "19066aa3f6563359",
    "frontend/src/routes/abonnements.tsx": "3f80a4b8491f5ded",
    "frontend/src/routes/admin.tsx": "262d83ee38b49471",
    "frontend/src/routes/admin/avis.tsx": "cddf93935bbfd734",
    "frontend/src/routes/admin/episodes.$id.tsx": "fa93df9b44924eea",
    "frontend/src/routes/admin/episodes.index.tsx": "f5cac4217616e775",
    "frontend/src/routes/admin/index.tsx": "2c110281ee3cc7cf",
    "frontend/src/routes/admin/journal.tsx": "9d486ab68796c84d",
    "frontend/src/routes/admin/moderation.tsx": "01bc643be1eb02f0",
    "frontend/src/routes/admin/paiements.tsx": "9e816a1a84ca8c2a",
    "frontend/src/routes/admin/parrainages.tsx": "42bf37d458fbd6a4",
    "frontend/src/routes/admin/publications.tsx": "7dfb7795345f9c67",
    "frontend/src/routes/admin/utilisateurs.$id.tsx": "ee2295b69c012e7a",
    "frontend/src/routes/admin/utilisateurs.index.tsx": "d42c38121d60e9dd",
    "frontend/src/routes/connexion.tsx": "d223b750523970ca",
    "frontend/src/routes/contact.tsx": "831fac9ec305bac0",
    "frontend/src/routes/episodes.$id.tsx": "e3224e7fd14f3a71",
    "frontend/src/routes/faq.tsx": "063b93d02f463069",
    "frontend/src/routes/gagner.tsx": "a968e52e192db896",
    "frontend/src/routes/galerie.$id.tsx": "226fbb8fd9f78e01",
    "frontend/src/routes/galerie.index.tsx": "f0ed6e939335e24f",
    "frontend/src/routes/index.tsx": "2e8cb139f6f7c5d7",
    "frontend/src/routes/inscription.tsx": "2a5eda423e16bd39",
    "frontend/src/routes/mon-avis.tsx": "0a70a60ab91813f2",
    "frontend/src/routes/mot-de-passe-oublie.tsx": "72b39b1d0984e353",
    "frontend/src/routes/regles-publication.tsx": "f63a02db99108a82",
    "frontend/src/routes/series.$id.tsx": "2e5ea32b5dc6d5ec",
    "frontend/src/routes/soutenir.tsx": "2d069a68608a4228",
    "frontend/src/routes/styles.tsx": "0462fa227e28aac4",
    "frontend/src/routes/verifier.tsx": "2c5ee9f260acb138",
    "frontend/src/styles.css": "6b5e9e7a6b094abc",
    "frontend/tsconfig.json": "357e4358413314b2",
    "frontend/vite.config.ts": "3d1641fb1402b332",
    "ranger.bat": "646636fa55e62690",
    "ranger.py": "d34e6b6ecd2ffb09",
    "vps/deployer.sh": "db92768c60dbaeae",
    "vps/nginx-mangastudio.conf": "ed5ad50dc85dc4f5",
    "vps/sauvegarde.sh": "d0af29dacde2516e",
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
