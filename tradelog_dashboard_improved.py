#!/usr/bin/env python3
"""
Tradelog Dashboard - Verbesserte Version
Hauptdatei mit den neuen Performance- und Wartbarkeitsverbesserungen
"""

import os
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import tempfile
import uuid
import time

# Streamlit-Startmeldungen ausblenden
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

# Projektverzeichnisse zum Python-Pfad hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Neue Core-Services importieren
from app.core.service_registry import register_service, get_service, has_service
from app.core.smart_cache import create_cache, get_cache_manager
from app.core.performance_monitor import get_performance_monitor, monitor_function
from app.core.module_loader import get_module_loader, call_module_function
from app.services.connection_pool import create_connection_pool, ConnectionConfig

# Bestehende Services
from app.services.trade_data_service import TradeDataService
from src.utils import load_config

# Einfacher Konfigurationsmanager für die Dateiauswahl
class SimpleConfigManager:
    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.last_file_config = self.config_dir / "last_file.txt"
        self.auto_load_config = self.config_dir / "auto_load.txt"
        
        # Stelle sicher, dass beide Konfigurationsdateien existieren
        self._ensure_config_files_exist()
    
    def _ensure_config_files_exist(self):
        """Stellt sicher, dass alle Konfigurationsdateien existieren"""
        try:
            # Auto-Load-Datei erstellen falls nicht vorhanden
            if not self.auto_load_config.exists():
                self.save_auto_load_setting(True)
                print("✅ Auto-Load-Datei erstellt")
            
            # Last-File-Datei erstellen falls nicht vorhanden (mit leerem Inhalt)
            if not self.last_file_config.exists():
                with open(self.last_file_config, 'w', encoding='utf-8') as f:
                    f.write("")
                print("✅ Last-File-Datei erstellt (leer)")
                
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Konfigurationsdateien: {e}")
    
    def save_last_file_path(self, file_path):
        """Speichert den zuletzt verwendeten Dateipfad"""
        try:
            # Stelle sicher, dass das Verzeichnis existiert
            self.config_dir.mkdir(exist_ok=True)
            
            # Datei schreiben
            with open(self.last_file_config, 'w', encoding='utf-8') as f:
                f.write(str(file_path))
            
            print(f"✅ Dateipfad gespeichert: {file_path}")
            print(f"📁 Datei gespeichert in: {self.last_file_config}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern des Dateipfads: {e}")
            print(f"📁 Verzeichnis: {self.config_dir}")
            print(f"📁 Datei: {self.last_file_config}")
            return False
    
    def get_last_file_path(self):
        """Holt den zuletzt verwendeten Dateipfad"""
        try:
            if self.last_file_config.exists():
                with open(self.last_file_config, 'r', encoding='utf-8') as f:
                    path = f.read().strip()
                    if path and os.path.exists(path):
                        print(f"✅ Gespeicherten Pfad gefunden: {path}")
                        return path
                    elif path:
                        print(f"⚠️ Gespeicherter Pfad existiert nicht mehr: {path}")
                    else:
                        print("ℹ️ Last-File-Datei ist leer")
            else:
                print("⚠️ Last-File-Datei existiert nicht")
            return None
            
        except Exception as e:
            print(f"❌ Fehler beim Laden des Dateipfads: {e}")
            return None
    
    def clear_last_file_path(self):
        """Löscht den gespeicherten Dateipfad"""
        try:
            if self.last_file_config.exists():
                # Datei leeren statt löschen
                with open(self.last_file_config, 'w', encoding='utf-8') as f:
                    f.write("")
                print("✅ Gespeicherten Pfad gelöscht (Datei geleert)")
            else:
                print("ℹ️ Last-File-Datei existiert nicht")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Löschen des Dateipfads: {e}")
            return False
    
    def save_auto_load_setting(self, auto_load):
        """Speichert die Auto-Load-Einstellung"""
        try:
            # Stelle sicher, dass das Verzeichnis existiert
            self.config_dir.mkdir(exist_ok=True)
            
            with open(self.auto_load_config, 'w', encoding='utf-8') as f:
                f.write('true' if auto_load else 'false')
            
            print(f"✅ Auto-Load-Einstellung gespeichert: {auto_load}")
            print(f"📁 Datei gespeichert in: {self.auto_load_config}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern der Auto-Load-Einstellung: {e}")
            return False
    
    def get_auto_load_setting(self):
        """Holt die Auto-Load-Einstellung"""
        try:
            if self.auto_load_config.exists():
                with open(self.auto_load_config, 'r', encoding='utf-8') as f:
                    setting = f.read().strip().lower()
                    return setting == 'true'
            return True  # Standard: Auto-Load aktiviert
        except Exception as e:
            print(f"❌ Fehler beim Laden der Auto-Load-Einstellung: {e}")
            return True  # Standard: Auto-Load aktiviert

