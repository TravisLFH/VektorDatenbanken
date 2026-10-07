# start.ps1
# Ein-Klick-Start fuer die Vector-DB-Demo (wie "npm start" bei Node-Projekten).
# Erledigt: Docker (Qdrant) starten, venv anlegen/aktivieren, Abhaengigkeiten
# installieren und die Streamlit-App starten.

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "==> Starte Qdrant via Docker Compose..." -ForegroundColor Cyan
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker wurde nicht gefunden. Installiere Docker Desktop und starte es zuerst."
}
docker compose up -d

Write-Host "==> Warte auf den Qdrant-Healthcheck..." -ForegroundColor Cyan
$Deadline = (Get-Date).AddSeconds(60)
do {
    try {
        $Health = Invoke-RestMethod -Uri "http://127.0.0.1:6333/healthz" -TimeoutSec 3
        if ($Health) { break }
    } catch {
        if ((Get-Date) -ge $Deadline) {
            throw "Qdrant wurde innerhalb von 60 Sekunden nicht gesund. Prüfe: docker compose logs qdrant"
        }
    }
    Start-Sleep -Seconds 2
} while ((Get-Date) -lt $Deadline)

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
# Hugging Face verwendet den lokalen Cache und darf fehlende Modelldateien laden.
$env:HF_HUB_OFFLINE = "0"
$env:TRANSFORMERS_OFFLINE = "0"
# Der Streamlit-Dateiwatcher laedt Aenderungen am Python-Code automatisch neu.
# .venv und qdrant_storage sind in .streamlit/config.toml davon ausgenommen.
streamlit run "$ProjectRoot\streamlit_app.py"
