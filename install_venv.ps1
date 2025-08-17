# Trade_Analysis - Venv Installation (PowerShell)
# Führen Sie dieses Skript in PowerShell aus

param(
    [switch]$Force
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Trade_Analysis - Venv Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Prüfen ob Python installiert ist
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python gefunden: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python ist nicht installiert oder nicht im PATH!" -ForegroundColor Red
    Write-Host "Bitte installieren Sie Python 3.8+ und versuchen Sie es erneut." -ForegroundColor Yellow
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

Write-Host ""

# Prüfen ob venv bereits existiert
if (Test-Path "venv") {
    if ($Force) {
        Write-Host "Lösche bestehende venv (Force-Modus aktiviert)..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force "venv"
    } else {
        Write-Host "WARNUNG: venv-Verzeichnis existiert bereits!" -ForegroundColor Yellow
        $choice = Read-Host "Möchten Sie es löschen und neu erstellen? (j/n)"
        if ($choice -eq "j" -or $choice -eq "J") {
            Write-Host "Lösche bestehende venv..." -ForegroundColor Yellow
            Remove-Item -Recurse -Force "venv"
        } else {
            Write-Host "Installation abgebrochen." -ForegroundColor Red
            Read-Host "Drücken Sie Enter zum Beenden"
            exit 0
        }
    }
}

# Virtuelle Umgebung erstellen
Write-Host "Erstelle virtuelle Umgebung..." -ForegroundColor Green
try {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        throw "Virtuelle Umgebung konnte nicht erstellt werden"
    }
} catch {
    Write-Host "ERROR: Konnte virtuelle Umgebung nicht erstellen!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

Write-Host ""

# Virtuelle Umgebung aktivieren
Write-Host "Aktiviere virtuelle Umgebung..." -ForegroundColor Green
try {
    & ".\venv\Scripts\Activate.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "Virtuelle Umgebung konnte nicht aktiviert werden"
    }
} catch {
    Write-Host "ERROR: Konnte virtuelle Umgebung nicht aktivieren!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

Write-Host ""

# pip aktualisieren
Write-Host "Aktualisiere pip..." -ForegroundColor Green
try {
    python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNUNG: pip konnte nicht aktualisiert werden!" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARNUNG: pip konnte nicht aktualisiert werden!" -ForegroundColor Yellow
}

Write-Host ""

# Basis-Abhängigkeiten installieren
Write-Host "Installiere Basis-Abhängigkeiten..." -ForegroundColor Green
try {
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNUNG: Einige Basis-Abhängigkeiten konnten nicht installiert werden!" -ForegroundColor Yellow
    } else {
        Write-Host "Basis-Abhängigkeiten erfolgreich installiert!" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNUNG: Einige Basis-Abhängigkeiten konnten nicht installiert werden!" -ForegroundColor Yellow
}

Write-Host ""

# Dashboard-Abhängigkeiten installieren
Write-Host "Installiere Dashboard-Abhängigkeiten..." -ForegroundColor Green
try {
    pip install -r requirements_dashboard.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNUNG: Einige Dashboard-Abhängigkeiten konnten nicht installiert werden!" -ForegroundColor Yellow
    } else {
        Write-Host "Dashboard-Abhängigkeiten erfolgreich installiert!" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNUNG: Einige Dashboard-Abhängigkeiten konnten nicht installiert werden!" -ForegroundColor Yellow
}

Write-Host ""

# Verzeichnisse erstellen
Write-Host "Erstelle Ausgabe- und Log-Verzeichnisse..." -ForegroundColor Green
if (-not (Test-Path "output")) { New-Item -ItemType Directory -Name "output" | Out-Null }
if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Name "logs" | Out-Null }

Write-Host ""

# Installation überprüfen
Write-Host "Überprüfe Installation..." -ForegroundColor Green
try {
    $testResult = python -c "import streamlit, pandas, plotly; print('Alle Pakete erfolgreich installiert!')" 2>&1
    Write-Host $testResult -ForegroundColor Green
} catch {
    Write-Host "WARNUNG: Einige Pakete sind möglicherweise nicht korrekt installiert!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Installation abgeschlossen!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Um die virtuelle Umgebung zu aktivieren:" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""

Write-Host "Um das Dashboard zu starten:" -ForegroundColor White
Write-Host "  streamlit run tradelog_dashboard.py" -ForegroundColor Cyan
Write-Host ""

Write-Host "Um den DataLoader zu testen:" -ForegroundColor White
Write-Host "  python example_tradelog_loader.py" -ForegroundColor Cyan
Write-Host ""

Write-Host "Installierte Pakete anzeigen:" -ForegroundColor White
Write-Host "  pip list" -ForegroundColor Cyan
Write-Host ""

Read-Host "Drücken Sie Enter zum Beenden"
