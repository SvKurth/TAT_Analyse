# Fehlende Abhängigkeiten installieren
# Führen Sie dieses Skript in PowerShell aus

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Fehlende Abhängigkeiten installieren" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Prüfen ob venv aktiviert ist
if (-not $env:VIRTUAL_ENV) {
    Write-Host "WARNUNG: Virtuelle Umgebung ist nicht aktiviert!" -ForegroundColor Yellow
    Write-Host "Bitte aktivieren Sie zuerst die venv:" -ForegroundColor White
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

Write-Host "Virtuelle Umgebung ist aktiviert: $env:VIRTUAL_ENV" -ForegroundColor Green
Write-Host ""

Write-Host "Installiere fehlende Abhängigkeiten..." -ForegroundColor Green
Write-Host ""

# 1. Kritische Pakete
Write-Host "1. Kritische Pakete..." -ForegroundColor Yellow
try {
    pip install "yfinance>=0.2.0"
    Write-Host "   yfinance erfolgreich installiert" -ForegroundColor Green
} catch {
    Write-Host "   WARNUNG: yfinance konnte nicht installiert werden" -ForegroundColor Yellow
}

try {
    pip install "ta>=0.10.0"
    Write-Host "   ta erfolgreich installiert" -ForegroundColor Green
} catch {
    Write-Host "   WARNUNG: ta konnte nicht installiert werden" -ForegroundColor Yellow
}

try {
    pip install "streamlit>=1.28.0"
    Write-Host "   streamlit erfolgreich installiert" -ForegroundColor Green
} catch {
    Write-Host "   WARNUNG: streamlit konnte nicht installiert werden" -ForegroundColor Yellow
}

try {
    pip install "plotly>=5.17.0"
    Write-Host "   plotly erfolgreich installiert" -ForegroundColor Green
} catch {
    Write-Host "   WARNUNG: plotly konnte nicht installiert werden" -ForegroundColor Yellow
}

Write-Host ""

# 2. Zusätzliche Visualisierung
Write-Host "2. Zusätzliche Visualisierung..." -ForegroundColor Yellow
try {
    pip install "seaborn>=0.12.0"
    Write-Host "   seaborn erfolgreich installiert" -ForegroundColor Green
} catch {
    Write-Host "   WARNUNG: seaborn konnte nicht installiert werden" -ForegroundColor Yellow
}

try {
    pip install "matplotlib>=3.7.0"
    Write-Host "   matplotlib erfolgreich installiert" -ForegroundColor Green
} catch {
    Write-Host "   WARNUNG: matplotlib konnte nicht installiert werden" -ForegroundColor Yellow
}

Write-Host ""

# 3. Alle Requirements neu installieren
Write-Host "3. Alle Requirements neu installieren..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "   Basis-Requirements erfolgreich installiert" -ForegroundColor Green
} catch {
    Write-Host "   WARNUNG: Einige Basis-Requirements konnten nicht installiert werden" -ForegroundColor Yellow
}

try {
    pip install -r requirements_dashboard.txt
    Write-Host "   Dashboard-Requirements erfolgreich installiert" -ForegroundColor Green
} catch {
    Write-Host "   WARNUNG: Einige Dashboard-Requirements konnten nicht installiert werden" -ForegroundColor Yellow
}

Write-Host ""

# Installation testen
Write-Host "4. Teste Installation..." -ForegroundColor Yellow
try {
    $testResult = python -c "import yfinance, ta, streamlit, pandas, plotly; print('Alle kritischen Pakete erfolgreich installiert!')" 2>&1
    Write-Host $testResult -ForegroundColor Green
} catch {
    Write-Host "WARNUNG: Einige Pakete sind möglicherweise nicht korrekt installiert!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Installation abgeschlossen!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Testen Sie jetzt das Dashboard:" -ForegroundColor White
Write-Host "  streamlit run tradelog_dashboard.py" -ForegroundColor Cyan
Write-Host ""

Read-Host "Drücken Sie Enter zum Beenden"
