# start.ps1
# Ein-Klick-Start fuer die Vector-DB-Demo (wie "npm start" bei Node-Projekten).
# Erledigt: Docker (Qdrant) starten, venv anlegen/aktivieren, Abhaengigkeiten
# installieren und die Streamlit-App starten.

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "==> Starte Qdrant via Docker Compose..." -ForegroundColor Cyan
docker compose up -d

$VenvPath = Join-Path $ProjectRoot ".venv"
$VenvActivate = Join-Path $VenvPath "Scripts\Activate.ps1"
$MarkerFile = Join-Path $VenvPath "requirements.installed"

if (-not (Test-Path $VenvPath)) {
    Write-Host "==> Kein virtuelles Environment gefunden, erstelle .venv..." -ForegroundColor Cyan
    python -m venv $VenvPath
}

Write-Host "==> Aktiviere virtuelles Environment..." -ForegroundColor Cyan
& $VenvActivate

# Abhaengigkeiten nur neu installieren, wenn requirements.txt sich geaendert hat.
$RequirementsHash = (Get-FileHash "$ProjectRoot\requirements.txt").Hash
$InstalledHash = if (Test-Path $MarkerFile) { Get-Content $MarkerFile } else { "" }

if ($RequirementsHash -ne $InstalledHash) {
    Write-Host "==> Installiere/aktualisiere Python-Abhaengigkeiten..." -ForegroundColor Cyan
    pip install -r "$ProjectRoot\requirements.txt"
    Set-Content -Path $MarkerFile -Value $RequirementsHash
} else {
    Write-Host "==> Abhaengigkeiten sind bereits aktuell, ueberspringe Installation." -ForegroundColor DarkGray
}

Write-Host "==> Starte Streamlit-App..." -ForegroundColor Cyan
streamlit run "$ProjectRoot\streamlit_app.py" --server.fileWatcherType poll
