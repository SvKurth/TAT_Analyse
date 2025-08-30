@echo off
echo ========================================
echo    TAT Analyse Tool - Flask Fork
echo ========================================
echo.

REM Prüfen ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python ist nicht installiert oder nicht im PATH!
    echo Bitte installieren Sie Python 3.8+ und versuchen Sie es erneut.
    pause
    exit /b 1
)

echo Python gefunden: 
python --version
echo.

REM Prüfen ob virtuelle Umgebung existiert
if not exist "venv_flask" (
    echo Virtuelle Umgebung wird erstellt...
    python -m venv venv_flask
    if errorlevel 1 (
        echo ERROR: Konnte virtuelle Umgebung nicht erstellen!
        pause
        exit /b 1
    )
    echo Virtuelle Umgebung erstellt!
    echo.
)

REM Virtuelle Umgebung aktivieren
echo Aktiviere virtuelle Umgebung...
call venv_flask\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Konnte virtuelle Umgebung nicht aktivieren!
    pause
    exit /b 1
)

REM Prüfen ob Requirements installiert sind
echo Prüfe Abhängigkeiten...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installiere Abhängigkeiten...
    pip install -r requirements_flask.txt
    if errorlevel 1 (
        echo ERROR: Konnte Abhängigkeiten nicht installieren!
        pause
        exit /b 1
    )
    echo Abhängigkeiten installiert!
    echo.
)

REM Anwendung starten
echo.
echo ========================================
echo    Starte Flask-Anwendung...
echo ========================================
echo.
echo Die Anwendung wird unter http://localhost:5000 gestartet
echo Drücken Sie STRG+C zum Beenden
echo.

python app_flask.py

REM Bei Fehler pausieren
if errorlevel 1 (
    echo.
    echo ERROR: Die Anwendung konnte nicht gestartet werden!
    pause
)

REM Virtuelle Umgebung deaktivieren
deactivate
