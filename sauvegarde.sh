#!/usr/bin/env bash
# Sauvegarde la base PostgreSQL et les images générées dans ~/mangastudio/sauvegardes (14 jours gardés).
#
#   bash vps/sauvegarde.sh            sauvegarde maintenant
#   bash vps/sauvegarde.sh --tester   restaure la dernière sauvegarde dans une base temporaire et la vérifie
#   bash vps/sauvegarde.sh --restaurer sauvegardes/base-AAAA-MM-JJ_HHMM.dump
#                                     remet la base dans l'état de ce fichier (après confirmation)
#
# Copiez régulièrement le dossier sauvegardes/ hors du VPS (scp ou rclone) : une sauvegarde
# qui vit sur la même machine disparaît avec elle.
set -euo pipefail
cd "$(dirname "$0")/.."
COMPOSE=(docker compose --env-file .env.production)
DIR=sauvegardes
mkdir -p "$DIR"
chmod 700 "$DIR"
D=$(date +%F_%H%M)

if [[ ${1:-} == --tester ]]; then
  f=$(ls -1t "$DIR"/base-*.dump 2>/dev/null | head -1) || true
  [[ -n ${f:-} ]] || { echo "Aucune sauvegarde : lancez d'abord bash vps/sauvegarde.sh"; exit 1; }
  echo "Restauration de $f dans une base temporaire…"
  "${COMPOSE[@]}" exec -T db psql -U manga -d postgres -qc "DROP DATABASE IF EXISTS restauration_test" -c "CREATE DATABASE restauration_test"
  "${COMPOSE[@]}" exec -T db pg_restore -U manga -d restauration_test --no-owner < "$f"
  "${COMPOSE[@]}" exec -T db psql -U manga -d restauration_test -c \
    "SELECT (SELECT version_num FROM alembic_version) AS migration, (SELECT count(*) FROM users) AS comptes, (SELECT count(*) FROM episodes) AS episodes, (SELECT count(*) FROM payments) AS paiements"
  "${COMPOSE[@]}" exec -T db psql -U manga -d postgres -qc "DROP DATABASE restauration_test"
  echo "Restauration réussie : la sauvegarde est utilisable (base temporaire supprimée)."
  exit 0
fi

if [[ ${1:-} == --restaurer ]]; then
  f=${2:?indiquez le fichier .dump}
  read -r -p "La base actuelle sera REMPLACÉE par $f. Taper OUI pour continuer : " r
  [[ $r == OUI ]] || exit 1
  bash "$0"   # filet de sécurité : sauvegarde de l'état actuel d'abord
  "${COMPOSE[@]}" stop api worker
  "${COMPOSE[@]}" exec -T db pg_restore -U manga -d manga --clean --if-exists --no-owner < "$f"
  "${COMPOSE[@]}" start api worker
  echo "Base restaurée depuis $f."
  exit 0
fi

"${COMPOSE[@]}" exec -T db pg_dump -U manga -Fc manga > "$DIR/base-$D.dump"
"${COMPOSE[@]}" run --rm --no-deps -T -v "$PWD/$DIR:/sauvegarde" api tar czf "/sauvegarde/images-$D.tgz" -C /data storage
find "$DIR" -name 'base-*.dump' -mtime +14 -delete
find "$DIR" -name 'images-*.tgz' -mtime +14 -delete
echo "$(date '+%F %T') sauvegarde : $DIR/base-$D.dump ($(du -h "$DIR/base-$D.dump" | cut -f1)), $DIR/images-$D.tgz ($(du -h "$DIR/images-$D.tgz" | cut -f1))"
