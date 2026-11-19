#!/usr/bin/env bash
# Déploie MangaStudio sur le VPS : première installation ou mise à jour.
#
#   cd ~/mangastudio && bash vps/deployer.sh
#
# Étapes : Docker présent → .env.production complet → DNS → ports → secrets hors de git
# → sauvegarde avant mise à jour → construction et démarrage → contrôle de sécurité
# → /health en HTTPS → sauvegarde quotidienne programmée.
set -euo pipefail
cd "$(dirname "$0")/.."
RACINE="$PWD"
ENV_FILE=.env.production
COMPOSE=(docker compose --env-file "$ENV_FILE")

ok()   { printf '  \033[32m✔\033[0m %s\n' "$*"; }
info() { printf '\n\033[1m%s\033[0m\n' "$*"; }
stop() { printf '\n  \033[31m✘ %s\033[0m\n\n' "$*"; exit 1; }
val()  { grep -E "^$1=" "$ENV_FILE" | tail -1 | cut -d= -f2- | sed 's/[[:space:]]*#.*$//; s/^["'\'']//; s/["'\'']$//'; }

info "1. Docker"
if ! command -v docker >/dev/null 2>&1; then
  echo "  Docker absent : installation (mot de passe sudo demandé)…"
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
  echo "  Docker installé. Si la suite échoue sur « permission denied », déconnectez-vous puis relancez ce script."
fi
docker compose version >/dev/null 2>&1 || stop "« docker compose » introuvable : installez le plugin compose (sudo apt install docker-compose-plugin)."
ok "$(docker --version)"

info "2. Fichier $ENV_FILE"
if [[ ! -f $ENV_FILE ]]; then
  cp .env.production.example "$ENV_FILE"
  sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|; s|^SECRET_KEY=.*|SECRET_KEY=$(openssl rand -hex 32)|" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  stop "$ENV_FILE créé avec un mot de passe de base et une clé de signature générés. Complétez-le (nano $ENV_FILE) : domaines, ADMIN_EMAILS, META_API_KEY, clés TrustChange. Puis relancez ce script."
fi
chmod 600 "$ENV_FILE"
# Lien .env → .env.production : « docker compose … » marche ensuite sans --env-file.
[[ -L .env || ! -e .env ]] && ln -sfn "$ENV_FILE" .env
manque=()
for v in APP_DOMAIN API_DOMAIN PUBLIC_BASE_URL FRONTEND_URL POSTGRES_PASSWORD SECRET_KEY ADMIN_EMAILS META_API_KEY; do
  [[ -n "$(val "$v")" ]] || manque+=("$v")
