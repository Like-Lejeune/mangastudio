# Tester MangaStudio en local (Windows)

Il faut Python 3.10 ou plus récent et Node.js 20 ou plus récent. Rien d'autre : la base est un fichier SQLite et la génération tourne dans l'API. Pas de Docker, pas de PostgreSQL, pas de Redis.

## 1. Vérifier que les fichiers sont à jour

```powershell
cd mangastudio
python verifier_fichiers.py
```

Le script liste les fichiers manquants, périmés ou à supprimer. Tant qu'il en reste, remplacez-les par la dernière version reçue.

## 2. Tout lancer

Double-cliquez sur `deploy.bat`, ou dans PowerShell :

```powershell
.\deploy.bat            # installe puis lance l'API et le front
.\deploy.bat -Tests     # lance aussi les 15 tests automatiques avant
.\deploy.bat -SansFront # l'API seule
```

Le script installe les dépendances Python et Node, crée `backend\.env` (modèles factices : aucune dépense) et `frontend\.env.local`, puis ouvre deux fenêtres : « MangaStudio - API » (http://localhost:8000) et « MangaStudio - Front » (http://localhost:5173). Le navigateur s'ouvre sur le front. Pour arrêter, fermez les deux fenêtres. Un `.env` existant n'est jamais écrasé.

## 3. Vérifier l'ensemble automatiquement

L'API restant lancée, dans un autre terminal :

```powershell
cd mangastudio\backend
.venv\Scripts\python -m scripts.parcours_local
```

Dix-sept vérifications : inscription, limites du plan gratuit, épisode de 4 pages, compteur de tokens, crédits. Tout doit afficher `[OK]`. Avec les modèles factices, les « pages » sont des images de remplacement.

## 4. Banc d'essai Muse (vrais modèles)

Dans `backend\.env`, supprimez le bloc « Développement sans dépense », décommentez le bloc Muse et renseignez `META_API_KEY`. Puis :

```powershell
cd mangastudio\backend
.venv\Scripts\python -m scripts.banc_essai --pages 6 --persos 4
```

Le banc d'essai n'a pas besoin que l'API soit lancée. Il affiche le coût par étape et par crédit ; les images sont dans `backend\storage\series\<id>\`. C'est le moment de juger la cohérence des visages et le lettrage en français. Cet épisode est réellement facturé par Meta.

Pour utiliser ensuite les vrais modèles depuis le front, fermez la fenêtre de l'API et relancez `deploy.bat` : l'API relit le `.env`.

## 5. Parcours à faire à la main dans le front

Inscription, nouvelle série, deux ou trois personnages (dont un avec photo), épisode de 4 pages, lecture en plein écran, écran Abonnements.

## 6. Paiement TrustChange

Ajoutez dans `backend\.env` une clé de test `TRUSTCHANGE_API_KEY=tc_test_...` et `TRUSTCHANGE_WEBHOOK_SECRET`, puis relancez. En local, TrustChange ne peut pas joindre votre machine : la notification n'arrive pas, mais le front interroge l'état du paiement et le plan s'active quand même. La notification elle-même se testera sur le VPS.

## 7. Modération

Mettez votre adresse dans `ADMIN_EMAILS` du fichier `backend\.env`, relancez, puis connectez-vous : le lien **Administration** apparaît. Une liste de départ (65 mots, 6 scènes interdites) est déjà chargée. *Administration › Modération* permet d'ajouter un mot : une série ou un épisode qui le contient est refusé.

Les 20 cas interdits du planning se vérifient avec `.venv\Scripts\python -m pytest tests\test_moderation_liste.py`. Le classeur de scènes avec Muse se vérifie avec `.venv\Scripts\python -m scripts.test_scenes` (clés Muse dans le `.env`).

## Repartir de zéro

Fermez les deux fenêtres, supprimez `backend\dev.db` et le dossier `backend\storage`, relancez. Ce n'est plus nécessaire après une mise à jour : la base se met à niveau toute seule au démarrage, en gardant vos données.

## En cas de problème

| Symptôme | Cause probable |
| --- | --- |
| « Le port 8000 est déjà utilisé » | Une fenêtre « MangaStudio - API » est encore ouverte : fermez-la |
| `no such table` ou `no such column` | Une migration manque : relancez `deploy.bat` ; en dernier recours, supprimez `backend\dev.db` |
| Le front affiche « Le studio est injoignable » | L'API n'est pas lancée |
| Épisode « Interrompu » avec les vrais modèles | L'erreur de Meta est écrite dans la fenêtre de l'API. Envoyez-la-moi |
| `npm install` échoue | Vérifiez la connexion, puis relancez `deploy.bat` : il reprend où il s'est arrêté |