# Module direkt importieren
from modules.overview_page import show_overview_page
from modules.trade_table_page import show_trade_table_page
from modules.metrics_page import show_metrics_page
from modules.calendar_page import show_calendar_page
from modules.monthly_calendar_page import show_monthly_calendar_page
from modules.navigator_page import show_tat_navigator_page

# Performance-Monitoring für die Hauptfunktionen
def initialize_services(config):
    """Initialisiert alle Services mit Performance-Monitoring."""
    try:
        # Service Registry initialisieren
        if not has_service('trade_data_service'):
            trade_service = TradeDataService(config)
            register_service('trade_data_service', trade_service)
            st.session_state.trade_service = trade_service
        
        # Cache-System initialisieren
        if not has_service('cache_manager'):
            cache_manager = get_cache_manager()
            register_service('cache_manager', cache_manager)
            
            # Erstelle spezifische Caches
            api_cache = create_cache('api_cache', max_size=500, default_ttl=300)
            trade_cache = create_cache('trade_cache', max_size=1000, default_ttl=600)
            
            st.session_state.api_cache = api_cache
            st.session_state.trade_cache = trade_cache
        
        # Module Loader initialisieren
        if not has_service('module_loader'):
            module_loader = get_module_loader('modules')
            register_service('module_loader', module_loader)
            st.session_state.module_loader = module_loader
        
        return True
        
    except Exception as e:
        st.error(f"Fehler bei der Service-Initialisierung: {e}")
        return False

def load_trade_data(db_path, use_cache=True):
    """Lädt Trade-Daten mit Caching."""
    if use_cache and hasattr(st.session_state, 'trade_cache'):
        cache_key = f"trade_data_{db_path}"
        cached_data = st.session_state.trade_cache.get(cache_key)
        
        if cached_data is not None:
            st.session_state.cache_hit = True
            return cached_data
    
    # Daten neu laden
    try:
        trade_service = get_service('trade_data_service')
        data = trade_service.load_trade_table(db_path)
        
        # Cache aktualisieren
        if use_cache and hasattr(st.session_state, 'trade_cache'):
            cache_key = f"trade_data_{db_path}"
            st.session_state.trade_cache.set(cache_key, data, ttl=600)  # 10 Minuten
        
        st.session_state.cache_hit = False
        return data
        
    except Exception as e:
        st.error(f"Fehler beim Laden der Trade-Daten: {e}")
        return None