done
[[ ${#manque[@]} -eq 0 ]] || stop "À remplir dans $ENV_FILE : ${manque[*]}"
APP_DOMAIN=$(val APP_DOMAIN); API_DOMAIN=$(val API_DOMAIN)
[[ $APP_DOMAIN != *votre-domaine* ]] || stop "APP_DOMAIN contient encore l'exemple « votre-domaine »."
[[ "$(val PUBLIC_BASE_URL)" == "https://$API_DOMAIN" ]] || stop "PUBLIC_BASE_URL doit valoir https://$API_DOMAIN"
[[ ",$(val FRONTEND_URL)," == *",https://$APP_DOMAIN,"* ]] || stop "FRONTEND_URL doit contenir https://$APP_DOMAIN"
if [[ -n "$(val TRUSTCHANGE_API_KEY)" && -z "$(val TRUSTCHANGE_WEBHOOK_SECRET)" ]]; then
  stop "TRUSTCHANGE_WEBHOOK_SECRET est vide : l'API refuserait de démarrer."
fi
[[ "$(val TRUSTCHANGE_API_KEY)" == tc_test_* ]] && echo "  (TrustChange en mode test : aucun argent réel encaissé)"
ok "variables obligatoires présentes, fichier lisible par vous seul"

info "3. DNS"
IP=$(curl -fsS --max-time 10 https://api.ipify.org 2>/dev/null || true)
[[ -n $IP ]] || IP=$(hostname -I 2>/dev/null | awk '{print $1}' || true)
[[ -n $IP ]] || stop "Impossible de connaître l'adresse IP publique du VPS."
for d in "$APP_DOMAIN" "$API_DOMAIN"; do
  r=$(getent ahostsv4 "$d" 2>/dev/null | awk 'NR==1{print $1}' || true)
  [[ -n $r ]] || stop "$d ne résout vers aucune adresse : créez un enregistrement A vers $IP chez votre registraire."
  [[ $r == "$IP" ]] || stop "$d pointe vers $r au lieu de $IP (ce VPS). Corrigez l'enregistrement A, attendez la propagation, relancez."
  ok "$d → $IP"
done

info "4. Ports 80 et 443"
for p in 80 443; do
  if ss -ltnp 2>/dev/null | grep -q ":$p " && ! "${COMPOSE[@]}" ps caddy 2>/dev/null | grep -q -E "Up|running"; then
    ss -ltnp | grep ":$p " || true
    stop "Le port $p est déjà pris par un autre programme (nginx, apache ?). Arrêtez-le : sudo systemctl disable --now nginx apache2"
  fi
done
if command -v ufw >/dev/null 2>&1 && sudo -n ufw status 2>/dev/null | grep -q "Status: active"; then
  sudo ufw allow 80/tcp >/dev/null; sudo ufw allow 443/tcp >/dev/null
fi
ok "ports libres ou déjà tenus par Caddy"

info "5. Secrets hors de git"
if git rev-parse --git-dir >/dev/null 2>&1; then
  suivis=$(git ls-files | grep -E '(^|/)\.env(\.production)?$|\.db$|(^|/)sauvegardes/' || true)
  [[ -z $suivis ]] || stop "Fichiers secrets suivis par git : $suivis — retirez-les : git rm --cached <fichier>"
  ok "aucun .env, base ni sauvegarde dans git ($(git log -1 --format='%h %s'))"
fi

info "6. Sauvegarde avant mise à jour"
if "${COMPOSE[@]}" ps db 2>/dev/null | grep -q -E "Up|running"; then
  bash vps/sauvegarde.sh
else
  echo "  première installation : rien à sauvegarder"
fi

info "7. Construction et démarrage (quelques minutes la première fois)"
"${COMPOSE[@]}" up -d --build --remove-orphans
ok "conteneurs lancés"

info "8. Contrôle de sécurité"
"${COMPOSE[@]}" run --rm --no-deps -v "$RACINE:/repo:ro" api \
  python -m scripts.controle_securite --racine /repo --env /repo/"$ENV_FILE" \
  || stop "Le contrôle de sécurité a trouvé un point à corriger (voir ci-dessus)."

info "9. Réponse en HTTPS (certificats obtenus au premier démarrage)"
for i in $(seq 1 60); do
  if curl -fsS --max-time 5 "https://$API_DOMAIN/health" >/dev/null 2>&1; then break; fi
  [[ $i -eq 60 ]] && { "${COMPOSE[@]}" logs --tail 40 api caddy; stop "https://$API_DOMAIN/health ne répond pas après 3 minutes (journaux ci-dessus)."; }
  sleep 3
done
ok "https://$API_DOMAIN/health → $(curl -fsS "https://$API_DOMAIN/health")"
code=$(curl -s -o /dev/null -w '%{http_code}' "https://$APP_DOMAIN/")
[[ $code == 200 ]] || stop "https://$APP_DOMAIN répond $code"
ok "https://$APP_DOMAIN → 200"
"${COMPOSE[@]}" ps --format 'table {{.Service}}\t{{.Status}}'

info "10. Sauvegarde quotidienne (3 h du matin)"
ligne="0 3 * * * cd $RACINE && bash vps/sauvegarde.sh >> $RACINE/sauvegardes/journal.log 2>&1"
if crontab -l 2>/dev/null | grep -qF "vps/sauvegarde.sh"; then
  ok "déjà programmée"
else
  (crontab -l 2>/dev/null; echo "$ligne") | crontab -
  ok "programmée (crontab -l pour la voir)"
fi

printf '\n\033[32mMangaStudio est en ligne : https://%s\033[0m\n' "$APP_DOMAIN"
printf 'Journaux : docker compose logs -f api worker   ·   Test de restauration : bash vps/sauvegarde.sh --tester\n\n'