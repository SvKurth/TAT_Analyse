"""
Navigator Page Module für Tradelog Dashboard
Zeigt die TAT Navigator-Seite mit Navigation und Charts
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from modules.api_charts import (
    get_option_price_data, 
    get_spx_vix_data, 
    create_options_price_chart, 
    create_spx_vix_chart,
    test_api_connection
)

def show_tat_navigator_page(data_loader, db_path):
    """Zeigt die TAT Tradenavigator-Seite an."""
    st.header("🎯 TAT Tradenavigator")
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
        
        # Intelligente Spaltenerkennung (wie in Metriken)
        profit_cols = [col for col in trade_data.columns if 'profit' in col.lower() or 'pnl' in col.lower() or 'gewinn' in col.lower()]
        type_cols = [col for col in trade_data.columns if 'type' in col.lower() or 'typ' in col.lower()]
        date_cols = [col for col in trade_data.columns if 'date' in col.lower() or 'datum' in col.lower() or 'time' in col.lower() or 'opened' in col.lower() or 'closed' in col.lower()]
        strategy_cols = [col for col in trade_data.columns if 'strategy' in col.lower() or 'strategie' in col.lower()]
        
        # Datumsfilter (exakt wie in Metriken)
        if date_cols:
            with st.container():
                st.markdown("---")
                st.markdown("**🔍 Filter & Auswahl**")
                
                # Datum-Eingaben
                col1, col2 = st.columns(2)
                with col1:
                    # Startdatum
                    start_date = st.date_input(
                        "Von", 
                        value=st.session_state.get('start_date', None), 
                        key="start_date_input_nav",
                        label_visibility="collapsed", 
                        help="Startdatum"
                    )
                    # Direkt im Session State speichern
                    if start_date != st.session_state.get('start_date'):
                        st.session_state.start_date = start_date
                with col2:
                    # Enddatum
                    end_date = st.date_input(
                        "Bis", 
                        value=st.session_state.get('end_date', None), 
                        key="end_date_input_nav",
                        label_visibility="collapsed", 
                        help="Enddatum"
                    )
                    # Direkt im Session State speichern
                    if end_date != st.session_state.get('end_date'):
                        st.session_state.end_date = end_date
                
                # Zusätzliche Filter: Trade Type und Strategy
                col_filter1, col_filter2 = st.columns(2)
                
                with col_filter1:
                    # Trade Type Filter
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
                    # Strategy Filter
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
                
                # Einheitlicher Anwenden-Button für alle Filter
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
                
                # Filter anwenden wenn Button gedrückt wurde
                if st.session_state.get('filters_applied_nav', False):
                    # Datumsspalte als datetime konvertieren
                    if trade_data[date_cols[0]].dtype == 'object':
                        trade_data[date_cols[0]] = pd.to_datetime(trade_data[date_cols[0]], errors='coerce')
                    
                    if pd.api.types.is_datetime64_any_dtype(trade_data[date_cols[0]]):
                        trade_data_filtered = trade_data.copy()
                        filter_description = ""
                        
                        # Datum-Filter anwenden
                        start_date = st.session_state.get('start_date')
                        end_date = st.session_state.get('end_date')
                        
                        if start_date and end_date:
                            # Konvertiere start_date und end_date zu datetime für besseren Vergleich
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
                        
                        # Trade Type Filter anwenden
                        if selected_types and type_cols:
                            trade_data_filtered = trade_data_filtered[trade_data_filtered[type_cols[0]].isin(selected_types)]
                            
                            if filter_description:
                                filter_description += f" | Type: {len(selected_types)}"
                            else:
                                filter_description = f"Type: {len(selected_types)}"
                        
                        # Strategy Filter anwenden
                        if selected_strategies and strategy_cols:
                            trade_data_filtered = trade_data_filtered[trade_data_filtered[strategy_cols[0]].isin(selected_strategies)]
                            
                            if filter_description:
                                filter_description += f" | Strategy: {len(selected_strategies)}"
                            else:
                                filter_description = f"Strategy: {len(selected_strategies)}"
                        
                        # Filter-Ergebnis anzeigen
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
        
        # Session State für ausgewählte Zeile initialisieren
        if 'selected_row_index' not in st.session_state:
            st.session_state.selected_row_index = None
        
        # Alle gefilterten Trades in einer Tabelle anzeigen
        if len(trade_data) > 0:
            # Erfolgsmeldung mit Anzahl der Trades
            st.success(f"✅ {len(trade_data)} gefilterte Trades gefunden")
            
            # Tabelle vorbereiten
            display_trades = trade_data.copy()
            
            # Datum formatieren
            if date_cols:
                date_col = date_cols[0]
                display_trades['Date'] = display_trades[date_col].dt.strftime('%d.%m.%Y')
            
            # Eröffnungszeit formatieren (nur Zeit ohne Datum, mit Sekunden)
            if 'DateOpened' in display_trades.columns:
                display_trades['TimeOnly'] = display_trades['DateOpened'].apply(
                    lambda x: x.strftime('%H:%M:%S') if pd.notna(x) and hasattr(x, 'strftime') else str(x)[-8:] if pd.notna(x) and len(str(x)) >= 8 else str(x)
                )
            
            # Schließungszeit formatieren (nur Zeit ohne Datum, mit Sekunden)
            if 'DateClosed' in display_trades.columns:
                display_trades['TimeClosedOnly'] = display_trades['DateClosed'].apply(
                    lambda x: x.strftime('%H:%M:%S') if pd.notna(x) and hasattr(x, 'strftime') else str(x)[-8:] if pd.notna(x) and len(str(x)) >= 8 else str(x)
                )
            
            # Metriken oberhalb der Tabelle
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
                if profit_cols and 'Qty' in trade_data.columns:
                    # Normalisierte P&L über alle Trades
                    normalized_values = trade_data.apply(
                        lambda row: row[profit_cols[0]] / row['Qty'] if pd.notna(row[profit_cols[0]]) and pd.notna(row['Qty']) and row['Qty'] != 0 else 0, 
                        axis=1
                    )
                    total_pnl_normalized = normalized_values.sum()
                    st.metric("💰 P&L norm. Gesamt", f"{total_pnl_normalized:.2f}")
                else:
                    st.metric("💰 P&L norm. Gesamt", "N/A")
            
            with col4:
                # Gestoppte Trades zählen
                if 'Status' in trade_data.columns:
                    stopped_trades = trade_data[trade_data['Status'] == 'Stopped']
                    total_stopped = len(stopped_trades)
                    st.metric("🛑 Gestoppte Trades", total_stopped)
                else:
                    st.metric("🛑 Gestoppte Trades", "N/A")
            
            # Überschrift für Tabelle
            st.subheader(f"📋 Alle gefilterten Trades")
            
            # P&L formatieren
            if profit_cols:
                pnl_col = profit_cols[0]
                display_trades['P&L_Display'] = display_trades[pnl_col].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                )
                
                # P&L normalisiert berechnen (P&L / Quantity)
                if 'Qty' in display_trades.columns:
                    display_trades['P&L_Normalized'] = display_trades.apply(
                        lambda row: row[pnl_col] / row['Qty'] if pd.notna(row[pnl_col]) and pd.notna(row['Qty']) and row['Qty'] != 0 else 0, 
                        axis=1
                    )
                    display_trades['P&L_Normalized_Display'] = display_trades['P&L_Normalized'].apply(
                        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                    )
            
            # Strike-Preis-Spalten hinzufügen
            strike_columns = []
            
            # Short Strike-Preise (wichtiger für Short-Optionen)
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
            
            # Spalten umbenennen für bessere Anzeige
            column_mapping = {
                'Date': '📅 Datum',
                'TimeOnly': '🕐 Eröffnung',  # Verwende TimeOnly statt DateOpened
                'PriceOpen': '💰 Preis Eröffnung',
                'TimeClosedOnly': '🕐 Schließung',  # Verwende TimeClosedOnly statt TimeClosed
                'PriceClose': '💰 Preis Schließung',
                'TradeType': '📊 Trade Type',
                'Symbol': '🏷️ Symbol',
                'Status': '📈 Status',
                'Commission': '💰 Kommission'
            }
            
            # Quantity-Spalte umbenennen falls vorhanden
            if 'Qty' in display_trades.columns:
                column_mapping['Qty'] = '📦 Quantity'
            
            # P&L normalisiert Spalte umbenennen falls vorhanden
            if 'P&L_Normalized_Display' in display_trades.columns:
                column_mapping['P&L_Normalized_Display'] = '💰 P&L norm.'
            
            if profit_cols:
                display_trades = display_trades.rename(columns={profit_cols[0]: '💰 P&L'})
            
            for old_name, new_name in column_mapping.items():
                if old_name in display_trades.columns:
                    display_trades = display_trades.rename(columns={old_name: new_name})
            
            # Wichtige Spalten für Anzeige (mit Strike-Preisen)
            display_columns = []
            for col in ['📅 Datum', '🕐 Eröffnung', '💰 Preis Eröffnung', '🕐 Schließung', '💰 Preis Schließung', '📊 Trade Type', '📦 Quantity', '💰 P&L']:
                if col in display_trades.columns:
                    display_columns.append(col)
            
            # Strike-Preis-Spalten hinzufügen
            display_columns.extend(strike_columns)
            
            # Summenzeile hinzufügen
            if profit_cols:
                total_pnl = trade_data[profit_cols[0]].sum()
                
                # Normalisierte P&L Summe berechnen
                total_pnl_normalized = 0
                if 'Qty' in trade_data.columns:
                    normalized_values = trade_data.apply(
                        lambda row: row[profit_cols[0]] / row['Qty'] if pd.notna(row[profit_cols[0]]) and pd.notna(row['Qty']) and row['Qty'] != 0 else 0, 
                        axis=1
                    )
                    total_pnl_normalized = normalized_values.sum()
                
                # Summenzeile erstellen
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
                
                # Strike-Preis-Spalten in Summenzeile mit leeren Werten
                for strike_col in strike_columns:
                    summary_data[strike_col] = ''
                
                summary_row = pd.DataFrame([summary_data])
                
                # Tabelle mit Summenzeile kombinieren
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
                st.info("💡 Versuche alternative Anzeige...")
                st.text(final_table.to_string())
            
            # API-Test Button
            if st.button("🧪 API-Verbindung testen", key="api_test"):
                test_api_connection()
            
            # Optionspreis-Chart mit interaktiver Tabellenauswahl
            st.subheader("📈 Optionspreis-Chart")
            
            # Sammle alle Short-Optionen für Charts
            short_options = []
            
            # Short Put Optionen sammeln
            if 'ShortPut' in trade_data.columns:
                for idx, trade in trade_data.iterrows():
                    if pd.notna(trade['ShortPut']) and trade['ShortPut'] != 0:
                        trade_type = trade.get('TradeType', 'N/A')
                        time_opened = trade.get('DateOpened', 'N/A')
                        short_options.append({
                            'row_index': idx,
                            'type': 'P',
                            'strike': int(trade['ShortPut']),
                            'trade_info': trade.to_dict(),
                            'label': f"🔴 Put {trade['ShortPut']:.0f} - {trade_type} - {time_opened}"
                        })
            
            # Short Call Optionen sammeln
            if 'ShortCall' in trade_data.columns:
                for idx, trade in trade_data.iterrows():
                    if pd.notna(trade['ShortCall']) and trade['ShortCall'] != 0:
                        trade_type = trade.get('TradeType', 'N/A')
                        time_opened = trade.get('DateOpened', 'N/A')
                        short_options.append({
                            'row_index': idx,
                            'type': 'C',
                            'strike': int(trade['ShortCall']),
                            'trade_info': trade.to_dict(),
                            'label': f"🟢 Call {trade['ShortCall']:.0f} - {trade_type} - {time_opened}"
                        })
            
            if short_options:
                # Buttons für jede Option erstellen
                st.markdown("**🎯 Klicken Sie auf eine Option für den Chart:**")
                
                # Buttons in Spalten anordnen
                cols = st.columns(min(3, len(short_options)))
                for i, option in enumerate(short_options):
                    col_idx = i % 3
                    with cols[col_idx]:
                        if st.button(
                            option['label'], 
                            key=f"option_btn_{option['row_index']}",
                            use_container_width=True
                        ):
                            st.session_state.selected_row_index = option['row_index']
                            st.rerun()
                
                # Ausgewählte Option finden
                selected_option = None
                if st.session_state.selected_row_index is not None:
                    for opt in short_options:
                        if opt['row_index'] == st.session_state.selected_row_index:
                            selected_option = opt
                            break
                
                if selected_option:
                    # Chart für gewählte Option anzeigen
                    st.info(f"📊 Chart für {selected_option['type']}{selected_option['strike']} wird geladen...")
                    
                    # Datum für API-Request formatieren
                    if date_cols:
                        # Verwende das erste verfügbare Datum aus den gefilterten Daten
                        first_date = trade_data[date_cols[0]].dt.date.iloc[0]
                        api_date = first_date.strftime('%Y-%m-%d')
                        
                        # Beide Charts laden
                        with st.spinner("🔄 Lade API-Daten..."):
                            # SPX/VIX Daten laden
                            spx_vix_data = get_spx_vix_data(api_date)
                            
                            # Optionspreis-Daten laden
                            chart_data = get_option_price_data('SPX', api_date, selected_option['type'], selected_option['strike'])
                        
                        # Charts anzeigen
                        if spx_vix_data and chart_data:
                            st.success(f"✅ API-Daten erfolgreich geladen!")
                            
                            # Optionspreis-Chart mit SPX
                            with st.spinner("🔄 Erstelle Optionspreis-Chart..."):
                                options_chart = create_options_price_chart(
                                    chart_data, 
                                    selected_option['type'], 
                                    selected_option['strike'], 
                                    api_date, 
                                    selected_option['trade_info']
                                )
                                
                                if options_chart:
                                    st.subheader(f"📈 {selected_option['type']}{selected_option['strike']} Optionspreis + SPX")
                                    st.plotly_chart(options_chart, use_container_width=True, height=600)
                                else:
                                    st.warning("⚠️ Fehler beim Erstellen des Optionspreis-Charts")
                            
                            # SPX/VIX Chart
                            with st.spinner("🔄 Erstelle SPX/VIX Chart..."):
                                spx_vix_chart = create_spx_vix_chart(spx_vix_data, api_date, selected_option['trade_info'])
                                
                                if spx_vix_chart:
                                    st.subheader("📊 SPX & VIX Chart")
                                    st.plotly_chart(spx_vix_chart, use_container_width=True, height=400)
                                else:
                                    st.warning("⚠️ Fehler beim Erstellen des SPX/VIX Charts")
                            
                        elif spx_vix_data:
                            st.info(f"✅ SPX/VIX API-Daten erhalten: {len(spx_vix_data)} Datenpunkte")
                            st.warning(f"⚠️ Keine Optionspreis-API-Daten für {selected_option['type']}{selected_option['strike']} verfügbar")
                            
                            # Nur SPX/VIX Chart anzeigen
                            with st.spinner("🔄 Erstelle SPX/VIX Chart..."):
                                spx_vix_chart = create_spx_vix_chart(spx_vix_data, api_date, selected_option['trade_info'])
                                
                                if spx_vix_chart:
                                    st.subheader("📊 SPX & VIX Chart")
                                    st.plotly_chart(spx_vix_chart, use_container_width=True, height=400)
                                else:
                                    st.warning("⚠️ Fehler beim Erstellen des SPX/VIX Charts")
                            
                        elif chart_data:
                            st.info(f"✅ Optionspreis-Daten erhalten für {selected_option['type']}{selected_option['strike']}")
                            st.warning("⚠️ Keine SPX/VIX API-Daten verfügbar")
                            
                            # Nur Optionspreis-Chart anzeigen
                            with st.spinner("🔄 Erstelle Optionspreis-Chart..."):
                                options_chart = create_options_price_chart(
                                    chart_data, 
                                    selected_option['type'], 
                                    selected_option['strike'], 
                                    api_date, 
                                    selected_option['trade_info']
                                )
                                
                                if options_chart:
                                    st.subheader(f"📈 {selected_option['type']}{selected_option['strike']} Optionspreis")
                                    st.plotly_chart(options_chart, use_container_width=True, height=600)
                                else:
                                    st.warning("⚠️ Fehler beim Erstellen des Optionspreis-Charts")
                        else:
                            st.warning("⚠️ Keine API-Daten verfügbar")
                            st.info("💡 Versuchen Sie es mit einem anderen Strike oder Datum")
                    
                    # Trade-Details anzeigen
                    st.markdown("### 📋 Trade-Details")
                    col1, col2, col3 = st.columns(3)
                    
                    trade_info = selected_option['trade_info']
                    
                    with col1:
                        if 'DateOpened' in trade_info and pd.notna(trade_info['DateOpened']):
                            st.metric("🕐 Eröffnung", str(trade_info['DateOpened']))
                        if 'TimeClosed' in trade_info and pd.notna(trade_info['TimeClosed']):
                            st.metric("🕐 Schließung", str(trade_info['TimeClosed']))
                    
                    with col2:
                        if 'TradeType' in trade_info and pd.notna(trade_info['TradeType']):
                            st.metric("📊 Trade Type", str(trade_info['TradeType']))
                        if 'Qty' in trade_info and pd.notna(trade_info['Qty']):
                            st.metric("📦 Quantity", str(trade_info['Qty']))
                    
                    with col3:
                        if profit_cols and profit_cols[0] in trade_info and pd.notna(trade_info[profit_cols[0]]):
                            pnl = trade_info[profit_cols[0]]
                            pnl_color = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                            st.metric(f"{pnl_color} P&L", f"{pnl:.2f}")
                        if 'PriceStopTarget' in trade_info and pd.notna(trade_info['PriceStopTarget']):
                            st.metric("🎯 Stoppreis", f"{trade_info['PriceStopTarget']:.2f}")
                    
                    # Zusätzliche Zeile für Preise
                    col4, col5, col6 = st.columns(3)
                    
                    with col4:
                        if 'PriceOpen' in trade_info and pd.notna(trade_info['PriceOpen']):
                            st.metric("💰 Preis Eröffnung", f"{trade_info['PriceOpen']:.3f}")
                    
                    with col5:
                        if 'PriceClose' in trade_info and pd.notna(trade_info['PriceClose']):
                            st.metric("💰 Preis Schließung", f"{trade_info['PriceClose']:.3f}")
                    
                    with col6:
                        if 'PriceShort' in trade_info and pd.notna(trade_info['PriceShort']):
                            st.metric("💰 Preis Short", f"{trade_info['PriceShort']:.3f}")
            else:
                st.info("📊 Keine Short-Optionen für Charts verfügbar")
        
        else:
            st.warning("⚠️ Keine gefilterten Trades gefunden!")
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der TAT Tradenavigator-Seite: {e}")
        st.info("💡 Bitte stellen Sie sicher, dass die Trade-Tabelle verfügbar ist.")