def show_performance_dashboard():
    """Zeigt Performance-Statistiken an."""
    st.header("📊 Performance Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Cache-Statistiken
        if hasattr(st.session_state, 'api_cache'):
            api_stats = st.session_state.api_cache.get_stats()
            if api_stats:
                st.metric("API Cache Hit Rate", f"{api_stats['hit_rate']:.1%}")
                st.metric("API Cache Size", api_stats['size'])
        
        if hasattr(st.session_state, 'trade_cache'):
            trade_stats = st.session_state.trade_cache.get_stats()
            if trade_stats:
                st.metric("Trade Cache Hit Rate", f"{trade_stats['hit_rate']:.1%}")
                st.metric("Trade Cache Size", trade_stats['size'])
    
    with col2:
        # Performance-Monitor Statistiken
        perf_monitor = get_performance_monitor()
        summary = perf_monitor.get_performance_summary()
        
        st.metric("Überwachte Funktionen", summary['total_functions'])
        st.metric("Gesamtaufrufe", summary['total_calls'])
        st.metric("Durchschn. Ausführungszeit", f"{summary['overall_avg_execution_time']:.3f}s")
    
    with col3:
        # Module Loader Statistiken
        if hasattr(st.session_state, 'module_loader'):
            module_stats = st.session_state.module_loader.get_cache_stats()
            st.metric("Verfügbare Module", module_stats['total_modules'])
            st.metric("Geladene Module", module_stats['loaded_modules'])
            st.metric("Cache-Auslastung", f"{module_stats['cache_usage']:.1%}")
    
    # Detaillierte Performance-Daten
    st.subheader("Top-Funktionen nach Ausführungszeit")
    perf_monitor = get_performance_monitor()
    top_functions = perf_monitor.get_top_functions(count=5, by="avg_time")
    
    if top_functions:
        perf_data = []
        for func in top_functions:
            perf_data.append({
                'Funktion': func.function_name,
                'Aufrufe': func.total_calls,
                'Durchschn. Zeit': f"{func.avg_execution_time:.3f}s",
                'Min Zeit': f"{func.min_execution_time:.3f}s",
                'Max Zeit': f"{func.max_execution_time:.3f}s",
                'Erfolgsrate': f"{func.success_rate:.1%}"
            })
        
        perf_df = pd.DataFrame(perf_data)
        st.dataframe(perf_df, use_container_width=True)
    
    # Cache-Performance
    st.subheader("Cache-Performance")
    if hasattr(st.session_state, 'api_cache') and hasattr(st.session_state, 'trade_cache'):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**API Cache**")
            api_stats = st.session_state.api_cache.get_stats()
            if api_stats:
                st.json(api_stats)
        
        with col2:
            st.write("**Trade Cache**")
            trade_stats = st.session_state.trade_cache.get_stats()
            if trade_stats:
                st.json(trade_stats)

def main():
    """Hauptfunktion des verbesserten Dashboards."""
    
    # Performance-Monitoring starten
    start_time = time.time()
    
    # Variablen initialisieren
    db_path = None
    uploaded_file = None
    
    # Session State initialisieren falls nicht vorhanden
    if 'temp_db_path' not in st.session_state:
        st.session_state.temp_db_path = None
    if 'last_uploaded_file' not in st.session_state:
        st.session_state.last_uploaded_file = None
    if 'db_path' not in st.session_state:
        st.session_state.db_path = None
    if 'error_occurred' not in st.session_state:
        st.session_state.error_occurred = False
    
    # Filter-Status initialisieren (standardmäßig deaktiviert)
    if 'apply_filters' not in st.session_state:
        st.session_state.apply_filters = False
    if 'filters_applied_nav' not in st.session_state:
        st.session_state.filters_applied_nav = False
    
    # Datumsfilter initialisieren (standardmäßig leer)
    if 'start_date' not in st.session_state:
        st.session_state.start_date = None
    if 'end_date' not in st.session_state:
        st.session_state.end_date = None
    
    # Seite konfigurieren
    st.set_page_config(
        page_title="Tradelog Dashboard - Verbessert",
        page_icon="📊",
        layout="wide"
    )
    
    # Header
    st.title("📊 Tradelog Dashboard - Verbessert")
    st.markdown("---")
    
    # Sidebar für Dateiauswahl
    with st.sidebar:
        st.header("📁 Dateiauswahl")
        
        # Datei-Upload
        uploaded_file = st.file_uploader(
            "SQLite-Datei hochladen",
            type=['db', 'db3', 'sqlite', 'sqlite3'],
            help="Laden Sie Ihre SQLite-Tradelogdatei hoch",
            key="file_uploader"  # Eindeutiger Key für den Uploader
        )
        
        # Cache leeren wenn neue Datei hochgeladen wird
        if uploaded_file is not None and hasattr(st.session_state, 'last_uploaded_file'):
            if st.session_state.last_uploaded_file != uploaded_file.name:
                # Neue Datei - Cache leeren
                if 'trade_data' in st.session_state:
                    del st.session_state.trade_data
                if 'db_path' in st.session_state:
                    del st.session_state.db_path
                if 'temp_db_path' in st.session_state:
                    del st.session_state.temp_db_path
                st.session_state.last_uploaded_file = uploaded_file.name
        elif uploaded_file is not None:
            st.session_state.last_uploaded_file = uploaded_file.name
        
        # Datei-Validierung
        if uploaded_file is not None:
            # Überprüfen ob es sich um eine gültige SQLite-Datei handelt
            try:
                file_content = uploaded_file.getvalue()
                if not file_content.startswith(b'SQLite format 3'):
                    st.warning("Die Datei scheint keine gültige SQLite-Datenbank zu sein.")
                    uploaded_file = None
                    if 'last_uploaded_file' in st.session_state:
                        del st.session_state.last_uploaded_file
                    if 'db_path' in st.session_state:
                        del st.session_state.db_path
                    
                    # Fehler-Flag setzen
                    st.session_state.error_occurred = True
                else:
                    uploaded_file.seek(0)  # Zurück zum Anfang der Datei
            except Exception as e:
                st.error(f"Fehler bei der Datei-Validierung: {e}")
                uploaded_file = None
                if 'last_uploaded_file' in st.session_state:
                    del st.session_state.last_uploaded_file
                if 'db_path' in st.session_state:
                    del st.session_state.db_path
                
                # Fehler-Flag setzen
                st.session_state.error_occurred = True
        
        # Debug-Informationen für Datei-Upload
        if uploaded_file is not None and uploaded_file.size > 0:
            st.info(f"Datei erkannt: {uploaded_file.name} ({uploaded_file.size} Bytes)")
        
        # Oder Pfad eingeben
        st.markdown("---")
        st.subheader("Oder Pfad eingeben")
        manual_db_path = st.text_input(
            "Pfad zur SQLite-Datei:",
            placeholder="C:/Path/To/Your/tradelog.db3"
        )
        
        # Automatisches Laden der zuletzt verwendeten Datei
        st.markdown("---")
        st.subheader("💾 Gespeicherte Einstellungen")
        
        # Konfigurationsmanager initialisieren
        config_manager = SimpleConfigManager()
        
        # Einstellungen laden
        auto_load = config_manager.get_auto_load_setting()
        last_file_path = config_manager.get_last_file_path()
        
        # Checkbox für automatisches Laden
        auto_load = st.checkbox(
            "Zuletzt verwendete Datei automatisch laden",
            value=auto_load,
            help="Beim nächsten Start wird automatisch die zuletzt verwendete Datei geladen"
        )
        
        # Auto-Load-Einstellung speichern
        config_manager.save_auto_load_setting(auto_load)
        
        # Zuletzt verwendete Datei anzeigen
        if last_file_path:
            # Prüfe ob es sich um eine Upload-Datei handelt
            if last_file_path.startswith("UPLOADED:"):
                filename = last_file_path.replace("UPLOADED:", "")
                st.info(f"📁 Zuletzt verwendet (Upload): {filename}")
                st.warning("⚠️ Upload-Dateien können nicht direkt geladen werden. Bitte laden Sie die Datei erneut hoch.")
            else:
                st.info(f"📁 Zuletzt verwendet: {os.path.basename(last_file_path)}")
                
                # Button zum Laden der gespeicherten Datei
                if st.button("🔄 Gespeicherte Datei laden", use_container_width=True):
                    if os.path.exists(last_file_path):
                        db_path = last_file_path
                        st.session_state.db_path = db_path
                        st.success(f"✅ Datei geladen: {os.path.basename(db_path)}")
                        st.rerun()
                    else:
                        st.error("❌ Gespeicherte Datei nicht mehr verfügbar")
                        # Gespeicherten Pfad löschen
                        config_manager.clear_last_file_path()
                        st.rerun()
            
            # Button zum Löschen des gespeicherten Pfads
            if st.button("🗑️ Gespeicherten Pfad löschen", use_container_width=True):
                config_manager.clear_last_file_path()
                st.success("✅ Gespeicherter Pfad gelöscht")
                st.rerun()
        else:
            st.info("ℹ️ Keine Datei gespeichert")
        
        # db_path setzen basierend auf Upload oder manueller Eingabe
        if uploaded_file is not None:
            # Verwende den Pfad der hochgeladenen Datei
            pass  # db_path wird später gesetzt
        elif manual_db_path and manual_db_path.strip():
            db_path = manual_db_path.strip()
            # Pfad in Konfiguration speichern
            if os.path.exists(db_path):
                st.info(f"🔄 Speichere Pfad: {db_path}")
                if config_manager.save_last_file_path(db_path):
                    st.success("✅ Pfad gespeichert")
                else:
                    st.error("❌ Fehler beim Speichern des Pfads")
            else:
                st.error(f"❌ Datei existiert nicht: {db_path}")
        else:
            db_path = None
        
        # Konfiguration laden
        try:
            config = load_config()
        except Exception as e:
            st.error(f"Fehler beim Laden der Konfiguration: {e}")
            st.exception(e)  # Detaillierte Fehlerinformationen anzeigen
            
            # Fehler-Flag setzen
            st.session_state.error_occurred = True
            
            return
        
        # Services initialisieren
        if 'services_initialized' not in st.session_state:
            with st.spinner("Initialisiere Services..."):
                try:
                    if initialize_services(config):
                        st.session_state.services_initialized = True
                        st.success("Services erfolgreich initialisiert!")
                    else:
                        st.error("Fehler bei der Service-Initialisierung")
                        
                        # Fehler-Flag setzen
                        st.session_state.error_occurred = True
                        
                        return
                except Exception as e:
                    st.error(f"Unerwarteter Fehler bei der Service-Initialisierung: {e}")
                    st.exception(e)  # Detaillierte Fehlerinformationen anzeigen
                    
                    # Fehler-Flag setzen
                    st.session_state.error_occurred = True
                    
                    return
        else:
            st.success("✅ Services bereits initialisiert")
        
        # Seitenauswahl
        page = st.selectbox(
            "📱 Seite auswählen:",
            [
                "📋 Übersicht", 
                "📈 Trade-Tabelle", 
                "📊 Metriken", 
                "📅 Kalender", 
                "📅 Monatskalender", 
                "🎯 TAT Tradenavigator",
                "📊 Performance Dashboard"
            ],
            key="page_selector"
        )
        
        # Performance-Informationen
        if hasattr(st.session_state, 'cache_hit'):
            if st.session_state.cache_hit:
                st.success("✅ Daten aus Cache geladen")
            else:
                st.info("🔄 Daten neu geladen")
    
    # Hauptbereich
    if uploaded_file is not None:
        try:
            # Temporäre Datei speichern
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
                # Dateiinhalt lesen
                uploaded_file.seek(0)  # Zurück zum Anfang der Datei
                file_content = uploaded_file.read()
                
                if file_content:
                    tmp_file.write(file_content)
                    tmp_file.flush()  # Sicherstellen, dass Daten geschrieben werden
                    db_path = tmp_file.name
                    st.session_state.temp_db_path = db_path
                    st.session_state.db_path = db_path  # Auch in session_state setzen
                    
                    # Pfad in Konfiguration speichern (für Upload-Dateien)
                    config_manager = SimpleConfigManager()
                    # Speichere den ursprünglichen Dateinamen für Uploads
                    original_filename = uploaded_file.name
                    if config_manager.save_last_file_path(f"UPLOADED:{original_filename}"):
                        st.success(f"✅ Upload-Datei gespeichert: {original_filename}")
                        st.info(f"📁 Dateiname: {original_filename}")
                    else:
                        st.warning("⚠️ Konnte Upload-Datei nicht in Konfiguration speichern")
                    
                    # Datei schließen
                    uploaded_file.close()
                else:
                    st.error("Die hochgeladene Datei ist leer oder konnte nicht gelesen werden.")
                    uploaded_file.close()
                    return
        except Exception as e:
            st.error(f"Fehler beim Verarbeiten der hochgeladenen Datei: {e}")
            st.exception(e)  # Detaillierte Fehlerinformationen anzeigen
            # Datei schließen falls möglich
            try:
                if uploaded_file is not None:
                    uploaded_file.close()
            except:
                pass
            
            # Session State aufräumen
            if 'last_uploaded_file' in st.session_state:
                del st.session_state.last_uploaded_file
            if 'db_path' in st.session_state:
                del st.session_state.db_path
            if 'temp_db_path' in st.session_state:
                del st.session_state.temp_db_path
            
            # Fehler-Flag setzen
            st.session_state.error_occurred = True
            
            return
    
    # Daten laden falls Pfad verfügbar
    # db_path aus session_state holen falls verfügbar
    if 'db_path' in st.session_state and st.session_state.db_path:
        db_path = st.session_state.db_path
    
    # Automatisches Laden der zuletzt verwendeten Datei beim Start (falls noch kein db_path gesetzt)
    if not db_path:
        config_manager = SimpleConfigManager()
        auto_load = config_manager.get_auto_load_setting()
        last_file_path = config_manager.get_last_file_path()
        
        st.info(f"🔍 Auto-Load: {auto_load}, Gespeicherter Pfad: {last_file_path}")
        
        if auto_load and last_file_path:
            # Prüfe ob es sich um eine Upload-Datei handelt
            if last_file_path.startswith("UPLOADED:"):
                filename = last_file_path.replace("UPLOADED:", "")
                st.info(f"📁 Suche nach Upload-Datei: {filename}")
                st.warning("⚠️ Upload-Dateien können nicht automatisch geladen werden. Bitte laden Sie die Datei erneut hoch.")
            elif os.path.exists(last_file_path):
                db_path = last_file_path
                st.session_state.db_path = db_path
                st.info(f"🔄 Automatisch geladen: {os.path.basename(db_path)}")
            else:
                st.warning(f"⚠️ Gespeicherter Pfad existiert nicht mehr: {last_file_path}")
        elif auto_load:
            st.info("ℹ️ Kein gespeicherter Pfad gefunden")
    
    if db_path and (uploaded_file is not None or os.path.exists(db_path)):
        # Überprüfen ob die Datei existiert und lesbar ist
        if not os.path.exists(db_path):
            st.error(f"Die Datei {db_path} existiert nicht.")
            return
        
        if not os.access(db_path, os.R_OK):
            st.error(f"Keine Leseberechtigung für die Datei {db_path}.")
            return
        # Prüfen ob Services initialisiert sind
        if 'services_initialized' not in st.session_state:
            st.error("Services müssen zuerst initialisiert werden!")
            return
            
        if 'trade_data' not in st.session_state:
            try:
                with st.spinner("Lade Trade-Daten..."):
                    # Überprüfen ob die Datenbank-Datei gültig ist
                    if not os.path.isfile(db_path):
                        st.error(f"Der Pfad {db_path} ist keine gültige Datei.")
                        return
                    
                    trade_data = load_trade_data(db_path)
                    if trade_data is not None:
                        st.session_state.trade_data = trade_data
                        st.session_state.db_path = db_path
                        st.success("Trade-Daten erfolgreich geladen!")
                    else:
                        st.warning("Keine Trade-Daten gefunden oder Fehler beim Laden.")
                        return
            except Exception as e:
                st.error(f"Fehler beim Laden der Trade-Daten: {e}")
                st.exception(e)  # Detaillierte Fehlerinformationen anzeigen
                
                # Session State aufräumen
                if 'trade_data' in st.session_state:
                    del st.session_state.trade_data
                if 'db_path' in st.session_state:
                    del st.session_state.db_path
                
                # Fehler-Flag setzen
                st.session_state.error_occurred = True
                
                return
        
        # Services für Seitenaufrufe verfügbar machen
        try:
            # Überprüfen ob der Service verfügbar ist
            if not has_service('trade_data_service'):
                st.error("Trade Data Service ist nicht verfügbar.")
                st.info("Bitte initialisieren Sie zuerst die Services.")
                return
            
            trade_service = get_service('trade_data_service')
            
            # Überprüfen ob der Service gültig ist
            if trade_service is None:
                st.error("Trade Data Service konnte nicht geladen werden.")
                return
            
            # Seite anzeigen
            if page == "📋 Übersicht":
                show_overview_page(trade_service, db_path)
            
            elif page == "📈 Trade-Tabelle":
                show_trade_table_page(trade_service, db_path)
            
            elif page == "📊 Metriken":
                show_metrics_page(trade_service, db_path)
            
            elif page == "📅 Kalender":
                show_calendar_page(trade_service, db_path)
            
            elif page == "📅 Monatskalender":
                show_monthly_calendar_page(trade_service, db_path)
            
            elif page == "🎯 TAT Tradenavigator":
                show_tat_navigator_page(trade_service, db_path)
            
            elif page == "📊 Performance Dashboard":
                show_performance_dashboard()
                
        except KeyError as e:
            st.error(f"Service nicht verfügbar: {e}")
            st.info("Bitte initialisieren Sie zuerst die Services.")
            return
        except Exception as e:
            st.error(f"Unerwarteter Fehler: {e}")
            st.exception(e)  # Detaillierte Fehlerinformationen anzeigen
            
            # Session State aufräumen
            if 'trade_data' in st.session_state:
                del st.session_state.trade_data
            if 'db_path' in st.session_state:
                del st.session_state.db_path
            
            # Fehler-Flag setzen
            st.session_state.error_occurred = True
            
            return
    
    else:
        if uploaded_file is None and (not db_path or not db_path.strip()):
            st.info("Bitte wählen Sie eine SQLite-Datei aus oder geben Sie einen Pfad ein.")
        elif db_path and not os.path.exists(db_path):
            st.error(f"Der angegebene Pfad existiert nicht: {db_path}")
        else:
            st.info("Keine gültige Datenbank-Datei verfügbar.")
    
    # Performance-Monitoring beenden
    execution_time = time.time() - start_time
    if execution_time > 1.0:
        st.warning(f"Dashboard-Ladezeit: {execution_time:.2f}s (langsam)")
    
    # Temporäre Dateien aufräumen
    if hasattr(st.session_state, 'temp_db_path') and st.session_state.temp_db_path:
        try:
            if os.path.exists(st.session_state.temp_db_path):
                os.unlink(st.session_state.temp_db_path)
                st.session_state.temp_db_path = None
        except Exception as e:
            st.warning(f"Konnte temporäre Datei nicht löschen: {e}")
    
    # Session State aufräumen falls Fehler aufgetreten sind
    if 'error_occurred' in st.session_state and st.session_state.error_occurred:
        if 'trade_data' in st.session_state:
            del st.session_state.trade_data
        if 'db_path' in st.session_state:
            del st.session_state.db_path
        if 'temp_db_path' in st.session_state:
            del st.session_state.temp_db_path
        st.session_state.error_occurred = False
    
    # Footer mit Performance-Informationen
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if hasattr(st.session_state, 'cache_hit'):
            cache_status = "✅ Cache Hit" if st.session_state.cache_hit else "🔄 Cache Miss"
            st.caption(f"Cache-Status: {cache_status}")
    
    with col2:
        st.caption(f"Ausführungszeit: {execution_time:.3f}s")
    
    with col3:
        if hasattr(st.session_state, 'module_loader'):
            module_stats = st.session_state.module_loader.get_cache_stats()
            st.caption(f"Module: {module_stats['loaded_modules']}/{module_stats['total_modules']}")

if __name__ == "__main__":
    main()
