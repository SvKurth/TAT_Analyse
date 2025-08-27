#!/usr/bin/env python3
"""
Tradelog Dashboard - Modulare Version
Hauptdatei mit sauberer Struktur und ausgelagerten Modulen
"""

import os
# Streamlit-Startmeldungen ausblenden
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

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
from modules.calendar_page import show_calendar_page
from modules.monthly_calendar_page import show_monthly_calendar_page
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

# Weitere Startmeldungen unterdrücken
# st.set_option('deprecation.showPyplotGlobalUse', False)  # Nicht unterstützt in dieser Streamlit-Version

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
            ["📋 Übersicht", "📈 Trade-Tabelle", "📊 Metriken", "📅 Kalender", "📅 Monatskalender", "🎯 TAT Tradenavigator"],
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
            
            # Prüfe ob es eine gültige SQLite-Datei ist
            if not is_sqlite_file(str(temp_path)):
                st.error("❌ Die hochgeladene Datei scheint keine gültige SQLite-Datenbank zu sein.")
                st.info("💡 Bitte stellen Sie sicher, dass Sie eine gültige SQLite-Datenbank hochladen.")
                return
            
            # Prüfe ob die Datenbank gültig ist
            try:
                # Seite anzeigen
                show_page(page, data_loader, str(temp_path))
            except Exception as e:
                st.error(f"❌ Fehler beim Laden der Datenbank: {e}")
                st.info("💡 Die Datenbank könnte beschädigt oder leer sein.")
                
                # Debug-Informationen anzeigen
                with st.expander("🐛 Debug-Informationen"):
                    st.write(f"**Fehler:** {str(e)}")
                    st.write(f"**Datei:** {uploaded_file.name}")
                    st.write(f"**Größe:** {len(uploaded_file.getvalue())} Bytes")
                    
        except Exception as e:
            st.error(f"❌ Fehler beim Laden der Daten: {e}")
        finally:
            # Temporäre Datei löschen
            try:
                temp_path.unlink()
            except:
                pass
                
    elif db_path and Path(db_path).exists():
        if not is_sqlite_file(db_path):
            st.error(f"❌ Die Datei {Path(db_path).name} scheint keine gültige SQLite-Datenbank zu sein.")
            st.info("💡 Bitte stellen Sie sicher, dass Sie einen gültigen Pfad zu einer SQLite-Datenbank eingeben.")
            return
        
        try:
            show_page(page, data_loader, db_path)
        except Exception as e:
            st.error(f"❌ Fehler beim Laden der Datenbank: {e}")
            st.info("💡 Die Datenbank könnte beschädigt oder leer sein.")
            
            # Debug-Informationen anzeigen
            with st.expander("🐛 Debug-Informationen"):
                st.write(f"**Fehler:** {str(e)}")
                st.write(f"**Pfad:** {db_path}")
                st.write(f"**Existiert:** {Path(db_path).exists()}")
                st.write(f"**Größe:** {Path(db_path).stat().st_size if Path(db_path).exists() else 'N/A'} Bytes")
    
    else:
        show_welcome_screen()

def show_page(page, data_loader, db_path):
    """Zeigt die gewählte Seite an."""
    try:
        if page == "📋 Übersicht":
            show_overview_page(data_loader, db_path)
        elif page == "📈 Trade-Tabelle":
            show_trade_table_page(data_loader, db_path)
        elif page == "📊 Metriken":
            show_metrics_page(data_loader, db_path)
        elif page == "📅 Kalender":
            show_calendar_page(data_loader, db_path)
        elif page == "📅 Monatskalender":
            show_monthly_calendar_page(data_loader, db_path)
        elif page == "🎯 TAT Tradenavigator":
            show_tat_navigator_page(data_loader, db_path)
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Seite '{page}': {e}")
        st.info("💡 Versuchen Sie es erneut oder wählen Sie eine andere Seite aus.")
        
        # Debug-Informationen anzeigen
        with st.expander("🐛 Debug-Informationen"):
            st.write(f"**Fehler:** {str(e)}")
            st.write(f"**Seite:** {page}")
            st.write(f"**Datenbank:** {db_path}")
            st.write(f"**Datenloader:** {type(data_loader).__name__}")

def validate_database(db_path: str, data_loader) -> bool:
    """Validiert eine Datenbank und zeigt Informationen an."""
    try:
        st.info("🔍 Validiere Datenbank...")
        
        # Datenbankinformationen abrufen
        db_info = data_loader.get_sqlite_table_info(db_path)
        
        if not db_info or 'tables' not in db_info:
            st.error("❌ Konnte keine Tabelleninformationen abrufen")
            return False
        
        tables = db_info['tables']
        
        if not tables:
            st.error("❌ Keine Tabellen in der Datenbank gefunden")
            return False
        
        st.success(f"✅ Datenbank validiert: {len(tables)} Tabellen gefunden")
        
        # Tabellenübersicht anzeigen
        with st.expander("📋 Tabellenübersicht"):
            for table_name, table_info in tables.items():
                st.write(f"**{table_name}** ({table_info['row_count']} Zeilen, {len(table_info['columns'])} Spalten)")
                
                # Spalten anzeigen
                columns_text = ", ".join([f"{col['name']}({col['type']})" for col in table_info['columns'][:5]])
                if len(table_info['columns']) > 5:
                    columns_text += f" ... und {len(table_info['columns']) - 5} weitere"
                st.write(f"Spalten: {columns_text}")
                st.write("---")
        
        # Trade-Tabelle suchen
        trade_table = data_loader.database_service.find_trade_table(db_path)
        if trade_table:
            st.success(f"🎯 Trade-Tabelle gefunden: {trade_table}")
            return True
        else:
            st.warning("⚠️ Keine Trade-Tabelle gefunden")
            st.info("💡 Verfügbare Tabellen:")
            for table_name in tables.keys():
                st.write(f"- {table_name}")
            return False
            
    except Exception as e:
        st.error(f"❌ Fehler bei der Datenbankvalidierung: {e}")
        return False

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
