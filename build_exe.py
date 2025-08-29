#!/usr/bin/env python3
"""
Build-Skript für die EXE-Datei des Tradelog Dashboards
"""

import PyInstaller.__main__
import os
import sys

def build_exe():
    """Erstellt eine ausführbare EXE-Datei des Dashboards"""
    
    # PyInstaller-Konfiguration
    PyInstaller.__main__.run([
        'tradelog_dashboard_improved.py',
        '--onefile',
        '--windowed',
        '--name=TAT_Dashboard',
        '--icon=📊',  # Falls du ein Icon hast
        '--add-data=app;app',
        '--add-data=modules;modules',
        '--add-data=config;config',
        '--hidden-import=streamlit',
        '--hidden-import=pandas',
        '--hidden-import=plotly',
        '--hidden-import=sqlite3',
        '--hidden-import=app.core.service_registry',
        '--hidden-import=app.core.smart_cache',
        '--hidden-import=app.services.trade_data_service',
        '--hidden-import=modules.overview_page',
        '--hidden-import=modules.trade_table_page',
        '--hidden-import=modules.metrics_page',
        '--hidden-import=modules.calendar_page',
        '--hidden-import=modules.monthly_calendar_page',
        '--hidden-import=modules.navigator_page',
        '--distpath=dist',
        '--workpath=build',
        '--specpath=build'
    ])

if __name__ == "__main__":
    build_exe()
    print("✅ EXE-Datei erfolgreich erstellt!")
    print("📁 Datei befindet sich im 'dist' Ordner")
