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

# Performance-Monitoring für die Hauptfunktionen
@monitor_function(slow_threshold=2.0)
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

@monitor_function(slow_threshold=1.0)
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
        except Exception as e:
            st.error(f"Fehler beim Laden der Konfiguration: {e}")
            return
        
        # Services initialisieren
        if st.button("🔄 Services initialisieren"):
            with st.spinner("Initialisiere Services..."):
                if initialize_services(config):
                    st.success("Services erfolgreich initialisiert!")
                else:
                    st.error("Fehler bei der Service-Initialisierung")
        
        # Seitenauswahl
        page = st.selectbox(
            "📱 Seite auswählen:",
            [
                "📋 Übersicht", 
                "📈 Trade-Tabelle", 
                "📊 Metriken", 
                "📅 Kalender", 
                "📅 Monatskalender", 
                "🚀 TAT Tradenavigator (Optimiert)",
                "🎯 TAT Tradenavigator (Original)",
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
        # Temporäre Datei speichern
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            db_path = tmp_file.name
        
        st.session_state.temp_db_path = db_path
        st.success(f"Datei erfolgreich hochgeladen: {uploaded_file.name}")
    
    # Daten laden falls Pfad verfügbar
    if db_path and (uploaded_file is not None or os.path.exists(db_path)):
        if 'trade_data' not in st.session_state:
            with st.spinner("Lade Trade-Daten..."):
                trade_data = load_trade_data(db_path)
                if trade_data is not None:
                    st.session_state.trade_data = trade_data
                    st.session_state.db_path = db_path
        
        # Seite anzeigen
        if page == "📋 Übersicht":
            call_module_function('overview_page', 'show_overview_page', 
                              get_service('trade_data_service'), db_path)
        
        elif page == "📈 Trade-Tabelle":
            call_module_function('trade_table_page', 'show_trade_table_page', 
                              get_service('trade_data_service'), db_path)
        
        elif page == "📊 Metriken":
            call_module_function('metrics_page', 'show_metrics_page', 
                              get_service('trade_data_service'), db_path)
        
        elif page == "📅 Kalender":
            call_module_function('calendar_page', 'show_calendar_page', 
                              get_service('trade_data_service'), db_path)
        
        elif page == "📅 Monatskalender":
            call_module_function('monthly_calendar_page', 'show_monthly_calendar_page', 
                              get_service('trade_data_service'), db_path)
        
        elif page == "🚀 TAT Tradenavigator (Optimiert)":
            call_module_function('navigator_page_optimized', 'show_tat_navigator_page_optimized', 
                              get_service('trade_data_service'), db_path)
        
        elif page == "🎯 TAT Tradenavigator (Original)":
            call_module_function('navigator_page', 'show_tat_navigator_page', 
                              get_service('trade_data_service'), db_path)
        
        elif page == "📊 Performance Dashboard":
            show_performance_dashboard()
    
    else:
        st.info("Bitte wählen Sie eine SQLite-Datei aus oder geben Sie einen Pfad ein.")
    
    # Performance-Monitoring beenden
    execution_time = time.time() - start_time
    if execution_time > 1.0:
        st.warning(f"Dashboard-Ladezeit: {execution_time:.2f}s (langsam)")
    
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
