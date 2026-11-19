# MangaStudio — backend (FastAPI)

Squelette de l'API : comptes, séries, personnages, épisodes à pages variables,
modération, compteur de tokens par épisode, crédits, abonnements (Stripe, mobile money).

## Démarrer

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # par défaut : SQLite + fournisseurs factices, aucune dépense
uvicorn app.main:app --reload # http://localhost:8000/docs
pytest -q
```

Le premier compte créé est administrateur.

## Où est quoi

| Fichier | Rôle |
| --- | --- |
| `app/plans.py` | Plans : crédits, personnages et pages max, prix |
| `app/pipeline/runner.py` | Génération d'un épisode, reprise, redessin |
| `app/pipeline/script.py` | Schéma JSON du scénario et normalisation |
| `app/pipeline/prompts.py` | Consignes de chaque étape |
| `app/moderation.py` | Mots bloqués, scènes interdites, journal |
| `app/usage.py` | Journal d'usage (tokens, images) et crédits |
| `app/providers/` | Fournisseurs IA interchangeables (`fake`, `openai_compat`) |
| `migrations/` | Migrations de la base (Alembic), appliquées au démarrage |
| `app/billing/` | Paiements : TrustChange (mobile money, `trust.py` + `trustchange_client.py`), Stripe |
| `app/routers/` | Routes HTTP |

## Brancher de vrais modèles

Dans `.env` : `WRITER_PROVIDER=openai_compat`, `WRITER_MODEL=...` (idem `CHECKER_*`, `IMAGE_*`),
`OPENAI_COMPAT_BASE_URL`, `OPENAI_COMPAT_API_KEY`, et les prix dans `PRICES`.
Pour un fournisseur au format différent : une classe dans `app/providers/` qui respecte
`TextProvider` ou `ImageProvider`, et une ligne dans `app/providers/__init__.py`.

## Avant la production

- `REDIS_URL` + `arq app.worker.WorkerSettings` pour les tâches de fond.
- Stockage S3/R2 à la place du disque (`app/storage.py`).
- TrustChange : confirmer les noms d'en-têtes du webhook et les libellés de statut (variables `TRUSTCHANGE_*` du `.env`).
- Limitation de débit sur `/auth/*`, vérification d'e-mail, réinitialisation de mot de passe.
