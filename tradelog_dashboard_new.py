#!/usr/bin/env python3
"""
Tradelog Dashboard - Modulare Version
Hauptdatei mit sauberer Struktur und ausgelagerten Modulen
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import tempfile
import uuid

# Projektverzeichnisse zum Python-Pfad hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Alle Imports nach der Pfad-Konfiguration
from app.services.trade_data_service import TradeDataService
from src.utils import load_config

# Module imports
from modules.overview_page import show_overview_page
from modules.trade_table_page import show_trade_table_page
from modules.metrics_page import show_metrics_page
from modules.navigator_page import show_tat_navigator_page
from modules.api_charts import test_api_connection

# Direkter Import mit korrigiertem Pfad
try:
    from utils.database_utils import is_sqlite_file
except ImportError:
    # Fallback: relativer Import
    import importlib.util
    spec = importlib.util.spec_from_file_location("database_utils", project_root / "utils" / "database_utils.py")
    database_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(database_utils)
    is_sqlite_file = database_utils.is_sqlite_file

# Seite konfigurieren
st.set_page_config(
    page_title="Tradelog Dashboard",
    page_icon="📊",
    layout="wide"
)

def main():
    """Hauptfunktion des Dashboards."""
    
    # Header
    st.title("📊 Tradelog Dashboard")
    
    # Sidebar für Dateiauswahl
    with st.sidebar:
        st.header("📁 Dateiauswahl")
        
        # Datei-Upload
        uploaded_file = st.file_uploader(
            "SQLite-Datei hochladen",
            type=['db', 'db3', 'sqlite', 'sqlite3'],
            help="Laden Sie Ihre SQLite-Tradelogdatei hoch"
        )
        
        # Oder Pfad eingeben
        st.markdown("---")
        st.subheader("Oder Pfad eingeben")
        db_path = st.text_input(
            "Pfad zur SQLite-Datei:",
            placeholder="C:/Path/To/Your/tradelog.db3"
        )
        
        # Konfiguration laden
        try:
            config = load_config()
            data_loader = TradeDataService(config)
        except Exception as e:
            st.error(f"Fehler beim Laden der Konfiguration: {e}")
            return
        
        # Seitenauswahl
        page = st.selectbox(
            "📱 Seite auswählen:",
            ["📋 Übersicht", "📈 Trade-Tabelle", "📊 Metriken", "🎯 TAT Tradenavigator"],
            key="page_selector"
        )
    
    # Hauptbereich
    if uploaded_file is not None:
        # Temporäre Datei speichern
        unique_id = str(uuid.uuid4())[:8]
        temp_path = Path(f"temp_upload_{unique_id}.db")
        
        try:
            # Datei schreiben
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Seite anzeigen
            if is_sqlite_file(str(temp_path)):
                show_page(page, data_loader, str(temp_path))
            else:
                st.error("Die hochgeladene Datei scheint keine gültige SQLite-Datenbank zu sein.")
        except Exception as e:
            st.error(f"Fehler beim Laden der Daten: {e}")
        finally:
            # Temporäre Datei löschen
            try:
                temp_path.unlink()
            except:
                pass
                
    elif db_path and Path(db_path).exists():
        if is_sqlite_file(db_path):
            try:
                show_page(page, data_loader, db_path)
            except Exception as e:
                st.error(f"Fehler beim Laden der Daten: {e}")
        else:
            st.error(f"Die Datei {Path(db_path).name} scheint keine gültige SQLite-Datenbank zu sein.")
    
    else:
        show_welcome_screen()

def show_page(page, data_loader, db_path):
    """Zeigt die gewählte Seite an."""
    if page == "📋 Übersicht":
        show_overview_page(data_loader, db_path)
    elif page == "📈 Trade-Tabelle":
        show_trade_table_page(data_loader, db_path)
    elif page == "📊 Metriken":
        show_metrics_page(data_loader, db_path)
    elif page == "🎯 TAT Tradenavigator":
        show_tat_navigator_page(data_loader, db_path)

# Module-Funktionen sind bereits importiert

def show_welcome_screen():
    """Willkommensbildschirm anzeigen."""
    st.markdown("""
    ## Willkommen beim Tradelog Dashboard! 🎯
    
    **So verwenden Sie das Dashboard:**
    
    1. **📁 Datei hochladen**: Laden Sie Ihre SQLite-Tradelogdatei über den Upload-Button hoch
    2. **🔗 Pfad eingeben**: Oder geben Sie den Pfad zu Ihrer Datei in der Seitenleiste ein
    3. **🧭 Seite wählen**: Wählen Sie zwischen Übersicht und Trade-Tabelle
    
    **Unterstützte Formate:**
    - SQLite-Datenbanken (.db, .db3, .sqlite, .sqlite3)
    """)

if __name__ == "__main__":
    main()
