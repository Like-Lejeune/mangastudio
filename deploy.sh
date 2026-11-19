#!/usr/bin/env bash
# MangaStudio : installe et lance le projet complet en local (Linux, macOS, Git Bash).
#   ./deploy.sh              installe puis lance l'API et le front (Ctrl+C arrête les deux)
#   ./deploy.sh --tests      lance aussi les tests automatiques avant
#   ./deploy.sh --sans-front n'installe et ne lance que l'API
set -euo pipefail
cd "$(dirname "$0")"
ROOT=$(pwd); TESTS=0; FRONT=1
for arg in "$@"; do case "$arg" in --tests) TESTS=1 ;; --sans-front) FRONT=0 ;; *) echo "Option inconnue : $arg"; exit 1 ;; esac; done
step() { printf '\n== %s\n' "$1"; }
PY=$(command -v python3 || command -v python) || { echo "Python 3.10 ou plus récent est requis."; exit 1; }
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || { echo "Python 3.10 ou plus récent est requis."; exit 1; }
[ "$FRONT" = 0 ] || command -v npm >/dev/null || { echo "Node.js 20 ou plus récent est requis (ou --sans-front)."; exit 1; }

step "Backend : environnement Python et dépendances"
cd "$ROOT/backend"
[ -d .venv ] || "$PY" -m venv .venv
VPY=.venv/bin/python; [ -x "$VPY" ] || VPY=.venv/Scripts/python.exe
"$VPY" -m pip install --quiet --upgrade pip
"$VPY" -m pip install --quiet -r requirements.txt
for d in app app/pipeline app/billing app/routers app/providers tests scripts; do [ -d "$d" ] && [ ! -f "$d/__init__.py" ] && : > "$d/__init__.py"; done || true
if [ ! -f .env ]; then cp .env.example .env; echo "backend/.env créé avec les modèles factices (aucune dépense)."; fi
if [ "$TESTS" = 1 ]; then step "Tests automatiques du backend"; "$VPY" -m pytest -q; fi

if [ "$FRONT" = 1 ]; then
  step "Frontend : dépendances"
  cd "$ROOT/frontend"
  [ -f .env.local ] || echo "VITE_API_URL=http://localhost:8000" > .env.local
  npm install --no-audit --no-fund
fi

step "Lancement"
mkdir -p "$ROOT/.logs"
cd "$ROOT/backend"; "$VPY" -m uvicorn app.main:app --reload --port 8000 > "$ROOT/.logs/api.log" 2>&1 & API=$!
trap 'kill $API ${WEB:-} 2>/dev/null || true' EXIT INT TERM
for _ in $(seq 1 40); do sleep 0.75; curl -fs http://localhost:8000/health >/dev/null 2>&1 && break; done
curl -fs http://localhost:8000/health >/dev/null || { echo "L'API n'a pas démarré : voir .logs/api.log"; exit 1; }
echo "API prête : http://localhost:8000  (documentation : /docs)"
if [ "$FRONT" = 1 ]; then cd "$ROOT/frontend"; npm run dev > "$ROOT/.logs/front.log" 2>&1 & WEB=$!; sleep 3; echo "Front : http://localhost:5173"; fi
echo "Journaux dans .logs/ — Ctrl+C pour tout arrêter."
wait
