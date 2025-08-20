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
    
    # Beide Caches initialisieren
    api_cache = get_cache_instance()
    trade_results_cache = get_trade_results_cache()
    
    # Cache-Statistiken in der Sidebar anzeigen
    with st.sidebar:
        st.markdown("**📊 Cache-Status**")
        
        # API-Cache Statistiken
        try:
            api_cache_stats = api_cache.get_cache_stats()
            st.markdown("**🗄️ API-Cache**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Einträge", f"{api_cache_stats['total_entries']}")
            with col2:
                st.metric("Größe", f"{api_cache_stats['total_size_mb']:.1f} MB")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Letzte 7 Tage", f"{api_cache_stats['recent_entries']}")
            with col2:
                if api_cache_stats['top_entries']:
                    top_entry = api_cache_stats['top_entries'][0]
                    st.metric("Top Entry", f"{top_entry['size_kb']:.1f} KB")
                else:
                    st.metric("Top Entry", "N/A")
        except Exception:
            st.info("🗄️ API-Cache: Nicht verfügbar")
        
        st.markdown("---")
        
        # Trade-Cache Statistiken
        try:
            trade_cache_stats = trade_results_cache.get_cache_stats()
            st.markdown("**⚡ Trade-Cache**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Einträge", f"{trade_cache_stats['total_entries']}")
            with col2:
                st.metric("Größe", f"{trade_cache_stats['total_size_kb']:.1f} KB")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Letzte 30 Tage", f"{trade_cache_stats['recent_entries']}")
            with col2:
                if trade_cache_stats['top_entries']:
                    top_entry = trade_cache_stats['top_entries'][0]
                    st.metric("Top Entry", f"{top_entry['size_kb']:.1f} KB")
                else:
                    st.metric("Top Entry", "N/A")
        except Exception:
            st.info("⚡ Trade-Cache: Nicht verfügbar")
        
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
            st.success(f"✅ {len(trade_data)} gefilterte Trades gefunden")
            
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
            
            # Metriken
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_trades = len(trade_data)
                st.metric("📈 Trades", total_trades)
            
            with col2:
                if profit_cols:
                    total_pnl = trade_data[profit_cols[0]].sum()
                    st.metric("💰 P&L Gesamt", f"{total_pnl:.2f}")
                else:
                    st.metric("💰 P&L Gesamt", "N/A")
            
            with col3:
                if 'Status' in trade_data.columns:
                    stopped_trades = trade_data[trade_data['Status'] == 'Stopped']
                    total_stopped = len(stopped_trades)
                    st.metric("🛑 Gestoppte Trades", total_stopped)
                else:
                    st.metric("🛑 Gestoppte Trades", "N/A")
            
            with col4:
                if 'Status' in trade_data.columns:
                    # Weitere Metrik hier hinzufügen falls gewünscht
                    st.metric("📊 Status", "Verfügbar")
                else:
                    st.metric("📊 Status", "N/A")
            
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
            for col in ['📅 Datum', '🕐 Eröffnung', '💰 Preis Eröffnung', '🎯 Stop/Target', '🕐 Schließung', '💰 Preis Schließung', '📊 Trade Type', '📦 Quantity', '💰 P&L']:
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
                    st.info(f"🔍 Gefundene Commission-Spalten: {commission_cols}")
                    
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
            
            # Handelsende-Preis-Werte sind gesetzt
            
            # Strike-Preis-Spalten hinzufügen
            display_columns.extend(strike_columns)
            
            # Summenzeile
            if profit_cols:
                total_pnl = trade_data[profit_cols[0]].sum()
                
                summary_data = {
                    '📅 Datum': 'GESAMT:',
                    '🕐 Eröffnung': '',
                    '💰 Preis Eröffnung': '',
                    '🕐 Schließung': '',
                    '💰 Preis Schließung': '',
                    '📊 Trade Type': '',
                    '📦 Quantity': '',
                    '💰 P&L': f"{total_pnl:.2f}"
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
