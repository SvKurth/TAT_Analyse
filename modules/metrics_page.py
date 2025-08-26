"""
Metrics Page Module für Tradelog Dashboard
Zeigt die ursprüngliche Metriken-Seite mit allen Kacheln, Filtern und Charts
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

def show_metrics_page(data_loader, db_path):
    """Zeigt die ursprüngliche Metriken-Seite mit allen Kacheln, Filtern und Charts."""
    st.header("📊 Metriken")
    
    try:
        # Trade-Tabelle laden
        trade_data = data_loader.load_trade_table(db_path)
        st.success(f"✅ Trade-Daten geladen: {len(trade_data)} Trades, {len(trade_data.columns)} Spalten")
        
        # Intelligente Spaltenerkennung
        profit_cols = [col for col in trade_data.columns if 'profit' in col.lower() or 'pnl' in col.lower() or 'gewinn' in col.lower()]
        type_cols = [col for col in trade_data.columns if 'type' in col.lower() or 'typ' in col.lower()]
        date_cols = [col for col in trade_data.columns if 'date' in col.lower() or 'datum' in col.lower() or 'time' in col.lower() or 'opened' in col.lower() or 'closed' in col.lower()]
        price_cols = [col for col in trade_data.columns if 'price' in col.lower() or 'preis' in col.lower()]
        quantity_cols = [col for col in trade_data.columns if 'quantity' in col.lower() or 'menge' in col.lower() or 'size' in col.lower()]
        
        # Datumsfilter
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
                        key="start_date_input",
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
                        key="end_date_input",
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
                    strategy_cols = [col for col in trade_data.columns if 'strategy' in col.lower() or 'strategie' in col.lower()]
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
                    if st.button("🔍 Alle Filter anwenden", type="primary", use_container_width=True):
                        st.session_state.apply_filters = True
                        st.rerun()
                
                with col_reset:
                    if st.button("🔄 Reset", use_container_width=True):
                        st.session_state.start_date = None
                        st.session_state.end_date = None
                        st.session_state.apply_filters = False
                        st.rerun()
                
                # Filter anwenden wenn Button gedrückt wurde
                if st.session_state.get('apply_filters', False):
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
                            st.session_state.apply_filters = False
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
                            st.session_state.apply_filters = False
                    else:
                        st.error(f"❌ Datumsspalte konnte nicht als Datum interpretiert werden")
                        st.session_state.apply_filters = False
                
                st.markdown("---")
        
        # CSS für Kacheln
        st.markdown("""
        <style>
        .metric-tile {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            border: 1px solid #e9ecef;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .metric-icon {
            font-size: 24px;
            margin-right: 10px;
        }
        .metric-title {
            font-size: 18px;
            font-weight: bold;
            color: #495057;
        }
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-description {
            font-size: 14px;
            color: #6c757d;
            font-style: italic;
        }
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .neutral { color: #495057; }
        </style>
        """, unsafe_allow_html=True)
        
        # 1. Key Performance Metrics
        st.subheader("✅ Key Performance Metrics")
        
        # Berechne Metriken
        total_trades = len(trade_data)
        
        if profit_cols:
            profit_col = profit_cols[0]
            total_profit = trade_data[profit_col].sum()
            avg_profit = trade_data[profit_col].mean()
            win_trades = len(trade_data[trade_data[profit_col] > 0])
            win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Profit Factor (Gewinn/Verlust)
            gains = trade_data[trade_data[profit_col] > 0][profit_col].sum()
            losses = abs(trade_data[trade_data[profit_col] < 0][profit_col].sum())
            profit_factor = gains / losses if losses > 0 else 0
            
            # Max Drawdown
            cumulative = trade_data[profit_col].cumsum()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max * 100
            max_drawdown = drawdown.min()
            peak_value = running_max.max()
            
            # Datumsinformationen für Peak und Max Drawdown
            if date_cols:
                date_col = date_cols[0]
                # Finde das Datum des Peaks
                peak_idx = cumulative.idxmax()
                peak_date = trade_data.loc[peak_idx, date_col].strftime('%d.%m.%Y') if pd.notna(peak_idx) else "N/A"
                
                # Finde das Datum des Max Drawdowns
                max_dd_idx = drawdown.idxmin()
                max_dd_date = trade_data.loc[max_dd_idx, date_col].strftime('%d.%m.%Y') if pd.notna(max_dd_idx) else "N/A"
                
                # Finde den Tiefpunkt (niedrigsten Wert nach dem Peak)
                if pd.notna(peak_idx):
                    # Betrachte nur Daten nach dem Peak
                    data_after_peak = cumulative[peak_idx:]
                    if len(data_after_peak) > 1:  # Mindestens 2 Datenpunkte nach dem Peak
                        # Suche den niedrigsten Wert nach dem Peak
                        bottom_idx = data_after_peak.idxmin()
                        if pd.notna(bottom_idx) and bottom_idx != peak_idx:
                            bottom_value = cumulative.loc[bottom_idx]
                            bottom_date = trade_data.loc[bottom_idx, date_col].strftime('%d.%m.%Y')
                        else:
                            # Fallback: Kein echter Tiefpunkt nach dem Peak
                            bottom_value = peak_value
                            bottom_date = peak_date
                    else:
                        # Keine Daten nach dem Peak - suche den niedrigsten Wert in der gesamten Zeitreihe
                        # Das ist der "globale Tiefpunkt" für den Max Drawdown
                        global_bottom_idx = cumulative.idxmin()
                        if pd.notna(global_bottom_idx):
                            bottom_value = cumulative.loc[global_bottom_idx]
                            bottom_date = trade_data.loc[global_bottom_idx, date_col].strftime('%d.%m.%Y')
                        else:
                            bottom_value = peak_value
                            bottom_date = peak_date
                else:
                    bottom_value = peak_value
                    bottom_date = peak_date
                
                # DEBUG: Alle wichtigen Daten anzeigen
                st.info(f"""
                **🔍 DEBUG Max Drawdown Berechnung:**
                - Peak Index: {peak_idx}
                - Peak Value: ${peak_value:,.2f}
                - Peak Date: {peak_date}
                - Bottom Index: {bottom_idx if 'bottom_idx' in locals() else 'N/A'}
                - Bottom Value: ${bottom_value:,.2f}
                - Bottom Date: {bottom_date}
                - Max DD Index: {max_dd_idx}
                - Max DD Date: {max_dd_date}
                - Max DD Value: {max_drawdown:.1f}%
                """)
                
                # Zeige die ersten 10 Zeilen der kumulativen P&L für Debugging
                st.info(f"""
                **📊 Erste 10 Zeilen der kumulativen P&L:**
                {cumulative.head(10).to_string()}
                """)
                
                # Zeige die ersten 10 Zeilen des Drawdowns für Debugging
                st.info(f"""
                **📉 Erste 10 Zeilen des Drawdowns:**
                {drawdown.head(10).to_string()}
                """)
            else:
                peak_date = "N/A"
                max_dd_date = "N/A"
                bottom_date = "N/A"
                bottom_value = peak_value
            
            # Durchschnittliche Gewinner und Verlierer
            winning_trades = trade_data[trade_data[profit_col] > 0]
            losing_trades = trade_data[trade_data[profit_col] < 0]
            
            avg_winner = winning_trades[profit_col].mean() if len(winning_trades) > 0 else 0
            avg_loser = losing_trades[profit_col].mean() if len(losing_trades) > 0 else 0
            
            # Durchschnittliche Tagesgewinne und -verluste
            if date_cols:
                date_col = date_cols[0]
                # Datumsspalte als datetime konvertieren falls nötig
                if trade_data[date_col].dtype == 'object':
                    trade_data[date_col] = pd.to_datetime(trade_data[date_col], errors='coerce')
                
                if pd.api.types.is_datetime64_any_dtype(trade_data[date_col]):
                    # Nach Datum gruppieren und tägliche P&L berechnen
                    daily_pnl = trade_data.groupby(trade_data[date_col].dt.date)[profit_col].sum()
                    
                    # Positive und negative Tage trennen
                    positive_days = daily_pnl[daily_pnl > 0]
                    negative_days = daily_pnl[daily_pnl < 0]
                    
                    # Durchschnittliche Tagesgewinne und -verluste
                    avg_daily_gain = positive_days.mean() if len(positive_days) > 0 else 0
                    avg_daily_loss = negative_days.mean() if len(negative_days) > 0 else 0
                    
                    # Prozentuale Anteile der positiven/negativen Tage
                    total_days = len(daily_pnl)
                    positive_days_count = len(positive_days)
                    negative_days_count = len(negative_days)
                    
                    positive_days_pct = (positive_days_count / total_days * 100) if total_days > 0 else 0
                    negative_days_pct = (negative_days_count / total_days * 100) if total_days > 0 else 0
                else:
                    avg_daily_gain = avg_daily_loss = positive_days_pct = negative_days_pct = 0
            else:
                avg_daily_gain = avg_daily_loss = positive_days_pct = negative_days_pct = 0
            
            # Stopouts (Status = 2)
            status_cols = [col for col in trade_data.columns if 'status' in col.lower()]
            stopouts = 0
            if status_cols:
                status_col = status_cols[0]
                stopouts = len(trade_data[trade_data[status_col] == 2])
        else:
            total_profit = avg_profit = win_rate = profit_factor = max_drawdown = peak_value = 0
            stopouts = 0
        
        # Trading Period und Trading Days
        if date_cols:
            start_date = trade_data[date_cols[0]].min()
            end_date = trade_data[date_cols[0]].max()
            trading_days = len(trade_data[date_cols[0]].dt.date.unique())
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-header">
                        <div class="metric-icon">📅</div>
                        <div class="metric-title">TRADING PERIOD</div>
                    </div>
                    <div class="metric-value neutral">{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}</div>
                    <div class="metric-description">Start - End Date</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-tile">
                    <div class="metric-header">
                        <div class="metric-icon">📊</div>
                        <div class="metric-title">TRADING DAYS</div>
                    </div>
                    <div class="metric-value neutral">{trading_days}</div>
                    <div class="metric-description">Anzahl Handelstage</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Kacheln für Key Performance Metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">🪙</div>
                    <div class="metric-title">ACC. RETURN $</div>
                </div>
                <div class="metric-value {'negative' if total_profit < 0 else 'positive'}">${total_profit:,.2f}</div>
                <div class="metric-description">Cumulative return</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">⚡</div>
                    <div class="metric-title">PROFIT FACTOR</div>
                </div>
                <div class="metric-value neutral">{profit_factor:.2f}</div>
                <div class="metric-description">Risk-reward ratio</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📊</div>
                    <div class="metric-title">AVG RETURN $</div>
                </div>
                <div class="metric-value {'negative' if avg_profit < 0 else 'positive'}">${avg_profit:.2f}</div>
                <div class="metric-description">Average per trade</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">🎯</div>
                    <div class="metric-title">WIN %</div>
                </div>
                <div class="metric-value positive">{win_rate:.1f}%</div>
                <div class="metric-description">Success rate</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📊</div>
                    <div class="metric-title">TOTAL TRADES</div>
                </div>
                <div class="metric-value neutral">{total_trades}</div>
                <div class="metric-description">Total number of trades</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Zweite Reihe
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            # Leere Spalte für bessere Ausrichtung
            st.markdown("")
        
        with col2:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📉</div>
                    <div class="metric-title">MAX DRAWDOWN</div>
                </div>
                <div class="metric-value negative">{max_drawdown:.1f}%</div>
                <div class="metric-description">Peak: ${peak_value:,.2f} am {peak_date}<br>Bottom: ${bottom_value:,.2f} am {bottom_date}<br>Max DD: {max_drawdown:.1f}% am {max_dd_date}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">🟢</div>
                    <div class="metric-title">AVG WINNER</div>
                </div>
                <div class="metric-value positive">${avg_winner:.2f}</div>
                <div class="metric-description">Average winning trade</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">🔴</div>
                    <div class="metric-title">AVG LOSER</div>
                </div>
                <div class="metric-value negative">${avg_loser:.2f}</div>
                <div class="metric-description">Average losing trade</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">🔴</div>
                    <div class="metric-title">STOPOUTS</div>
                </div>
                <div class="metric-value neutral">{stopouts}</div>
                <div class="metric-description">Number of stopouts</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 2. Daily Performance Metrics
        st.subheader("📅 Daily Performance Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">🟢</div>
                    <div class="metric-title">AVG DAILY GAIN</div>
                </div>
                <div class="metric-value positive">${avg_daily_gain:,.2f}</div>
                <div class="metric-description">Positive days: {positive_days_pct:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">🔴</div>
                    <div class="metric-title">AVG DAILY LOSS</div>
                </div>
                <div class="metric-value negative">${avg_daily_loss:,.2f}</div>
                <div class="metric-description">Negative days: {negative_days_pct:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📊</div>
                    <div class="metric-title">WINNING DAYS</div>
                </div>
                <div class="metric-value positive">{positive_days_count if 'positive_days_count' in locals() else 0}</div>
                <div class="metric-description">Days with positive P&L</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📉</div>
                    <div class="metric-title">LOSING DAYS</div>
                </div>
                <div class="metric-value negative">{negative_days_count if 'negative_days_count' in locals() else 0}</div>
                <div class="metric-description">Days with negative P&L</div>
            </div>
            """, unsafe_allow_html=True)
        
        # P&L Chart mit Equity Curve
        if profit_cols and date_cols:
            st.markdown("---")
            st.subheader("📈 P&L Chart & Equity Curve")
            
            try:
                # Daten für Chart vorbereiten und bereinigen
                chart_data = trade_data.copy()
                
                # Leere Strings und ungültige Werte in Profit-Spalte bereinigen
                chart_data[profit_cols[0]] = chart_data[profit_cols[0]].replace(['', 'None', 'nan', 'NaN'], pd.NA)
                
                # Leere Werte und ungültige Daten bereinigen
                chart_data = chart_data.dropna(subset=[profit_cols[0], date_cols[0]])
                
                # Sicherstellen, dass Profit-Spalte numerisch ist
                chart_data[profit_cols[0]] = pd.to_numeric(chart_data[profit_cols[0]], errors='coerce')
                chart_data = chart_data.dropna(subset=[profit_cols[0]])
                
                # Nur Daten mit gültigen Werten verarbeiten
                if len(chart_data) == 0:
                    st.warning("⚠️ Keine gültigen Daten für das Chart verfügbar")
                    return
                
                # Datumsspalte als datetime konvertieren
                if chart_data[date_cols[0]].dtype == 'object':
                    chart_data[date_cols[0]] = pd.to_datetime(chart_data[date_cols[0]], errors='coerce')
                
                # Ungültige Datumswerte entfernen
                chart_data = chart_data.dropna(subset=[date_cols[0]])
                
                if pd.api.types.is_datetime64_any_dtype(chart_data[date_cols[0]]) and len(chart_data) > 0:
                    # Nach Datum sortieren
                    chart_data = chart_data.sort_values(date_cols[0])
                    
                    # Kumulative P&L berechnen
                    chart_data['Cumulative_PnL'] = chart_data[profit_cols[0]].cumsum()
                    
                    # Tägliche P&L gruppieren
                    try:
                        daily_pnl = chart_data.groupby(chart_data[date_cols[0]].dt.date)[profit_cols[0]].sum().reset_index()
                        daily_pnl[date_cols[0]] = pd.to_datetime(daily_pnl[date_cols[0]])
                        daily_pnl = daily_pnl.sort_values(date_cols[0])
                        
                        # Kumulative P&L für Equity Curve
                        daily_pnl['Cumulative_PnL'] = daily_pnl[profit_cols[0]].cumsum()
                        
                        # Sicherstellen, dass alle Werte numerisch sind
                        daily_pnl[profit_cols[0]] = pd.to_numeric(daily_pnl[profit_cols[0]], errors='coerce')
                        daily_pnl['Cumulative_PnL'] = pd.to_numeric(daily_pnl['Cumulative_PnL'], errors='coerce')
                        
                        # Ungültige Werte entfernen
                        daily_pnl = daily_pnl.dropna()
                        
                        if len(daily_pnl) == 0:
                            st.warning("⚠️ Keine gültigen Daten für die Chart-Erstellung verfügbar")
                            return
                            
                    except Exception as e:
                        st.error(f"❌ Fehler bei der Datenverarbeitung: {e}")
                        return
                    
                    # Chart erstellen
                    # Einzelnes Chart mit zwei Y-Achsen
                    fig = go.Figure()
                    
                    # Tägliche P&L als Balken (linke Y-Achse) - grün für Gewinne, rot für Verluste
                    colors = ['green' if pd.notna(x) and x >= 0 else 'red' for x in daily_pnl[profit_cols[0]]]
                    
                    fig.add_trace(
                        go.Bar(
                            x=daily_pnl[date_cols[0]],
                            y=daily_pnl[profit_cols[0]],
                            name='Tägliche P&L',
                            marker_color=colors,
                            opacity=0.7,
                            yaxis='y'
                        )
                    )
                    
                    # Equity Curve mit Flächenfüllung
                    fig.add_trace(
                        go.Scatter(
                            x=daily_pnl[date_cols[0]],
                            y=daily_pnl['Cumulative_PnL'],
                            mode='lines',
                            name='Equity Curve',
                            line=dict(color='#2E86AB', width=3),
                            yaxis='y2',
                            fill='tonexty',  # Füllt Fläche unter der Linie
                            fillcolor='rgba(46, 134, 171, 0.2)',  # Transparentes Blau
                            showlegend=True
                        )
                    )
                    
                    # Layout mit zwei Y-Achsen
                    fig.update_layout(
                        height=600,
                        showlegend=True,
                        title_text="Trading Performance: Equity Curve & Tägliche P&L",
                        xaxis=dict(
                            title="Datum",
                            showgrid=True,
                            gridcolor='lightgray'
                        ),
                        yaxis=dict(
                            title="Tägliche P&L ($)",
                            side="left",
                            showgrid=True,
                            gridcolor='lightgray'
                        ),
                        yaxis2=dict(
                            title="Kumulative P&L ($)",
                            side="right",
                            overlaying="y",
                            showgrid=False
                        ),
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.warning("⚠️ Datumsspalte konnte nicht als Datum interpretiert werden")
                    
            except Exception as e:
                st.error(f"❌ Fehler beim Erstellen des Charts: {e}")
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Metriken: {e}")
        st.info("💡 Bitte stellen Sie sicher, dass die Trade-Tabelle verfügbar ist.")
