"""
Navigator Page Module für Tradelog Dashboard
Zeigt die TAT Navigator-Seite mit Navigation und Charts
"""

import streamlit as st
import pandas as pd
import datetime
import time
from pathlib import Path
from modules.api_charts import (
    get_option_price_data, 
    get_spx_vix_data, 
    create_options_price_chart, 
    create_spx_vix_chart,
    test_api_connection
)
from .api_cache import get_cache_instance
from .trade_results_cache import get_trade_results_cache

def show_tat_navigator_page(data_loader, db_path):
    """Zeigt die TAT Tradenavigator-Seite an."""
    st.header("🎯 TAT Tradenavigator")
    st.markdown("---")
    
    # CSS für schöne Metrikkacheln (wie auf der Metrikseite)
    st.markdown("""
    <style>
        .metric-tile {
            background-color: #ffffff;
            border-radius: 15px;
            padding: 25px;
            margin: 15px 0;
            border: 1px solid #e9ecef;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            color: #374151;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .metric-tile:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        }
        .metric-header {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 20px;
        }
        .metric-icon {
            font-size: 32px;
            margin-bottom: 10px;
        }
        .metric-title {
            font-size: 16px;
            font-weight: 600;
            color: #374151;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            margin: 15px 0;
        }
        .metric-description {
            font-size: 13px;
            color: #6c757d;
            font-style: normal;
            line-height: 1.4;
        }
        .positive { 
            color: #28a745; 
        }
        .negative { 
            color: #dc3545; 
        }
        .neutral { 
            color: #374151; 
        }
        .metric-section {
            margin: 40px 0;
        }
        .metric-section h3 {
            color: #374151;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 25px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Beide Caches initialisieren
    api_cache = get_cache_instance()
    trade_results_cache = get_trade_results_cache()
    
    # Cache-Statistiken in der Sidebar anzeigen
    with st.sidebar:
        st.markdown("**📊 Cache-Status**")
        
        # API-Cache Statistiken
        try:
            api_cache_stats = api_cache.get_cache_stats()
            
            if api_cache_stats:
                st.markdown("**🗄️ API-Cache**")
                
                # Robuste Behandlung verschiedener Rückgabetypen
                if isinstance(api_cache_stats, dict):
                    # Standard Dictionary-Format
                    stats = api_cache_stats
                elif isinstance(api_cache_stats, tuple):
                    # Tuple-Format - konvertiere zu Dictionary
                    try:
                        if hasattr(api_cache_stats, '_asdict'):
                            # Named Tuple
                            stats = dict(api_cache_stats._asdict())
                        else:
                            # Reguläres Tuple
                            if len(api_cache_stats) >= 4:
                                stats = {
                                    'total_entries': api_cache_stats[0] if api_cache_stats[0] is not None else 0,
                                    'total_size_mb': api_cache_stats[1] if api_cache_stats[1] is not None else 0,
                                    'recent_entries': api_cache_stats[2] if api_cache_stats[2] is not None else 0,
                                    'top_entries': api_cache_stats[3] if api_cache_stats[3] is not None else []
                                }
                            else:
                                stats = {}
                    except Exception as conv_error:
                        st.error(f"❌ Konvertierungsfehler: {conv_error}")
                        stats = {}
                else:
                    # Unbekannter Typ
                    st.error(f"❌ Unbekannter Rückgabetyp: {type(api_cache_stats)}")
                    stats = {}
                
                # Zeige Statistiken an
                if stats:
                    col1, col2 = st.columns(2)
                    with col1:
                        total_entries = stats.get('total_entries', 0)
                        st.metric("Einträge", f"{total_entries}")
                    with col2:
                        total_size_mb = stats.get('total_size_mb', 0)
                        st.metric("Größe", f"{total_size_mb:.1f} MB")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        recent_entries = stats.get('recent_entries', 0)
                        st.metric("Letzte 7 Tage", f"{recent_entries}")
                    with col2:
                        top_entries = stats.get('top_entries', [])
                        if top_entries and len(top_entries) > 0:
                            if isinstance(top_entries[0], dict):
                                # Dictionary-Format
                                top_entry = top_entries[0]
                                size_kb = top_entry.get('size_kb', 0)
                            else:
                                # Tuple-Format
                                size_kb = top_entries[0] if isinstance(top_entries[0], (int, float)) else 0
                            st.metric("Top Entry", f"{size_kb:.1f} KB")
                        else:
                            st.metric("Top Entry", "N/A")
                else:
                    st.info("🗄️ API-Cache: Keine gültigen Statistiken verfügbar")
            else:
                st.info("🗄️ API-Cache: Keine Statistiken verfügbar")
        except Exception as e:
            st.error(f"❌ API-Cache Fehler: {str(e)}")
            st.info("🗄️ API-Cache: Fehler beim Laden der Statistiken")
        
        st.markdown("---")
        
        # Trade-Cache Statistiken
        try:
            trade_cache_stats = trade_results_cache.get_cache_stats()
            
            if trade_cache_stats:
                st.markdown("**⚡ Trade-Cache**")
                
                # Robuste Behandlung verschiedener Rückgabetypen
                if isinstance(trade_cache_stats, dict):
                    # Standard Dictionary-Format
                    stats = trade_cache_stats
                elif isinstance(trade_cache_stats, tuple):
                    # Tuple-Format - konvertiere zu Dictionary
                    try:
                        if hasattr(trade_cache_stats, '_asdict'):
                            # Named Tuple
                            stats = dict(trade_cache_stats._asdict())
                        else:
                            # Reguläres Tuple
                            if len(trade_cache_stats) >= 4:
                                stats = {
                                    'total_entries': trade_cache_stats[0] if trade_cache_stats[0] is not None else 0,
                                    'total_size_kb': trade_cache_stats[1] if trade_cache_stats[1] is not None else 0,
                                    'recent_entries': trade_cache_stats[2] if trade_cache_stats[2] is not None else 0,
                                    'top_entries': trade_cache_stats[3] if trade_cache_stats[3] is not None else []
                                }
                            else:
                                stats = {}
                    except Exception as conv_error:
                        st.error(f"❌ Trade-Cache Konvertierungsfehler: {conv_error}")
                        stats = {}
                else:
                    # Unbekannter Typ
                    st.error(f"❌ Trade-Cache unbekannter Rückgabetyp: {type(trade_cache_stats)}")
                    stats = {}
                
                # Zeige Statistiken an
                if stats:
                    col1, col2 = st.columns(2)
                    with col1:
                        total_entries = stats.get('total_entries', 0)
                        st.metric("Einträge", f"{total_entries}")
                    with col2:
                        total_size_kb = stats.get('total_size_kb', 0)
                        st.metric("Größe", f"{total_size_kb:.1f} KB")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        recent_entries = stats.get('recent_entries', 0)
                        st.metric("Letzte 30 Tage", f"{recent_entries}")
                    with col2:
                        top_entries = stats.get('top_entries', [])
                        if top_entries and len(top_entries) > 0:
                            if isinstance(top_entries[0], dict):
                                # Dictionary-Format
                                top_entry = top_entries[0]
                                size_kb = top_entry.get('size_kb', 0)
                            else:
                                # Tuple-Format
                                size_kb = top_entries[0] if isinstance(top_entries[0], (int, float)) else 0
                            st.metric("Top Entry", f"{size_kb:.1f} KB")
                        else:
                            st.metric("Top Entry", "N/A")
                else:
                    st.info("⚡ Trade-Cache: Keine gültigen Statistiken verfügbar")
            else:
                st.info("⚡ Trade-Cache: Keine Statistiken verfügbar")
        except Exception as e:
            st.error(f"❌ Trade-Cache Fehler: {str(e)}")
            st.info("⚡ Trade-Cache: Fehler beim Laden der Statistiken")
        
        st.markdown("---")
        
        # Cache-Verwaltung
        st.markdown("**🛠️ Cache-Verwaltung**")
        
        # API-Cache Verwaltung
        if st.button("🧹 API-Cache bereinigen (30+ Tage)", 
                    help="Löscht API-Cache-Einträge älter als 30 Tage",
                    use_container_width=True):
            deleted_count = api_cache.clear_old_cache(30)
            st.success(f"✅ {deleted_count} API-Cache-Einträge gelöscht")
            st.rerun()
        
        if st.button("🗑️ API-Cache löschen", 
                    help="Löscht alle API-Cache-Einträge",
                    use_container_width=True):
            deleted_count = api_cache.clear_all_cache()
            st.success(f"✅ {deleted_count} API-Cache-Einträge gelöscht")
            st.rerun()
        
        # Trade-Cache Verwaltung
        if st.button("🧹 Trade-Cache bereinigen (60+ Tage)", 
                    help="Löscht Trade-Cache-Einträge älter als 60 Tage",
                    use_container_width=True):
            deleted_count = trade_results_cache.clear_old_cache(60)
            st.success(f"✅ {deleted_count} Trade-Cache-Einträge gelöscht")
            st.rerun()
        
        if st.button("🗑️ Trade-Cache löschen", 
                    help="Löscht alle Trade-Cache-Einträge",
                    use_container_width=True):
            deleted_count = trade_results_cache.clear_all_cache()
            st.success(f"✅ {deleted_count} Trade-Cache-Einträge gelöscht")
            st.rerun()
        
        st.markdown("---")
    
    if not db_path:
        st.warning("⚠️ Bitte laden Sie zuerst eine Datenbank hoch oder geben Sie einen Pfad ein.")
        return
    
    try:
        # Lade Trade-Daten
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
        
        # Datumsfilter
        if date_cols:
            with st.container():
                st.markdown("---")
                st.markdown("**🔍 Filter & Auswahl**")
                
                # Datum-Eingaben
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input(
                        "Von", 
                        value=st.session_state.get('start_date', None), 
                        key="start_date_input_nav",
                        label_visibility="collapsed", 
                        help="Startdatum"
                    )
                    if start_date != st.session_state.get('start_date'):
                        st.session_state.start_date = start_date
                with col2:
                    end_date = st.date_input(
                        "Bis", 
                        value=st.session_state.get('end_date', None), 
                        key="end_date_input_nav",
                        label_visibility="collapsed", 
                        help="Enddatum"
                    )
                    if end_date != st.session_state.get('end_date'):
                        st.session_state.end_date = end_date
                
                # Filter: Trade Type und Strategy
                col_filter1, col_filter2 = st.columns(2)
                
                with col_filter1:
                    if type_cols:
                        type_col = type_cols[0]
                        available_types = sorted(trade_data[type_col].dropna().unique())
                        selected_types = st.multiselect(
                            "Trade Type:",
                            options=available_types,
                            default=available_types,
                            help="Wählen Sie die gewünschten Trade-Typen"
                        )
                    else:
                        selected_types = []
                
                with col_filter2:
                    if strategy_cols:
                        strategy_col = strategy_cols[0]
                        available_strategies = sorted(trade_data[strategy_col].dropna().unique())
                        selected_strategies = st.multiselect(
                            "Strategy:",
                            options=available_strategies,
                            default=available_strategies,
                            help="Wählen Sie die gewünschten Strategien"
                        )
                    else:
                        selected_strategies = []
                
                # Zusätzliche Filter
                col_filter3, col_filter4, col_filter5 = st.columns(3)
                
                with col_filter3:
                    # Optionspreis Handelsende Filter (Profitable Short-Optionen)
                    filter_profitable_options = st.checkbox(
                        "✅ Nur profitable Short-Optionen (Opening > Handelsende)",
                        value=st.session_state.get('filter_profitable_options', False),
                        help="Zeigt nur Trades, bei denen die verkaufte Option wertlos geworden ist (Eröffnungspreis > Handelsende-Preis = Gewinn)"
                    )
                    if filter_profitable_options != st.session_state.get('filter_profitable_options', False):
                        st.session_state.filter_profitable_options = filter_profitable_options
                
                with col_filter4:
                    # Optionspreis Handelsende Filter (Nicht profitable Short-Optionen)
                    filter_unprofitable_options = st.checkbox(
                        "❌ Nur nicht profitable Short-Optionen (Handelsende > Opening)",
                        value=st.session_state.get('filter_unprofitable_options', False),
                        help="Zeigt nur Trades, bei denen die verkaufte Option teurer geworden ist (Handelsende-Preis > Eröffnungspreis = Verlust)"
                    )
                    if filter_unprofitable_options != st.session_state.get('filter_unprofitable_options', False):
                        st.session_state.filter_unprofitable_options = filter_unprofitable_options
                
                with col_filter5:
                    # Status Filter - Session State zurücksetzen falls alte Werte vorhanden
                    if 'status_filter' in st.session_state:
                        old_values = st.session_state.status_filter
                        if old_values and isinstance(old_values[0], tuple) and isinstance(old_values[0][0], str):
                            # Alte String-Werte gefunden, zurücksetzen
                            st.session_state.status_filter = []
                    
                    status_filter = st.multiselect(
                        "📊 Status Filter:",
                        options=[
                            (2, "2 = Stopped"),
                            (4, "4 = Expired")
                        ],
                        default=st.session_state.get('status_filter', []),
                        format_func=lambda x: x[1],
                        help="Wählen Sie die gewünschten Status-Werte"
                    )
                    if status_filter != st.session_state.get('status_filter', []):
                        st.session_state.status_filter = status_filter
                
                # Filter-Buttons
                col_apply, col_reset = st.columns([3, 1])
                with col_apply:
                    if st.button("🔍 Alle Filter anwenden", type="primary", use_container_width=True, key="apply_filters_nav"):
                        st.session_state.filters_applied_nav = True
                        st.rerun()
                
                with col_reset:
                    if st.button("🔄 Reset", use_container_width=True, key="reset_filters_nav"):
                        st.session_state.start_date = None
                        st.session_state.end_date = None
                        st.session_state.filter_profitable_options = False
                        st.session_state.filter_unprofitable_options = False
                        st.session_state.pending_profitable_filter = False
                        st.session_state.pending_unprofitable_filter = False
                        st.session_state.status_filter = []
                        st.session_state.filters_applied_nav = False
                        st.rerun()
                
                # Filter anwenden
                if st.session_state.get('filters_applied_nav', False):
                    if trade_data[date_cols[0]].dtype == 'object':
                        trade_data[date_cols[0]] = pd.to_datetime(trade_data[date_cols[0]], errors='coerce')
                    
                    if pd.api.types.is_datetime64_any_dtype(trade_data[date_cols[0]]):
                        trade_data_filtered = trade_data.copy()
                        filter_description = ""
                        
                        start_date = st.session_state.get('start_date')
                        end_date = st.session_state.get('end_date')
                        
                        if start_date and end_date:
                            start_datetime = pd.to_datetime(start_date)
                            end_datetime = pd.to_datetime(end_date)
                            
                            trade_data_filtered = trade_data_filtered[
                                (trade_data_filtered[date_cols[0]] >= start_datetime) & 
                                (trade_data_filtered[date_cols[0]] <= end_datetime)
                            ]
                            
                            filter_description = f"Datum: {start_date} bis {end_date}"
                        else:
                            st.warning("⚠️ Bitte wählen Sie Start- und Enddatum aus")
                            st.session_state.filters_applied_nav = False
                            return
                        
                        # Trade Type Filter
                        if selected_types and type_cols:
                            trade_data_filtered = trade_data_filtered[trade_data_filtered[type_cols[0]].isin(selected_types)]
                            if filter_description:
                                filter_description += f" | Type: {len(selected_types)}"
                            else:
                                filter_description = f"Type: {len(selected_types)}"
                        
                        # Strategy Filter
                        if selected_strategies and strategy_cols:
                            trade_data_filtered = trade_data_filtered[trade_data_filtered[strategy_cols[0]].isin(selected_strategies)]
                            if filter_description:
                                filter_description += f" | Strategy: {len(selected_strategies)}"
                            else:
                                filter_description = f"Strategy: {len(selected_strategies)}"
                        
                        # Status Filter
                        if st.session_state.get('status_filter', []):
                            selected_status_values = [item[0] for item in st.session_state.status_filter]
                            # Suche nach Status-Spalte (mit oder ohne Emoji)
                            status_col = None
                            for col in trade_data_filtered.columns:
                                if 'Status' in col:
                                    status_col = col
                                    break
                            
                            if status_col:
                                # Konvertiere Status-Spalte zu numerischen Werten für Vergleich
                                trade_data_filtered = trade_data_filtered[
                                    pd.to_numeric(trade_data_filtered[status_col], errors='coerce').isin(selected_status_values)
                                ]
                                if filter_description:
                                    filter_description += f" | Status: {len(selected_status_values)}"
                                else:
                                    filter_description = f"Status: {len(selected_status_values)}"
                        
                        # Optionspreis Handelsende Filter (Profitable/Nicht profitable)
                        if st.session_state.get('filter_profitable_options', False):
                            # Markiere für späteren Filter (nach dem Laden der Handelsende-Preise)
                            st.session_state.pending_profitable_filter = True
                            if filter_description:
                                filter_description += " | Profitable Short-Optionen (wird nach Handelsende-Preisen angewendet)"
                            else:
                                filter_description = "Profitable Short-Optionen (wird nach Handelsende-Preisen angewendet)"
                        
                        if st.session_state.get('filter_unprofitable_options', False):
                            # Markiere für späteren Filter (nach dem Laden der Handelsende-Preise)
                            st.session_state.pending_unprofitable_filter = True
                            if filter_description:
                                filter_description += " | Nicht profitable Short-Optionen (wird nach Handelsende-Preisen angewendet)"
                            else:
                                filter_description = "Nicht profitable Short-Optionen (wird nach Handelsende-Preisen angewendet)"
                        
                        # Filter-Ergebnis
                        if len(trade_data_filtered) > 0:
                            st.success(f"✅ {len(trade_data_filtered)} Trades gefunden: {filter_description}")
                            trade_data = trade_data_filtered
                        else:
                            st.warning(f"⚠️ Keine Trades gefunden")
                            st.session_state.filters_applied_nav = False
                            return
                    else:
                        st.error(f"❌ Datumsspalte konnte nicht als Datum interpretiert werden")
                        st.session_state.filters_applied_nav = False
                
                st.markdown("---")
        
        # Session State für ausgewählte Zeile
        if 'selected_row_index' not in st.session_state:
            st.session_state.selected_row_index = None
        
        # Trades anzeigen
        if len(trade_data) > 0:
            # Tabelle vorbereiten
            display_trades = trade_data.copy()
            
            # Preisspalten für Arrow/Streamlit bereinigen und numerisch konvertieren
            price_columns_raw = ['PriceOpen', 'PriceClose', 'PriceShort', 'PriceStopTarget']
            for raw_col in price_columns_raw:
                if raw_col in display_trades.columns:
                    display_trades[raw_col] = display_trades[raw_col].replace(['', 'None', 'nan', 'NaN'], pd.NA)
                    display_trades[raw_col] = pd.to_numeric(display_trades[raw_col], errors='coerce')
            
            # Quantity numerisch erzwingen
            if 'Qty' in display_trades.columns:
                display_trades['Qty'] = display_trades['Qty'].replace(['', 'None', 'nan', 'NaN'], pd.NA)
                display_trades['Qty'] = pd.to_numeric(display_trades['Qty'], errors='coerce')
            
            # Profit/P&L-Spalte numerisch machen (für Anzeige und Aggregation)
            if profit_cols:
                try:
                    display_trades[profit_cols[0]] = display_trades[profit_cols[0]].replace(['', 'None', 'nan', 'NaN'], pd.NA)
                    display_trades[profit_cols[0]] = pd.to_numeric(display_trades[profit_cols[0]], errors='coerce')
                except Exception:
                    pass
            
            # Falsche Trades entfernen: PriceOpen == 0.0
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
            
            # Eröffnungszeit formatieren
            if 'DateOpened' in display_trades.columns:
                display_trades['TimeOnly'] = display_trades['DateOpened'].apply(
                    lambda x: x.strftime('%H:%M:%S') if pd.notna(x) and hasattr(x, 'strftime') else str(x)[-8:] if pd.notna(x) and len(str(x)) >= 8 else str(x)
                )
            
            # Schließungszeit formatieren
            if 'DateClosed' in display_trades.columns:
                display_trades['TimeClosedOnly'] = display_trades['DateClosed'].apply(
                    lambda x: x.strftime('%H:%M:%S') if pd.notna(x) and hasattr(x, 'strftime') else str(x)[-8:] if pd.notna(x) and len(str(x)) >= 8 else str(x)
                )
            
            # Metriken werden nach dem Anwenden des Optionspreis-Filters berechnet
            # (siehe weiter unten nach dem Laden der Handelsende-Preise)
            
            # Überschrift für Tabelle
            st.subheader(f"📋 Alle gefilterten Trades")
            
            # P&L formatieren
            if profit_cols:
                pnl_col = profit_cols[0]
                display_trades['P&L_Display'] = display_trades[pnl_col].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                )
                

            
            # Strike-Preis-Spalten
            strike_columns = []
            
            if 'ShortPut' in display_trades.columns:
                display_trades['🎯 Short Put Strike'] = display_trades['ShortPut'].apply(
                    lambda x: f"{x:.0f}" if pd.notna(x) and x != 0 else "N/A"
                )
                strike_columns.append('🎯 Short Put Strike')
            
            if 'ShortCall' in display_trades.columns:
                display_trades['🎯 Short Call Strike'] = display_trades['ShortCall'].apply(
                    lambda x: f"{x:.0f}" if pd.notna(x) and x != 0 else "N/A"
                )
                strike_columns.append('🎯 Short Call Strike')
            
            # Spalten umbenennen
            column_mapping = {
                'Date': '📅 Datum',
                'TimeOnly': '🕐 Eröffnung',
                'PriceOpen': '💰 Preis Eröffnung',
                'PriceStopTarget': '🎯 Stop/Target',
                'TimeClosedOnly': '🕐 Schließung',
                'PriceClose': '💰 Preis Schließung',
                'TradeType': '📊 Trade Type',
                'Symbol': '🏷️ Symbol',
                'Status': '📈 Status',
                'Commission': '💰 Kommission'
            }
            
            if 'Qty' in display_trades.columns:
                column_mapping['Qty'] = '📦 Quantity'
            
            if profit_cols:
                display_trades = display_trades.rename(columns={profit_cols[0]: '💰 P&L'})
            
            for old_name, new_name in column_mapping.items():
                if old_name in display_trades.columns:
                    display_trades = display_trades.rename(columns={old_name: new_name})
            
            # Wichtige Spalten für Anzeige
            display_columns = []
            for col in ['📅 Datum', '🕐 Eröffnung', '💰 Preis Eröffnung', '🎯 Stop/Target', '🕐 Schließung', '💰 Preis Schließung', '📊 Trade Type', '📦 Quantity', '💰 P&L', '📈 Status']:
                if col in display_trades.columns:
                    display_columns.append(col)
            
            # Neue Spalte: Optionspreis Handelsende immer hinzufügen
            display_trades['📈 Optionspreis Handelsende'] = 'N/A'
            display_columns.insert(8, '📈 Optionspreis Handelsende')
            
            # Neue Spalte: Peak (höchster Optionspreis) hinzufügen
            display_trades['📊 Peak'] = 'N/A'
            display_columns.insert(9, '📊 Peak')
            
            # Neue Spalte: Peak-Zeit hinzufügen
            display_trades['🕐 Peak-Zeit'] = 'N/A'
            display_columns.insert(10, '🕐 Peak-Zeit')
            
            # Neue Spalte: API-Link hinzufügen
            display_trades['🔗 API-Link'] = 'N/A'
            display_columns.insert(11, '🔗 API-Link')
            

            
            # Neue Spalte: Commission (Comission + CommissionClose) hinzufügen
            try:
                # Suche nach den ursprünglichen Commission-Spalten in den Rohdaten
                commission_cols = []
                for col in trade_data.columns:
                    if 'commission' in col.lower() or 'comission' in col.lower():
                        commission_cols.append(col)
                
                if commission_cols:
                    # Commission-Werte kombinieren
                    combined_commission = pd.Series(0.0, index=display_trades.index)
                    
                    for col in commission_cols:
                        if col in trade_data.columns:
                            # Werte zu numerischen Werten konvertieren und zu combined_commission addieren
                            col_values = pd.to_numeric(trade_data[col], errors='coerce').fillna(0)
                            # Nur die Zeilen hinzufügen, die in display_trades vorhanden sind
                            if len(col_values) == len(display_trades):
                                combined_commission += col_values
                            else:
                                # Fallback: Verwende den ursprünglichen Index
                                for idx in display_trades.index:
                                    if idx in trade_data.index:
                                        combined_commission.loc[idx] += col_values.get(idx, 0)
                    
                    # Formatierung: 2 Dezimalstellen für Commission
                    formatted_commission = []
                    for comm in combined_commission:
                        if pd.isna(comm) or comm == 0:
                            formatted_commission.append('0.00')
                        else:
                            formatted_commission.append(f"{comm:.2f}")
                    
                    display_trades['💰 Commission'] = formatted_commission
                    display_columns.insert(13, '💰 Commission')
                    
                else:
                    st.warning("⚠️ Keine Commission-Spalten in den Trade-Daten gefunden")
                    display_trades['💰 Commission'] = 'N/A'
                    display_columns.insert(13, '💰 Commission')
                    
            except Exception as e:
                st.warning(f"⚠️ Konnte Commission-Spalte nicht hinzufügen: {e}")
                display_trades['💰 Commission'] = 'N/A'
                display_columns.insert(13, '💰 Commission')
            
            # Handelsende-Preis-Berechnung (immer ausführen)
            st.markdown("---")
            st.subheader("📈 Optionspreis Handelsende")
            
            # Optionspreis-Filter anwenden (falls aktiviert)
            if st.session_state.get('pending_profitable_filter', False) and st.session_state.get('filter_profitable_options', False):
                st.info("🎯 Filtere nach profitablen Short-Optionen (Opening > Handelsende)...")
                st.session_state.pending_profitable_filter = False  # Zurücksetzen
            elif st.session_state.get('pending_unprofitable_filter', False) and st.session_state.get('filter_unprofitable_options', False):
                st.info("🎯 Filtere nach nicht profitablen Short-Optionen (Handelsende > Opening)...")
                st.session_state.pending_unprofitable_filter = False  # Zurücksetzen
            
            st.info(f"🔄 Lade Handelsende-Preise für alle {len(display_trades)} Trades...")
            
            # Debug: Nur wichtige Informationen (Browser nicht überlasten)

            # Trade-Auswahl basierend auf Test-Modus
            # Alle Trades laden
            selected_trades = display_trades
            
            # Für jeden Trade Handelsende-Preis abrufen
            progress_bar = st.progress(0)
            total_trades = len(selected_trades)
            
            for i, (idx, trade) in enumerate(selected_trades.iterrows()):
                progress = (i + 1) / total_trades
                progress_bar.progress(progress)
                
                try:
                    # Strike und Optionstyp ermitteln (ohne Debug-Ausgaben)
                    strike = None
                    option_type = None
                    
                    if 'ShortPut' in trade and pd.notna(trade['ShortPut']) and trade['ShortPut'] != 0:
                        strike = int(trade['ShortPut'])
                        option_type = 'P'
                    elif 'ShortCall' in trade and pd.notna(trade['ShortCall']) and trade['ShortCall'] != 0:
                        strike = int(trade['ShortCall'])
                        option_type = 'C'
                    else:
                        strike = None
                        option_type = None
                    
                    if strike and option_type and date_cols:
                        trade_date = trade[date_cols[0]]
                        if hasattr(trade_date, 'strftime'):
                            api_date = trade_date.strftime('%Y-%m-%d')
                            
                            # Eindeutige Trade-ID erstellen
                            trade_id = f"{api_date}_{option_type}{strike}_{idx}"
                            
                            # PRÜFE ZUERST DEN TRADE-RESULTS-CACHE (schnellste Option)
                            cached_results = trade_results_cache.get_cached_results(trade_id, api_date, option_type, strike)
                            
                            if cached_results:
                                # ✅ Alle Werte sind bereits berechnet - sofort setzen
                                display_trades.loc[idx, '🔗 API-Link'] = cached_results['api_link']
                                display_trades.loc[idx, '📈 Optionspreis Handelsende'] = f"{cached_results['handelsende_preis']:.3f}"
                                display_trades.loc[idx, '📊 Peak'] = f"{cached_results['peak_preis']:.3f}"
                                display_trades.loc[idx, '🕐 Peak-Zeit'] = cached_results['peak_zeit']
                                continue  # Nächster Trade
                            
                            # API-Link für diesen Trade erstellen
                            api_link = f"https://api.0dtespx.com/optionPrice?asset=SPX&date={api_date}&interval=1&symbol=-{option_type}{strike}"
                            display_trades.loc[idx, '🔗 API-Link'] = api_link
                            
                            # API-Call mit API-Cache-Unterstützung
                            try:
                                # Prüfe zuerst den API-Cache
                                cached_response = api_cache.get_cached_price('SPX', api_date, option_type, strike)
                                
                                if cached_response:
                                    # Verwende gecachte API-Daten
                                    api_response = cached_response
                                    api_cache_hit = True
                                else:
                                    # API-Call durchführen
                                    api_response = get_option_price_data('SPX', api_date, option_type, strike)
                                    api_cache_hit = False
                                    
                                    # Speichere in API-Cache (falls erfolgreich)
                                    if api_response and isinstance(api_response, list) and len(api_response) > 0:
                                        api_cache.cache_price_data('SPX', api_date, option_type, strike, api_response)
                                


                                
                                # API-Antwort überprüfen
                                if api_response and isinstance(api_response, list) and len(api_response) > 0:
                                    


                                    
                                                                        # Verfallpreis wird nicht mehr benötigt - entfernt
                                    
                                    # Optionspreis Handelsende (22:00 oder letzter verfügbarer)
                                    handelsende_preis = None
                                    
                                    # Suche nach 22:00 Uhr Preis
                                    for data_point in api_response:
                                        if isinstance(data_point, dict):
                                            time_str = data_point.get('time') or data_point.get('timestamp')
                                            if time_str and '22:00' in str(time_str):
                                                price_str = data_point.get('price') or data_point.get('value') or data_point.get('close')
                                                if price_str:
                                                    try:
                                                        # String zu Float konvertieren und Format-Probleme beheben
                                                        price_clean = str(price_str).strip()
                                                        price_clean = price_clean.replace(',', '.').replace('$', '').replace(' ', '')
                                                        handelsende_preis = float(price_clean)
                                                        break
                                                    except (ValueError, TypeError):
                                                        continue
                                    
                                    # Wenn kein 22:00 Preis, nimm den letzten verfügbaren
                                    if not handelsende_preis and len(api_response) > 0:
                                        last_data = api_response[-1]
                                        if isinstance(last_data, dict):
                                            price_str = last_data.get('price') or last_data.get('value') or last_data.get('close')
                                            if price_str:
                                                try:
                                                    # String zu Float konvertieren und Format-Probleme beheben
                                                    price_clean = str(price_str).strip()
                                                    price_clean = price_clean.replace(',', '.').replace('$', '').replace(' ', '')
                                                    handelsende_preis = float(price_clean)
                                                except (ValueError, TypeError):
                                                    handelsende_preis = None
                                    
                                    # Setze Handelsende-Preis
                                    if handelsende_preis is not None:
                                        display_trades.loc[idx, '📈 Optionspreis Handelsende'] = f"{handelsende_preis:.3f}"
                                    else:
                                        display_trades.loc[idx, '📈 Optionspreis Handelsende'] = 'Keine Daten'
                                    
                                    # Peak (höchster Optionspreis) berechnen - Max-Wert aus allen Datenpunkten
                                    peak_preis = None
                                    

                                    
                                                                        # STABILE PEAK-FINDER FUNKTION
                                    # 1. Alle API-Datenpunkte in DataFrame laden
                                    peak_data = []
                                    
                                    for data_point in api_response:
                                        if isinstance(data_point, dict):
                                            # Zeitstempel des API-Datenpunkts
                                            data_time = data_point.get('dateTime') or data_point.get('time') or data_point.get('timestamp')
                                            price = data_point.get('price') or data_point.get('value') or data_point.get('close')
                                            
                                            if data_time and isinstance(data_time, (int, float)) and price:
                                                try:
                                                    # String zu Float konvertieren
                                                    price_str = str(price).strip()
                                                    price_str = price_str.replace(',', '.').replace('$', '').replace(' ', '')
                                                    price_float = float(price_str)
                                                    
                                                    # API-Zeitstempel ist UTC, konvertiere zu UTC datetime
                                                    data_datetime_utc = datetime.datetime.utcfromtimestamp(data_time)
                                                    
                                                    # Konvertiere API-UTC-Zeit zu Bern-Zeit
                                                    if data_datetime_utc.month in [3, 4, 5, 6, 7, 8, 9, 10]:
                                                        data_datetime_bern = data_datetime_utc + datetime.timedelta(hours=2)  # Sommer (CEST)
                                                    else:
                                                        data_datetime_bern = data_datetime_utc + datetime.timedelta(hours=1)  # Winter (CET)
                                                    
                                                    # Datenpunkt zum DataFrame hinzufügen
                                                    peak_data.append({
                                                        'timestamp': data_time,
                                                        'price': price_float,
                                                        'datetime_bern': data_datetime_bern,
                                                        'datetime_utc': data_datetime_utc
                                                    })
                                                except (ValueError, TypeError):
                                                    continue
                                    
                                    # 2. DataFrame erstellen
                                    if peak_data:
                                        peak_df = pd.DataFrame(peak_data)
                                        

                                        
                                        # 3. Nach Eröffnungszeit filtern (falls verfügbar)
                                        trade_open_datetime = None
                                        trade_open_time_str = trade.get('🕐 Eröffnung', '')
                                        
                                        if trade_open_time_str and isinstance(trade_open_time_str, str) and ':' in trade_open_time_str:
                                            # Trade-Eröffnungszeit zu datetime konvertieren
                                            trade_date_obj = trade[date_cols[0]]
                                            if hasattr(trade_date_obj, 'date'):
                                                trade_date_only = trade_date_obj.date()
                                            else:
                                                trade_date_only = datetime.datetime.now().date()
                                            
                                            trade_open_datetime = datetime.datetime.combine(
                                                trade_date_only, 
                                                datetime.datetime.strptime(trade_open_time_str, '%H:%M:%S').time()
                                            )
                                            

                                            

                                        
                                        # 4. Nach Eröffnungszeit filtern
                                        if trade_open_datetime is not None:
                                            peak_df_filtered = peak_df[peak_df['datetime_bern'] >= trade_open_datetime]
                                            

                                        else:
                                            # Keine Eröffnungszeit verfügbar - alle Datenpunkte verwenden
                                            peak_df_filtered = peak_df
                                        
                                                                                # 5. Peak finden (negativster Preis für Short-Optionen)
                                        if len(peak_df_filtered) > 0:
                                            # Bei Short-Optionen: Negativster Preis = größter Verlust
                                            peak_idx = peak_df_filtered['price'].idxmin()
                                            peak_preis = peak_df_filtered.loc[peak_idx, 'price']
                                            peak_time = peak_df_filtered.loc[peak_idx, 'timestamp']
                                            peak_datetime_bern = peak_df_filtered.loc[peak_idx, 'datetime_bern']
                                            

                                        else:
                                            peak_preis = None
                                            peak_time = None
                                            peak_datetime_bern = None
                                    else:
                                        peak_preis = None
                                        peak_time = None
                                    

                                    
                                    # Setze Peak-Preis und Peak-Zeit
                                    if peak_preis is not None:
                                        # Peak-Preis setzen
                                        display_trades.loc[idx, '📊 Peak'] = f"{float(peak_preis):.3f}"
                                        
                                        # Peak-Zeit direkt aus dem DataFrame in lesbarer Bern-Zeit setzen
                                        if peak_datetime_bern is not None:
                                            try:
                                                # Direkt aus dem DataFrame: bereits in Bern-Zeit
                                                peak_time_formatted = peak_datetime_bern.strftime('%H:%M:%S')
                                                display_trades.loc[idx, '🕐 Peak-Zeit'] = peak_time_formatted
                                                
                                                # ✅ SPEICHERE ALLE BEREICHNETEN ERGEBNISSE IM TRADE-RESULTS-CACHE
                                                if handelsende_preis is not None:
                                                    trade_results_cache.cache_trade_results(
                                                        trade_id, api_date, option_type, strike,
                                                        handelsende_preis, peak_preis, peak_time_formatted, api_link
                                                    )
                                            except Exception:
                                                display_trades.loc[idx, '🕐 Peak-Zeit'] = 'Zeit-Fehler'
                                        else:
                                            display_trades.loc[idx, '🕐 Peak-Zeit'] = 'Keine Zeit'
                                    else:
                                        display_trades.loc[idx, '📊 Peak'] = 'Keine Daten'
                                        display_trades.loc[idx, '🕐 Peak-Zeit'] = 'Keine Daten'
                                        
                                else:

                                    
                                    display_trades.loc[idx, '📈 Optionspreis Handelsende'] = 'Keine API-Daten'
                                    display_trades.loc[idx, '📊 Peak'] = 'Keine API-Daten'
                                    display_trades.loc[idx, '🕐 Peak-Zeit'] = 'Keine API-Daten'
                                    display_trades.loc[idx, '🔗 API-Link'] = 'Keine API-Daten'
                            except Exception as api_error:

                                
                                display_trades.loc[idx, '📈 Optionspreis Handelsende'] = 'API Probleme'
                                display_trades.loc[idx, '📊 Peak'] = 'API Probleme'
                                display_trades.loc[idx, '🕐 Peak-Zeit'] = 'API Probleme'
                                display_trades.loc[idx, '🔗 API-Link'] = 'API Probleme'
                            
                            # Kurze Pause zwischen API-Calls (Dashboard nicht überlasten)
                            time.sleep(0.1)
                    else:
                        display_trades.loc[idx, '📈 Optionspreis Handelsende'] = 'Keine Option'
                        display_trades.loc[idx, '📊 Peak'] = 'Keine Option'
                        display_trades.loc[idx, '🕐 Peak-Zeit'] = 'Keine Option'
                        display_trades.loc[idx, '🔗 API-Link'] = 'Keine Option'
                    
                except Exception as e:
                    display_trades.loc[idx, '📈 Optionspreis Handelsende'] = 'Fehler'
                    display_trades.loc[idx, '📊 Peak'] = 'Fehler'
                    display_trades.loc[idx, '🕐 Peak-Zeit'] = 'Fehler'
                    display_trades.loc[idx, '🔗 API-Link'] = 'Fehler'
            
            progress_bar.empty()
            st.success(f"✅ Handelsende-Preise geladen")
            
            # Optionspreis-Filter anwenden (falls aktiviert)
            if st.session_state.get('filter_profitable_options', False) or st.session_state.get('filter_unprofitable_options', False):
                filter_type = "profitable" if st.session_state.get('filter_profitable_options', False) else "unprofitable"
                
                if filter_type == "profitable":
                    st.info("🎯 Wende Filter für profitable Short-Optionen an...")
                else:
                    st.info("🎯 Wende Filter für nicht profitable Short-Optionen an...")
                
                before_filter = len(display_trades)
                
                # Nur Trades mit gültigen Daten filtern
                valid_trades = display_trades[
                    (display_trades['📈 Optionspreis Handelsende'] != 'N/A') & 
                    (display_trades['📈 Optionspreis Handelsende'] != 'Keine Daten') &
                    (display_trades['📈 Optionspreis Handelsende'] != 'Keine API-Daten') &
                    (display_trades['📈 Optionspreis Handelsende'] != 'API Probleme') &
                    (display_trades['📈 Optionspreis Handelsende'] != 'Keine Option') &
                    (display_trades['📈 Optionspreis Handelsende'] != 'Fehler')
                ].copy()
                
                if len(valid_trades) > 0:
                    # Konvertiere Handelsende-Preise zu numerischen Werten (als Absolutwerte für Vergleich)
                    valid_trades['handelsende_numeric'] = pd.to_numeric(
                        valid_trades['📈 Optionspreis Handelsende'], 
                        errors='coerce'
                    ).abs()  # Absolutwerte verwenden, da Eröffnungspreis auch positiv angezeigt wird
                    
                    # Konvertiere Opening-Preise zu numerischen Werten
                    if '💰 Preis Eröffnung' in valid_trades.columns:
                        valid_trades['opening_numeric'] = pd.to_numeric(
                            valid_trades['💰 Preis Eröffnung'], 
                            errors='coerce'
                        )
                        
                        if filter_type == "profitable":
                            # Profitable: Opening > Handelsende (Gewinn bei Short-Optionen)
                            filtered_trades = valid_trades[
                                (valid_trades['opening_numeric'] > valid_trades['handelsende_numeric']) &
                                (valid_trades['opening_numeric'] > 0)  # Nur gültige Opening-Preise
                            ]
                            success_msg = "profitable Short-Optionen"
                            warning_msg = "⚠️ Keine profitablen Short-Optionen gefunden"
                        else:
                            # Nicht profitable: Handelsende > Opening (Verlust bei Short-Optionen)
                            filtered_trades = valid_trades[
                                (valid_trades['handelsende_numeric'] > valid_trades['opening_numeric']) &
                                (valid_trades['opening_numeric'] > 0)  # Nur gültige Opening-Preise
                            ]
                            success_msg = "nicht profitable Short-Optionen"
                            warning_msg = "⚠️ Keine nicht profitablen Short-Optionen gefunden"
                        
                        if len(filtered_trades) > 0:
                            # Entferne temporäre Spalten
                            filtered_trades = filtered_trades.drop(['handelsende_numeric', 'opening_numeric'], axis=1)
                            display_trades = filtered_trades
                            
                            after_filter = len(display_trades)
                            st.success(f"✅ Filter angewendet: {after_filter} {success_msg} gefunden (von {before_filter} Trades)")
                        else:
                            st.warning(warning_msg)
                            if filter_type == "profitable":
                                st.session_state.filter_profitable_options = False
                            else:
                                st.session_state.filter_unprofitable_options = False
                    else:
                        st.warning("⚠️ Opening-Preis-Spalte nicht verfügbar für Filter")
                        if filter_type == "profitable":
                            st.session_state.filter_profitable_options = False
                        else:
                            st.session_state.filter_unprofitable_options = False
                else:
                    st.warning("⚠️ Keine gültigen Handelsende-Preis-Daten für Filter verfügbar")
                    if filter_type == "profitable":
                        st.session_state.filter_profitable_options = False
                    else:
                        st.session_state.filter_unprofitable_options = False
            
            # Handelsende-Preis-Werte sind gesetzt
            
            # Jetzt die Metriken berechnen (nach dem Anwenden des Optionspreis-Filters)
            st.markdown('<div class="metric-section"><h3>📊 Trading Übersicht</h3></div>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_trades = len(display_trades)  # Verwende display_trades (gefilterte Daten)
                st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-header">
                        <div class="metric-icon">📈</div>
                        <div class="metric-title">TRADES</div>
                    </div>
                    <div class="metric-value neutral">{total_trades}</div>
                    <div class="metric-description">Anzahl aller Trades</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Finde P&L-Spalte in display_trades (kann umbenannt worden sein)
                pnl_column = None
                if '💰 P&L' in display_trades.columns:
                    pnl_column = '💰 P&L'
                elif profit_cols and profit_cols[0] in display_trades.columns:
                    pnl_column = profit_cols[0]
                
                if pnl_column:
                    try:
                        # Verwende display_trades für gefilterte P&L-Berechnung
                        total_pnl = display_trades[pnl_column].sum()
                        st.markdown(f"""
                        <div class="metric-tile">
                            <div class="metric-header">
                                <div class="metric-icon">💰</div>
                                <div class="metric-title">P&L GESAMT</div>
                            </div>
                            <div class="metric-value {'negative' if total_pnl < 0 else 'positive'}">${total_pnl:,.2f}</div>
                            <div class="metric-description">Gesamter Profit/Loss</div>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f"""
                        <div class="metric-tile">
                            <div class="metric-header">
                                <div class="metric-icon">💰</div>
                                <div class="metric-title">P&L GESAMT</div>
                            </div>
                            <div class="metric-value neutral">Fehler</div>
                            <div class="metric-description">P&L-Berechnung fehlgeschlagen</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-header">
                            <div class="metric-icon">💰</div>
                            <div class="metric-title">P&L GESAMT</div>
                        </div>
                        <div class="metric-value neutral">N/A</div>
                        <div class="metric-description">Keine P&L-Daten verfügbar</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col3:
                # Suche nach Status-Spalte (mit oder ohne Emoji)
                status_col = None
                for col in display_trades.columns:
                    if 'Status' in col:
                        status_col = col
                        break
                
                if status_col:
                    # Filtere nach numerischem Status-Wert 2 (Stopped)
                    stopped_trades = display_trades[
                        pd.to_numeric(display_trades[status_col], errors='coerce') == 2
                    ]
                    total_stopped = len(stopped_trades)
                    st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-header">
                            <div class="metric-icon">🛑</div>
                            <div class="metric-title">GESTOPPTE TRADES</div>
                        </div>
                        <div class="metric-value neutral">{total_stopped}</div>
                        <div class="metric-description">Status = 2 (Stopped)</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-header">
                            <div class="metric-icon">🛑</div>
                            <div class="metric-title">GESTOPPTE TRADES</div>
                        </div>
                        <div class="metric-value neutral">N/A</div>
                        <div class="metric-description">Status-Spalte nicht verfügbar</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col4:
                if 'Status' in display_trades.columns:
                    st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-header">
                            <div class="metric-icon">📊</div>
                            <div class="metric-title">STATUS</div>
                        </div>
                        <div class="metric-value neutral">Verfügbar</div>
                        <div class="metric-description">Status-Informationen aktiv</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-tile">
                        <div class="metric-header">
                            <div class="metric-icon">📊</div>
                            <div class="metric-title">STATUS</div>
                        </div>
                        <div class="metric-value neutral">N/A</div>
                        <div class="metric-description">Status-Spalte nicht verfügbar</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # API-Link Spalte aus den Anzeige-Spalten entfernen
            display_columns = [col for col in display_columns if col != '🔗 API-Link']
            
            # Strike-Preis-Spalten hinzufügen
            display_columns.extend(strike_columns)
            
            # Summenzeile
            if profit_cols:
                total_pnl = trade_data[profit_cols[0]].sum()
                
                summary_data = {
                    '📅 Datum': 'GESAMT:',
                    '🕐 Eröffnung': '',
                    '💰 Preis Eröffnung': '',
                    '🎯 Stop/Target': '',
                    '🕐 Schließung': '',
                    '💰 Preis Schließung': '',
                    '📊 Trade Type': '',
                    '📦 Quantity': '',
                    '💰 P&L': f"{total_pnl:.2f}",
                    '📈 Optionspreis Handelsende': '',
                    '📊 Peak': '',
                    '🕐 Peak-Zeit': '',
                    '📈 Status': ''
                }
                
                # Optionspreis Handelsende zur Summenzeile
                if '📈 Optionspreis Handelsende' in display_columns:
                    summary_data['📈 Optionspreis Handelsende'] = ''
                
                # Peak zur Summenzeile
                if '📊 Peak' in display_columns:
                    summary_data['📊 Peak'] = ''
                
                # Strike-Preis-Spalten
                for strike_col in strike_columns:
                    summary_data[strike_col] = ''
                

                
                # Commission-Spalte zur Summenzeile
                if '💰 Commission' in display_columns:
                    summary_data['💰 Commission'] = ''
                
                summary_row = pd.DataFrame([summary_data])
                final_table = pd.concat([display_trades[display_columns], summary_row], ignore_index=True)
            else:
                final_table = display_trades[display_columns]
            
            # Tabelle anzeigen
            try:
                st.dataframe(
                    final_table,
                    use_container_width=True,
                    hide_index=True
                )
            except Exception as e:
                st.error(f"❌ Fehler beim Anzeigen der Tabelle: {e}")
                st.text(final_table.to_string())
            
            # API-Test Button
            if st.button("🧪 API-Verbindung testen", key="api_test"):
                test_api_connection()
            
            # Vereinfachte Chart-Funktionalität
            st.subheader("📈 Optionspreis-Chart")
            st.info("📊 Chart-Funktionalität wird geladen...")
            
        else:
            st.warning("⚠️ Keine gefilterten Trades gefunden!")
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der TAT Tradenavigator-Seite: {e}")
        st.info("💡 Bitte stellen Sie sicher, dass die Trade-Tabelle verfügbar ist.")
