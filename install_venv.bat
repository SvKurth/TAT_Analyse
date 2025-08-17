@echo off
echo ========================================
echo    Trade_Analysis - Venv Installation
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

REM Prüfen ob venv bereits existiert
if exist "venv" (
    echo WARNUNG: venv-Verzeichnis existiert bereits!
    echo.
    set /p choice="Möchten Sie es löschen und neu erstellen? (j/n): "
    if /i "%choice%"=="j" (
        echo Lösche bestehende venv...
        rmdir /s /q venv
        echo.
    ) else (
        echo Installation abgebrochen.
        pause
        exit /b 0
    )
)

echo Erstelle virtuelle Umgebung...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Konnte virtuelle Umgebung nicht erstellen!
    pause
    exit /b 1
)

echo.
echo Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Konnte virtuelle Umgebung nicht aktivieren!
    pause
    exit /b 1
)

echo.
echo Aktualisiere pip...
python -m pip install --upgrade pip

echo.
echo Installiere Basis-Abhängigkeiten...
pip install -r requirements.txt
if errorlevel 1 (
    echo WARNUNG: Einige Basis-Abhängigkeiten konnten nicht installiert werden!
    echo.
)

echo.
echo Installiere Dashboard-Abhängigkeiten...
pip install -r requirements_dashboard.txt
if errorlevel 1 (
    echo WARNUNG: Einige Dashboard-Abhängigkeiten konnten nicht installiert werden!
    echo.
)

echo.
echo Erstelle Ausgabe- und Log-Verzeichnisse...
if not exist "output" mkdir output
if not exist "logs" mkdir logs

echo.
echo ========================================
echo    Installation abgeschlossen!
echo ========================================
echo.
echo Um die virtuelle Umgebung zu aktivieren:
echo   venv\Scripts\activate.bat
echo.
echo Um das Dashboard zu starten:
echo   streamlit run tradelog_dashboard.py
echo.
echo Um den DataLoader zu testen:
echo   python example_tradelog_loader.py
echo.
echo Drücken Sie eine beliebige Taste zum Beenden...
pause >nul
