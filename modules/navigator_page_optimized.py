"""
Optimierte Navigator Page Module für Tradelog Dashboard
Zeigt die TAT Navigator-Seite mit Navigation und Charts
Performance-optimiert mit Async-Processing, Batch-API-Calls und intelligentem Caching
"""

import streamlit as st
import pandas as pd
import datetime
import time
import asyncio
import concurrent.futures
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Optional, Tuple
import threading
from queue import Queue
import json

# Neue Core-Services importieren
from app.core.performance_monitor import monitor_function
from app.core.smart_cache import get_cache_manager
from app.core.module_loader import get_module_loader
from app.services.connection_pool import get_connection_pool
from app.services.api_optimizer import get_api_optimizer, get_prefetch_manager

# Bestehende Module importieren
from modules.api_charts import (
    get_option_price_data, 
    get_spx_vix_data, 
    create_options_price_chart, 
    create_spx_vix_chart,
    test_api_connection
)
from .api_cache import get_cache_instance
from .trade_results_cache import get_trade_results_cache

# Performance-Konstanten
MAX_CONCURRENT_API_CALLS = 5
BATCH_SIZE = 10
CACHE_TTL_HOURS = 24

class NavigatorPerformanceOptimizer:
    """Performance-Optimierer für den Navigator"""
    
    def __init__(self):
        self.api_cache = get_cache_instance()
        self.trade_results_cache = get_trade_results_cache()
        self.smart_cache = get_cache_manager().get_cache("navigator_data")
        self.connection_pool = get_connection_pool()
        self.logger = get_logger(__name__)
        
        # API-Optimizer initialisieren
        self.api_optimizer = get_api_optimizer()
        self.prefetch_manager = get_prefetch_manager()
        
        # API-Funktion registrieren
        self.api_optimizer.register_api_function('get_option_price_data', get_option_price_data)
        
        # Prefetching starten
        self.prefetch_manager.start_prefetching(strategy='smart')
        
    @monitor_function
    def batch_load_api_data(self, trades_batch: List[Tuple]) -> Dict[str, Any]:
        """Lädt API-Daten für einen Batch von Trades mit dem API-Optimizer"""
        results = {}
        
        # Requests für den API-Optimizer vorbereiten
        api_requests = []
        trade_info_map = {}
        
        for trade_info in trades_batch:
            idx, trade, date_cols = trade_info
            try:
                # Strike und Optionstyp ermitteln
                strike = None
                option_type = None
                
                if 'ShortPut' in trade and pd.notna(trade['ShortPut']) and trade['ShortPut'] != 0:
                    strike = int(trade['ShortPut'])
                    option_type = 'P'
                elif 'ShortCall' in trade and pd.notna(trade['ShortCall']) and trade['ShortCall'] != 0:
                    strike = int(trade['ShortCall'])
                    option_type = 'C'
                
                if not strike or not option_type:
                    results[idx] = {'error': 'Keine Option'}
                    continue
                
                trade_date = trade[date_cols[0]]
                if not hasattr(trade_date, 'strftime'):
                    results[idx] = {'error': 'Ungültiges Datum'}
                    continue
                
                api_date = trade_date.strftime('%Y-%m-%d')
                trade_id = f"{api_date}_{option_type}{strike}_{idx}"
                
                # Prüfe Trade-Results-Cache zuerst
                cached_results = self.trade_results_cache.get_cached_results(
                    trade_id, api_date, option_type, strike
                )
                
                if cached_results:
                    results[idx] = {
                        'cached': True,
                        'handelsende_preis': cached_results['handelsende_preis'],
                        'peak_preis': cached_results['peak_preis'],
                        'peak_zeit': cached_results['peak_zeit'],
                        'api_link': cached_results['api_link']
                    }
                    continue
                
                # API-Request vorbereiten
                api_requests.append((trade_id, 'SPX', api_date, option_type, strike))
                trade_info_map[trade_id] = (idx, trade, date_cols)
                
            except Exception as e:
                results[idx] = {'error': f'Fehler: {str(e)}'}
        
        if not api_requests:
            return results
        
        # API-Requests einreichen
        self.api_optimizer.submit_batch_requests(api_requests, priority=1)
        
        # Prefetching für zukünftige Requests
        self.prefetch_manager.add_prefetch_request(api_requests)
        
        # Warte auf alle Responses
        self.api_optimizer.wait_for_completion(timeout=30.0)
        
        # Alle Responses abholen
        api_responses = self.api_optimizer.get_all_responses(timeout=5.0)
        
        # Responses verarbeiten
        for response in api_responses:
            if response.success and response.data:
                trade_id = response.trade_id
                if trade_id in trade_info_map:
                    idx, trade, date_cols = trade_info_map[trade_id]
                    
                    # Daten verarbeiten
                    handelsende_preis, peak_preis, peak_zeit = self._process_api_response(
                        response.data, trade, date_cols
                    )
                    
                    # API-Link erstellen
                    api_date = trade_id.split('_')[0]
                    option_type = trade_id.split('_')[1][0]
                    strike = trade_id.split('_')[1][1:]
                    api_link = f"https://api.0dtespx.com/optionPrice?asset=SPX&date={api_date}&interval=1&symbol=-{option_type}{strike}"
                    
                    # In Trade-Results-Cache speichern
                    if handelsende_preis is not None:
                        self.trade_results_cache.cache_trade_results(
                            trade_id, api_date, option_type, int(strike),
                            handelsende_preis, peak_preis, peak_zeit, api_link
                        )
                    
                    results[idx] = {
                        'cached': False,
                        'handelsende_preis': handelsende_preis,
                        'peak_preis': peak_preis,
                        'peak_zeit': peak_zeit,
                        'api_link': api_link,
                        'api_cache_hit': response.cache_hit
                    }
                else:
                    self.logger.warning(f"Trade-ID {trade_id} nicht in trade_info_map gefunden")
            else:
                # Fehlerbehandlung
                trade_id = response.trade_id
                if trade_id in trade_info_map:
                    idx, _, _ = trade_info_map[trade_id]
                    results[idx] = {
                        'error': response.error or 'Unbekannter API-Fehler'
                    }
        
        return results
    
    def _process_api_response(self, api_response: List[Dict], trade: pd.Series, date_cols: List[str]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """Verarbeitet API-Antwort und extrahiert relevante Daten"""
        try:
            # Handelsende-Preis (22:00 oder letzter verfügbarer)
            handelsende_preis = None
            for data_point in api_response:
                if isinstance(data_point, dict):
                    time_str = data_point.get('time') or data_point.get('timestamp')
                    if time_str and '22:00' in str(time_str):
                        price_str = data_point.get('price') or data_point.get('value') or data_point.get('close')
                        if price_str:
                            try:
                                price_clean = str(price_str).strip().replace(',', '.').replace('$', '').replace(' ', '')
                                handelsende_preis = float(price_clean)
                                break
                            except (ValueError, TypeError):
                                continue
            
            # Fallback: Letzter verfügbarer Preis
            if not handelsende_preis and len(api_response) > 0:
                last_data = api_response[-1]
                if isinstance(last_data, dict):
                    price_str = last_data.get('price') or last_data.get('value') or last_data.get('close')
                    if price_str:
                        try:
                            price_clean = str(price_str).strip().replace(',', '.').replace('$', '').replace(' ', '')
                            handelsende_preis = float(price_clean)
                        except (ValueError, TypeError):
                            handelsende_preis = None
            
            # Peak-Berechnung
            peak_preis, peak_zeit = self._calculate_peak(api_response, trade, date_cols)
            
            return handelsende_preis, peak_preis, peak_zeit
            
        except Exception as e:
            return None, None, None
    
    def _calculate_peak(self, api_response: List[Dict], trade: pd.Series, date_cols: List[str]) -> Tuple[Optional[float], Optional[str]]:
        """Berechnet den Peak-Preis und die Peak-Zeit"""
        try:
            peak_data = []
            
            for data_point in api_response:
                if isinstance(data_point, dict):
                    data_time = data_point.get('dateTime') or data_point.get('time') or data_point.get('timestamp')
                    price = data_point.get('price') or data_point.get('value') or data_point.get('close')
                    
                    if data_time and isinstance(data_time, (int, float)) and price:
                        try:
                            price_str = str(price).strip().replace(',', '.').replace('$', '').replace(' ', '')
                            price_float = float(price_str)
                            
                            # UTC zu Bern-Zeit konvertieren
                            data_datetime_utc = datetime.datetime.utcfromtimestamp(data_time)
                            if data_datetime_utc.month in [3, 4, 5, 6, 7, 8, 9, 10]:
                                data_datetime_bern = data_datetime_utc + datetime.timedelta(hours=2)
                            else:
                                data_datetime_bern = data_datetime_utc + datetime.timedelta(hours=1)
                            
                            peak_data.append({
                                'timestamp': data_time,
                                'price': price_float,
                                'datetime_bern': data_datetime_bern
                            })
                        except (ValueError, TypeError):
                            continue
            
            if not peak_data:
                return None, None
            
            peak_df = pd.DataFrame(peak_data)
            
            # Nach Eröffnungszeit filtern
            trade_open_datetime = self._get_trade_open_datetime(trade, date_cols)
            if trade_open_datetime:
                peak_df_filtered = peak_df[peak_df['datetime_bern'] >= trade_open_datetime]
            else:
                peak_df_filtered = peak_df
            
            if len(peak_df_filtered) > 0:
                peak_idx = peak_df_filtered['price'].idxmin()
                peak_preis = peak_df_filtered.loc[peak_idx, 'price']
                peak_datetime_bern = peak_df_filtered.loc[peak_idx, 'datetime_bern']
                peak_zeit = peak_datetime_bern.strftime('%H:%M:%S')
                return peak_preis, peak_zeit
            
            return None, None
            
        except Exception as e:
            return None, None
    
    def _get_trade_open_datetime(self, trade: pd.Series, date_cols: List[str]) -> Optional[datetime.datetime]:
        """Ermittelt die Trade-Eröffnungszeit als datetime-Objekt"""
        try:
            trade_open_time_str = trade.get('🕐 Eröffnung', '')
            if not trade_open_time_str or not isinstance(trade_open_time_str, str) or ':' not in trade_open_time_str:
                return None
            
            trade_date_obj = trade[date_cols[0]]
            if not hasattr(trade_date_obj, 'date'):
                return None
            
            trade_date_only = trade_date_obj.date()
            trade_open_datetime = datetime.datetime.combine(
                trade_date_only, 
                datetime.datetime.strptime(trade_open_time_str, '%H:%M:%S').time()
            )
            
            return trade_open_datetime
            
        except Exception:
            return None

@monitor_function
def show_tat_navigator_page_optimized(data_loader, db_path):
    """Zeigt die optimierte TAT Tradenavigator-Seite an."""
    st.header("🎯 TAT Tradenavigator (Optimiert)")
    st.markdown("---")
    
    # Performance-Optimierer initialisieren
    optimizer = NavigatorPerformanceOptimizer()
    
    # CSS für schöne Metriken (vereinfacht)
    st.markdown("""
    <style>
        .metric-tile {
            background-color: #ffffff;
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            border: 1px solid #e9ecef;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            margin: 10px 0;
        }
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .neutral { color: #374151; }
    </style>
    """, unsafe_allow_html=True)
    
    # Cache-Status in der Sidebar (vereinfacht)
    with st.sidebar:
        st.markdown("**📊 Cache-Status**")
        
        # API-Cache Statistiken
        try:
            api_cache_stats = optimizer.api_cache.get_cache_stats()
            if api_cache_stats:
                st.metric("API-Cache Einträge", api_cache_stats.get('total_entries', 0))
                st.metric("API-Cache Größe", f"{api_cache_stats.get('total_size_mb', 0):.1f} MB")
        except Exception:
            st.info("API-Cache: Statistiken nicht verfügbar")
        
        st.markdown("---")
        
        # Trade-Cache Statistiken
        try:
            trade_cache_stats = optimizer.trade_results_cache.get_cache_stats()
            if trade_cache_stats:
                st.metric("Trade-Cache Einträge", trade_cache_stats.get('total_entries', 0))
                st.metric("Trade-Cache Größe", f"{trade_cache_stats.get('total_size_kb', 0):.1f} KB")
        except Exception:
            st.info("Trade-Cache: Statistiken nicht verfügbar")
        
        st.markdown("---")
        
        # Cache-Verwaltung
        if st.button("🧹 Caches bereinigen", use_container_width=True):
            try:
                deleted_api = optimizer.api_cache.clear_old_cache(30)
                deleted_trade = optimizer.trade_results_cache.clear_old_cache(60)
                st.success(f"✅ {deleted_api} API-Cache, {deleted_trade} Trade-Cache Einträge gelöscht")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Fehler beim Bereinigen: {e}")
    
    if not db_path:
        st.warning("⚠️ Bitte laden Sie zuerst eine Datenbank hoch oder geben Sie einen Pfad ein.")
        return
    
    try:
        # Lade Trade-Daten mit Performance-Monitoring
        with st.spinner("🔄 Lade Trade-Daten..."):
            trade_data = data_loader.load_trade_table(db_path)
        
        if trade_data is None or len(trade_data) == 0:
            st.error("❌ Keine Trade-Daten verfügbar.")
            return
        
        st.success(f"✅ {len(trade_data)} Trades geladen")
        
        # Intelligente Spaltenerkennung
        profit_cols = [col for col in trade_data.columns if 'profit' in col.lower() or 'pnl' in col.lower() or 'gewinn' in col.lower()]
        type_cols = [col for col in trade_data.columns if 'type' in col.lower() or 'typ' in col.lower()]
        date_cols = [col for col in trade_data.columns if 'date' in col.lower() or 'datum' in col.lower() or 'time' in col.lower() or 'opened' in col.lower() or 'closed' in col.lower()]
        strategy_cols = [col for col in trade_data.columns if 'strategy' in col.lower() or 'strategie' in col.lower()]
        
        # Datumsfilter (vereinfacht)
        if date_cols:
            with st.container():
                st.markdown("---")
                st.markdown("**🔍 Filter & Auswahl**")
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input(
                        "Von", 
                        value=st.session_state.get('start_date', None), 
                        key="start_date_input_nav_opt"
                    )
                    if start_date != st.session_state.get('start_date'):
                        st.session_state.start_date = start_date
                
                with col2:
                    end_date = st.date_input(
                        "Bis", 
                        value=st.session_state.get('end_date', None), 
                        key="end_date_input_nav_opt"
                    )
                    if end_date != st.session_state.get('end_date'):
                        st.session_state.end_date = end_date
                
                # Filter anwenden
                if st.button("🔍 Filter anwenden", type="primary", use_container_width=True):
                    if start_date and end_date:
                        if trade_data[date_cols[0]].dtype == 'object':
                            trade_data[date_cols[0]] = pd.to_datetime(trade_data[date_cols[0]], errors='coerce')
                        
                        if pd.api.types.is_datetime64_any_dtype(trade_data[date_cols[0]]):
                            start_datetime = pd.to_datetime(start_date)
                            end_datetime = pd.to_datetime(end_date)
                            
                            trade_data = trade_data[
                                (trade_data[date_cols[0]] >= start_datetime) & 
                                (trade_data[date_cols[0]] <= end_datetime)
                            ]
                            
                            st.success(f"✅ {len(trade_data)} Trades nach Datum gefiltert")
                        else:
                            st.error("❌ Datumsspalte konnte nicht als Datum interpretiert werden")
                    else:
                        st.warning("⚠️ Bitte wählen Sie Start- und Enddatum aus")
        
        # Trades vorbereiten
        if len(trade_data) > 0:
            display_trades = trade_data.copy()
            
            # Preisspalten bereinigen
            price_columns_raw = ['PriceOpen', 'PriceClose', 'PriceShort', 'PriceStopTarget']
            for raw_col in price_columns_raw:
                if raw_col in display_trades.columns:
                    display_trades[raw_col] = display_trades[raw_col].replace(['', 'None', 'nan', 'NaN'], pd.NA)
                    display_trades[raw_col] = pd.to_numeric(display_trades[raw_col], errors='coerce')
            
            # Falsche Trades entfernen
            if 'PriceOpen' in display_trades.columns:
                before_rows = len(display_trades)
                display_trades = display_trades[~(display_trades['PriceOpen'] == 0.0)]
                removed_rows = before_rows - len(display_trades)
                if removed_rows > 0:
                    st.info(f"🧹 {removed_rows} Trades mit Eröffnungspreis 0.0 entfernt")
            
            # Datum formatieren
            if date_cols:
                date_col = date_cols[0]
                display_trades['Date'] = display_trades[date_col].dt.strftime('%d.%m.%Y')
            
            # Neue Spalten für Optionspreise
            display_trades['📈 Optionspreis Handelsende'] = 'N/A'
            display_trades['📊 Peak'] = 'N/A'
            display_trades['🕐 Peak-Zeit'] = 'N/A'
            display_trades['🔗 API-Link'] = 'N/A'
            
            # Handelsende-Preise laden (Batch-Processing)
            st.markdown("---")
            st.subheader("📈 Optionspreis Handelsende (Batch-Processing)")
            
            if st.button("🚀 Handelsende-Preise laden", type="primary", use_container_width=True):
                with st.spinner("🔄 Lade Handelsende-Preise mit Batch-Processing..."):
                    # Trades in Batches aufteilen
                    trades_list = [(idx, trade, date_cols) for idx, trade in display_trades.iterrows()]
                    total_trades = len(trades_list)
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Batch-Processing
                    for i in range(0, total_trades, BATCH_SIZE):
                        batch = trades_list[i:i + BATCH_SIZE]
                        batch_num = i // BATCH_SIZE + 1
                        total_batches = (total_trades + BATCH_SIZE - 1) // BATCH_SIZE
                        
                        status_text.text(f"🔄 Verarbeite Batch {batch_num}/{total_batches} ({len(batch)} Trades)")
                        
                        # Batch parallel verarbeiten
                        batch_results = optimizer.batch_load_api_data(batch)
                        
                        # Ergebnisse in DataFrame eintragen
                        for idx, result in batch_results.items():
                            if 'error' not in result:
                                if result.get('handelsende_preis') is not None:
                                    display_trades.loc[idx, '📈 Optionspreis Handelsende'] = f"{result['handelsende_preis']:.3f}"
                                if result.get('peak_preis') is not None:
                                    display_trades.loc[idx, '📊 Peak'] = f"{result['peak_preis']:.3f}"
                                if result.get('peak_zeit'):
                                    display_trades.loc[idx, '🕐 Peak-Zeit'] = result['peak_zeit']
                                if result.get('api_link'):
                                    display_trades.loc[idx, '🔗 API-Link'] = result['api_link']
                            else:
                                display_trades.loc[idx, '📈 Optionspreis Handelsende'] = result['error']
                                display_trades.loc[idx, '📊 Peak'] = result['error']
                                display_trades.loc[idx, '🕐 Peak-Zeit'] = result['error']
                                display_trades.loc[idx, '🔗 API-Link'] = result['error']
                        
                        # Fortschritt aktualisieren
                        progress = min((i + BATCH_SIZE) / total_trades, 1.0)
                        progress_bar.progress(progress)
                        
                        # Kurze Pause zwischen Batches
                        time.sleep(0.05)
                    
                    progress_bar.empty()
                    status_text.empty()
                    st.success(f"✅ Handelsende-Preise für {total_trades} Trades geladen")
            
            # Metriken anzeigen
            st.markdown("---")
            st.markdown("**📊 Trading Übersicht**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_trades = len(display_trades)
                st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-value neutral">{total_trades}</div>
                    <div>TRADES</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if profit_cols and profit_cols[0] in display_trades.columns:
                    try:
                        total_pnl = display_trades[profit_cols[0]].sum()
                        pnl_class = 'negative' if total_pnl < 0 else 'positive'
                        st.markdown(f"""
                        <div class="metric-tile">
                            <div class="metric-value {pnl_class}">${total_pnl:,.2f}</div>
                            <div>P&L GESAMT</div>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception:
                        st.markdown(f"""
                        <div class="metric-tile">
                            <div class="metric-value neutral">Fehler</div>
                            <div>P&L GESAMT</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-value neutral">N/A</div>
                        <div>P&L GESAMT</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col3:
                # Status-Spalte finden
                status_col = None
                for col in display_trades.columns:
                    if 'Status' in col:
                        status_col = col
                        break
                
                if status_col:
                    stopped_trades = display_trades[
                        pd.to_numeric(display_trades[status_col], errors='coerce') == 2
                    ]
                    total_stopped = len(stopped_trades)
                    st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-value neutral">{total_stopped}</div>
                        <div>GESTOPPTE TRADES</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-value neutral">N/A</div>
                        <div>GESTOPPTE TRADES</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col4:
                # Cache-Hit-Rate
                cached_count = len(display_trades[
                    display_trades['📈 Optionspreis Handelsende'] != 'N/A'
                ])
                cache_rate = (cached_count / len(display_trades) * 100) if len(display_trades) > 0 else 0
                st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-value neutral">{cache_rate:.1f}%</div>
                    <div>CACHE-HIT RATE</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Tabelle anzeigen (vereinfacht)
            st.markdown("---")
            st.subheader("📋 Trade-Übersicht")
            
            # Wichtige Spalten für Anzeige
            display_columns = ['Date', '📈 Optionspreis Handelsende', '📊 Peak', '🕐 Peak-Zeit']
            
            # Zusätzliche Spalten hinzufügen falls verfügbar
            for col in ['PriceOpen', 'PriceClose', 'TradeType', 'Symbol', 'Status']:
                if col in display_trades.columns:
                    display_columns.append(col)
            
            # Tabelle anzeigen
            try:
                st.dataframe(
                    display_trades[display_columns],
                    use_container_width=True,
                    hide_index=True
                )
            except Exception as e:
                st.error(f"❌ Fehler beim Anzeigen der Tabelle: {e}")
            
            # Performance-Info
            with st.expander("📊 Performance-Informationen", expanded=False):
                st.info("🚀 **Performance-Optimierungen aktiviert:**")
                st.write("• **Batch-Processing**: API-Calls werden in Batches von 10 parallel verarbeitet")
                st.write("• **Intelligentes Caching**: Trade-Results werden zwischengespeichert")
                st.write("• **Connection Pooling**: Optimierte Datenbankverbindungen")
                st.write("• **Performance-Monitoring**: Alle Funktionen werden überwacht")
                st.write(f"• **Max. parallele API-Calls**: {MAX_CONCURRENT_API_CALLS}")
                st.write(f"• **Batch-Größe**: {BATCH_SIZE}")
                st.write(f"• **Cache-TTL**: {CACHE_TTL_HOURS} Stunden")
                
                # API-Optimizer Statistiken
                try:
                    api_stats = optimizer.api_optimizer.get_stats()
                    st.markdown("---")
                    st.markdown("**🔧 API-Optimizer Statistiken:**")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Gesamt-Requests", api_stats.get('total_requests', 0))
                        st.metric("Erfolgreiche Requests", api_stats.get('successful_requests', 0))
                    with col2:
                        st.metric("Fehlgeschlagene Requests", api_stats.get('failed_requests', 0))
                        st.metric("Cache-Hits", api_stats.get('cache_hits', 0))
                    with col3:
                        avg_time = api_stats.get('average_response_time', 0.0)
                        st.metric("Ø Response-Zeit", f"{avg_time:.3f}s")
                        
                        # Cache-Hit-Rate berechnen
                        total_req = api_stats.get('total_requests', 0)
                        cache_hits = api_stats.get('cache_hits', 0)
                        if total_req > 0:
                            hit_rate = (cache_hits / total_req) * 100
                            st.metric("Cache-Hit-Rate", f"{hit_rate:.1f}%")
                        else:
                            st.metric("Cache-Hit-Rate", "0%")
                    
                    # Performance-Tipps
                    if api_stats.get('total_requests', 0) > 0:
                        st.markdown("---")
                        st.markdown("**💡 Performance-Tipps:**")
                        
                        if api_stats.get('cache_hits', 0) > 0:
                            st.success("✅ Cache funktioniert gut - viele Requests werden aus dem Cache bedient")
                        
                        avg_time = api_stats.get('average_response_time', 0.0)
                        if avg_time > 1.0:
                            st.warning("⚠️ Durchschnittliche Response-Zeit ist hoch - prüfe API-Verbindung")
                        elif avg_time < 0.5:
                            st.success("✅ Sehr gute Response-Zeiten - API läuft optimal")
                        
                        failed_rate = (api_stats.get('failed_requests', 0) / api_stats.get('total_requests', 1)) * 100
                        if failed_rate > 10:
                            st.error(f"❌ Hohe Fehlerrate ({failed_rate:.1f}%) - prüfe API-Verbindung")
                        elif failed_rate < 5:
                            st.success("✅ Niedrige Fehlerrate - API läuft stabil")
                
                except Exception as e:
                    st.warning(f"⚠️ Konnte API-Optimizer-Statistiken nicht laden: {e}")
            
            # API-Test Button
            if st.button("🧪 API-Verbindung testen", key="api_test_opt"):
                test_api_connection()
        
        else:
            st.warning("⚠️ Keine gefilterten Trades gefunden!")
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der TAT Tradenavigator-Seite: {e}")
        st.info("💡 Bitte stellen Sie sicher, dass die Trade-Tabelle verfügbar ist.")

# Fallback-Funktion für Kompatibilität
def show_tat_navigator_page(data_loader, db_path):
    """Fallback zur optimierten Version"""
    return show_tat_navigator_page_optimized(data_loader, db_path)
