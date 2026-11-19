# Du poste local au VPS

## 1. Tester en local

Voir `TEST_LOCAL.md` : un double-clic sur `deploy.bat` installe et lance l'API et le front.

## 2. Mettre sous git

```bash
cd mangastudio
git init && git add . && git status
```

Avant le premier commit, vérifier dans `git status` qu'aucun `.env`, `dev.db` ni dossier `storage/` n'apparaît : le `.gitignore` les écarte. Une clé poussée par erreur doit être révoquée, pas seulement retirée du dépôt.

```bash
git commit -m "MangaStudio : backend, front, paiement TrustChange, modèles Muse"
git remote add origin <adresse de votre dépôt privé>
git push -u origin main
```

## 3. Préparer le VPS (une seule fois)

- DNS : deux enregistrements A, `app.votre-domaine.com` et `api.votre-domaine.com`, vers l'adresse IP du VPS.
- Pare-feu : ports 22, 80 et 443 ouverts ; rien d'autre.
- Docker :

```bash
curl -fsSL https://get.docker.com | sh
git clone <adresse de votre dépôt> mangastudio && cd mangastudio
cp .env.production.example .env.production && nano .env.production
chmod 600 .env.production
docker compose --env-file .env.production up -d --build
```

Vérifier : `curl https://api.votre-domaine.com/health` répond `{"ok":true}` et `https://app.votre-domaine.com` affiche l'accueil. Les certificats HTTPS sont obtenus tout seuls au premier démarrage, une fois le DNS en place.

Le front est construit dans l'image avec l'adresse de l'API (`API_DOMAIN`) : si elle change, relancez avec `--build`.

Créer tout de suite votre compte sur `/docs` (`POST /auth/register`) : le premier compte créé est administrateur.

## 4. Déployer une nouvelle version

```bash
ssh <vps>
cd mangastudio && git pull
docker compose --env-file .env.production up -d --build
docker compose logs -f api worker        # Ctrl+C pour quitter
```

## 5. Utile

| Besoin | Commande |
| --- | --- |
| Journaux | `docker compose logs -f api worker` |
| Sauvegarde de la base | `docker compose exec db pg_dump -U manga manga > sauvegarde-$(date +%F).sql` |
| Restauration | `docker compose exec -T db psql -U manga manga < sauvegarde.sql` |
| Banc d'essai sur le VPS | `docker compose exec api python -m scripts.banc_essai --pages 6 --persos 4` |
| Tout arrêter | `docker compose down` (les données restent dans les volumes) |

## Limites connues de cette version

- Les tables sont créées au démarrage de l'API. Tant qu'il n'y a pas de migrations Alembic, une colonne ajoutée à une table existante ne s'applique pas toute seule à la base de production.
- Les images sont sur le disque du VPS (volume `storage`), servies par l'API. À passer sur un stockage S3 quand le volume grandit ; d'ici là, sauvegarder aussi ce volume.
- L'URL du webhook TrustChange est `https://api.votre-domaine.com/billing/webhooks/trust` : elle est envoyée à chaque demande de paiement, rien à déclarer chez TrustChange sauf s'ils l'exigent.
