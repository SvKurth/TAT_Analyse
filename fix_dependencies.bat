@echo off
echo ========================================
echo    Fehlende Abhängigkeiten installieren
echo ========================================
echo.

REM Prüfen ob venv aktiviert ist
if not defined VIRTUAL_ENV (
    echo WARNUNG: Virtuelle Umgebung ist nicht aktiviert!
    echo Bitte aktivieren Sie zuerst die venv:
    echo   .\venv\Scripts\Activate.ps1
    echo.
    pause
    exit /b 1
)

echo Virtuelle Umgebung ist aktiviert: %VIRTUAL_ENV%
echo.

echo Installiere fehlende Abhängigkeiten...
echo.

echo 1. Kritische Pakete...
pip install yfinance>=0.2.0
pip install ta>=0.10.0
pip install streamlit>=1.28.0
pip install plotly>=5.17.0

echo.
echo 2. Zusätzliche Visualisierung...
pip install seaborn>=0.12.0
pip install matplotlib>=3.7.0

echo.
echo 3. Alle Requirements neu installieren...
pip install -r requirements.txt
pip install -r requirements_dashboard.txt

echo.
echo ========================================
echo    Installation abgeschlossen!
echo ========================================
echo.
echo Testen Sie jetzt das Dashboard:
echo   streamlit run tradelog_dashboard.py
echo.
pause
