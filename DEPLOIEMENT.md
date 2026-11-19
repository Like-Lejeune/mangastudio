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

## 3. Premier déploiement sur le VPS

Avant : deux enregistrements DNS de type A, `app.votre-domaine.com` et `api.votre-domaine.com`, vers l'adresse IP du VPS.

```bash
ssh <utilisateur>@<ip-du-vps>
git clone <adresse de votre dépôt> mangastudio && cd mangastudio
bash vps/deployer.sh          # crée .env.production avec des secrets générés, puis s'arrête
nano .env.production          # domaines, ADMIN_EMAILS, META_API_KEY, clés TrustChange
bash vps/deployer.sh          # installe, construit, démarre, contrôle, vérifie le HTTPS
bash vps/sauvegarde.sh && bash vps/sauvegarde.sh --tester
```

`vps/deployer.sh` installe Docker s'il manque. Il s'arrête avec un message clair si une variable manque, si le DNS ne pointe pas vers le VPS, si les ports 80/443 sont pris ou si un secret est suivi par git. Ensuite, il construit et démarre tout, passe la liste de contrôle de sécurité, attend que `/health` réponde en HTTPS et programme une sauvegarde chaque nuit à 3 h.

Puis créez votre compte sur `https://app.votre-domaine.com/inscription` avec une adresse de `ADMIN_EMAILS` : le lien **Administration** apparaît.

## 4. Déployer une nouvelle version

```bash
cd ~/mangastudio && git pull && bash vps/deployer.sh
```

Le script sauvegarde la base avant de reconstruire. Il crée aussi le lien `.env → .env.production` : toutes les commandes `docker compose …` ci-dessous marchent sans `--env-file`. Les migrations s'appliquent au démarrage de l'API.

## 5. Utile

| Besoin | Commande |
| --- | --- |
| Journaux | `docker compose logs -f api worker` |
| Sauvegarde (base + images) | `bash vps/sauvegarde.sh` (aussi chaque nuit à 3 h, 14 jours gardés) |
| Vérifier qu'une sauvegarde se restaure | `bash vps/sauvegarde.sh --tester` |
| Remettre la base dans un état passé | `bash vps/sauvegarde.sh --restaurer sauvegardes/base-….dump` |
| Copier les sauvegardes sur votre PC | `scp -r <utilisateur>@<ip>:mangastudio/sauvegardes .` |
| Banc d'essai sur le VPS | `docker compose exec api python -m scripts.banc_essai --pages 6 --persos 4` |
| Tout arrêter | `docker compose down` (les données restent dans les volumes) |

## Sécurité et plafond de dépense

L'API refuse de démarrer en production si la configuration est dangereuse : `SECRET_KEY` absente ou d'exemple, adresses en http, base SQLite, fournisseur IA resté sur « fake », clé Muse vide, webhook TrustChange sans secret. Le message d'erreur s'affiche dans `docker compose logs api`.

Liste de contrôle complète (secrets hors de git, configuration, en-têtes HTTPS) :

```bash
docker compose run --rm -v "$PWD:/repo:ro" api python -m scripts.controle_securite --racine /repo --env /repo/.env.production
```

Ce qui est en place :

- **Connexion** : 5 essais ratés pour un même compte depuis une même adresse, puis 15 minutes d'attente ; 30 essais ratés depuis une adresse, tous comptes confondus. Inscriptions : 10 par heure et par adresse.
- **Photos** : 3 Mo au plus, et le fichier doit vraiment être un JPEG, un PNG ou un WebP.
- **CORS** : en production, seules les adresses de `FRONTEND_URL` peuvent appeler l'API. La documentation `/docs` n'est pas publiée.
- **Caddy** : HTTPS imposé (HSTS), politique de contenu stricte pour le site, pas d'affichage dans un cadre, envois limités à 8 Mo. L'API n'est joignable qu'à travers Caddy.
- **Plafond IA** : `AI_DAILY_BUDGET_USD` (dollars par jour, calculé avec `PRICES`). Une alerte part à 80 %, puis une autre à 100 %. Elles sont notées dans *Administration › Journal* et envoyées à `ALERT_WEBHOOK_URL` si elle est réglée (Slack, Discord, Google Chat). Au-delà du plafond, les nouveaux épisodes, reprises et redessins sont refusés jusqu'au lendemain, sans débiter de crédit. Les épisodes déjà lancés se terminent. La jauge du jour est en haut de l'administration.

Pour tester le classeur de scènes interdites avec le vrai modèle (20 cas interdits, 6 cas permis, quelques centimes) :

```bash
docker compose exec api python -m scripts.test_scenes
```

## Ports 80 et 443 déjà utilisés par un autre serveur web

`vps/deployer.sh` s'adapte à ce qu'il trouve sur le VPS :

| Sur le VPS | Ce que fait le script |
|---|---|
| 80 et 443 libres | Caddy tient les deux ports et fait le HTTPS lui-même. |
| 80 pris, 443 libre | Caddy garde le 443 et valide ses certificats par là. Il faut une redirection http → https côté serveur existant (voir ci-dessous). |
| 80 et 443 pris par nginx | Caddy écoute **en local seulement**, sur le premier port libre à partir de 127.0.0.1:8081. Le script ajoute ensuite à nginx un site pour les deux sous-domaines (`vps/nginx-mangastudio.conf` → `/etc/nginx/sites-available/mangastudio`), vérifie la configuration (`nginx -t`), recharge nginx, puis obtient les certificats avec certbot, redirection http → https comprise. Les autres sites de nginx ne sont pas touchés. Si `nginx -t` échoue, le fichier ajouté est retiré aussitôt. |

Dans le troisième cas, les adresses restent `https://mangastudio.psikalab.space` et `https://apimangastudio.psikalab.space`, sans numéro de port. Le choix est noté dans `.env.production` (`CADDY_CONFIG`, `CADDY_HTTP_PORT`, `CADDY_HTTPS_PORT`) et réutilisé aux déploiements suivants.

Redirection http → https dans le deuxième cas, avec nginx :

```bash
sudo tee /etc/nginx/sites-available/mangastudio-redirection >/dev/null <<'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name mangastudio.psikalab.space apimangastudio.psikalab.space;
    return 301 https://$host$request_uri;
}
NGINX
sudo ln -sf /etc/nginx/sites-available/mangastudio-redirection /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Modifier la base de données

La structure de la base est gérée par des migrations (Alembic), appliquées toutes seules à chaque démarrage de l'API. Après une modification de `backend/app/models.py`, sur votre poste :

```bash
cd backend
.venv\Scripts\alembic revision --autogenerate -m "ce qui change"
```

Relisez le fichier créé dans `backend/migrations/versions/`, validez-le dans git avec le reste, puis déployez : la base du VPS se met à niveau au redémarrage, sans perdre de données. Faites une sauvegarde avant tout déploiement qui contient une migration.

## Limites connues de cette version

- Les images sont sur le disque du VPS (volume `storage`), servies par l'API. À passer sur un stockage S3 quand le volume grandit ; d'ici là, sauvegarder aussi ce volume.
- L'URL du webhook TrustChange est `https://api.votre-domaine.com/billing/webhooks/trust` : elle est envoyée à chaque demande de paiement, rien à déclarer chez TrustChange sauf s'ils l'exigent.
