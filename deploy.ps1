# MangaStudio : installe et lance le projet complet en local (Windows).
#
#   Double-clic sur deploy.bat, ou :
#   powershell -ExecutionPolicy Bypass -File deploy.ps1            installe puis lance l'API et le front
#   powershell -ExecutionPolicy Bypass -File deploy.ps1 -Tests     lance aussi les tests automatiques avant
#   powershell -ExecutionPolicy Bypass -File deploy.ps1 -SansFront n'installe et ne lance que l'API
#
# L'API tourne sur http://localhost:8000, le front sur http://localhost:5173.
# Chacun s'ouvre dans sa propre fenêtre : fermez la fenêtre pour l'arrêter.
param([switch]$Tests, [switch]$SansFront)
$ErrorActionPreference = "Stop"
$racine = $PSScriptRoot
$back = Join-Path $racine "backend"
$front = Join-Path $racine "frontend"

function Etape($texte) { Write-Host ""; Write-Host "== $texte" -ForegroundColor Cyan }
function Echec($texte) { Write-Host $texte -ForegroundColor Red; exit 1 }
function PortOccupe($port) { [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) }

# --- 1. Outils requis ---------------------------------------------------------
Etape "Vérification des outils"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { Echec "Python est introuvable. Installez Python 3.10 ou plus récent (python.org) en cochant 'Add python.exe to PATH'." }
if ((& python -c "import sys; print(sys.version_info >= (3, 10))") -ne "True") { Echec "Python 3.10 ou plus récent est requis." }
Write-Host ("Python : " + (& python --version))
if (-not $SansFront) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Echec "Node.js est introuvable. Installez Node.js 20 ou plus récent (nodejs.org), ou relancez avec -SansFront." }
    $node = (& node --version).TrimStart("v")
    if ([int]($node.Split(".")[0]) -lt 20) { Echec "Node.js 20 ou plus récent est requis (version trouvée : $node)." }
    Write-Host "Node.js : $node"
}

# --- 2. Backend ---------------------------------------------------------------
Etape "Backend : environnement Python et dépendances"
Set-Location $back
if (-not (Test-Path ".venv")) { & python -m venv .venv }
$py = Join-Path $back ".venv\Scripts\python.exe"
& $py -m pip install --quiet --upgrade pip
& $py -m pip install --quiet -r requirements.txt
if ($LASTEXITCODE -ne 0) { Echec "L'installation des dépendances Python a échoué (voir ci-dessus)." }
foreach ($dir in "app", "app\pipeline", "app\billing", "app\routers", "app\providers", "tests", "scripts") {
    $init = Join-Path $dir "__init__.py"
    if ((Test-Path $dir) -and -not (Test-Path $init)) { New-Item -ItemType File -Path $init | Out-Null }
}
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "backend\.env créé avec les modèles factices (aucune dépense). Mettez-y vos clés Muse et TrustChange." -ForegroundColor Yellow
} else { Write-Host "backend\.env existe déjà : conservé tel quel." }

if ($Tests) {
    Etape "Tests automatiques du backend"
    & $py -m pytest -q
    if ($LASTEXITCODE -ne 0) { Echec "Des tests échouent : rien n'a été lancé." }
}

# --- 3. Frontend --------------------------------------------------------------
if (-not $SansFront) {
    Etape "Frontend : dépendances"
    Set-Location $front
    if (-not (Test-Path ".env.local")) { Set-Content -Path ".env.local" -Value "VITE_API_URL=http://localhost:8000" -Encoding ascii }
    & npm install --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { Echec "npm install a échoué (voir ci-dessus)." }
}

# --- 4. Lancement -------------------------------------------------------------
Etape "Lancement"
if (PortOccupe 8000) { Echec "Le port 8000 est déjà utilisé : une API tourne sans doute encore. Fermez sa fenêtre puis relancez." }
Start-Process powershell -WorkingDirectory $back -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'MangaStudio - API'; & '$py' -m uvicorn app.main:app --reload --port 8000"

$pret = $false
foreach ($i in 1..40) {
    Start-Sleep -Milliseconds 750
    try { if ((Invoke-WebRequest "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { $pret = $true; break } } catch { }
}
if (-not $pret) { Echec "L'API n'a pas démarré : lisez le message d'erreur dans la fenêtre 'MangaStudio - API'." }
Write-Host "API prête : http://localhost:8000  (documentation : http://localhost:8000/docs)" -ForegroundColor Green

if (-not $SansFront) {
    if (PortOccupe 5173) { Echec "Le port 5173 est déjà utilisé : un front tourne sans doute encore. Fermez sa fenêtre puis relancez." }
    Start-Process powershell -WorkingDirectory $front -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'MangaStudio - Front'; npm run dev"
    Start-Sleep -Seconds 4
    Start-Process "http://localhost:5173"
    Write-Host "Front : http://localhost:5173" -ForegroundColor Green
}

Write-Host ""
Write-Host "Pour vérifier l'ensemble :   cd backend ; .venv\Scripts\python -m scripts.parcours_local"
Write-Host "Banc d'essai Muse :          cd backend ; .venv\Scripts\python -m scripts.banc_essai --pages 6 --persos 4"
Set-Location $racine
