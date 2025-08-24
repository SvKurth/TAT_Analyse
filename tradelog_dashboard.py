#!/usr/bin/env python3
"""
Tradelog Dashboard - Einfache Oberfläche für SQLite-Tradelogdateien
Zeigt nur die Trade-Tabelle an.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import tempfile
import uuid

# Projektverzeichnis zum Python-Pfad hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from app.services.trade_data_service import TradeDataService
from src.utils import load_config

# Module imports
from modules.overview_page import show_overview_page
from modules.trade_table_page import show_trade_table_page
from modules.api_charts import test_api_connection
from utils.database_utils import is_sqlite_file

# Projektverzeichnis zum Python-Pfad hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from app.services.trade_data_service import TradeDataService
from src.utils import load_config

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
        import tempfile
        import uuid
        
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
    """Zeigt die Metriken-Seite mit Kacheln an."""
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
            else:
                peak_date = "N/A"
                max_dd_date = "N/A"
            
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
        
        # Long/Short Preise und Volumen
        price_long_cols = [col for col in trade_data.columns if 'pricelong' in col.lower() or 'price_long' in col.lower() or 'longprice' in col.lower()]
        price_short_cols = [col for col in trade_data.columns if 'priceshort' in col.lower() or 'price_short' in col.lower() or 'shortprice' in col.lower()]
        quantity_cols = [col for col in trade_data.columns if 'quantity' in col.lower() or 'qty' in col.lower() or 'size' in col.lower()]
        
        # TOTAL LONG COSTS berechnen
        if price_long_cols and quantity_cols:
            price_long_col = price_long_cols[0]
            qty_col = quantity_cols[0]
            
            # Prüfe ob Spalten numerisch sind
            if pd.api.types.is_numeric_dtype(trade_data[price_long_col]) and pd.api.types.is_numeric_dtype(trade_data[qty_col]):
                # Berechne: PriceLong * 100 * Quantity
                total_long_costs = (trade_data[price_long_col] * 100 * trade_data[qty_col]).sum()
                avg_long_price = trade_data[price_long_col].mean()
                max_long_price = trade_data[price_long_col].max()
                min_long_price = trade_data[price_long_col].min()
            else:
                total_long_costs = avg_long_price = max_long_price = min_long_price = 0
        else:
            total_long_costs = avg_long_price = max_long_price = min_long_price = 0
        
        # TOTAL SHORT PREMIUM berechnen
        if price_short_cols and quantity_cols:
            price_short_col = price_short_cols[0]
            qty_col = quantity_cols[0]
            
            if pd.api.types.is_numeric_dtype(trade_data[price_short_col]) and pd.api.types.is_numeric_dtype(trade_data[qty_col]):
                # Berechne: PriceShort * 100 * Quantity
                total_short_premium = (trade_data[price_short_col] * 100 * trade_data[qty_col]).sum()
                avg_short_price = trade_data[price_short_col].mean()
                max_short_price = trade_data[price_short_col].max()
                min_short_price = trade_data[price_short_col].min()
            else:
                total_short_premium = avg_short_price = max_short_price = min_short_price = 0
        else:
            total_short_premium = avg_short_price = max_short_price = min_short_price = 0
        
        # Weitere Volumen-Metriken
        total_volume = total_short_premium - total_long_costs
        avg_trade_size = total_volume / total_trades if total_trades > 0 else 0
        long_short_ratio = total_long_costs / total_short_premium if total_short_premium > 0 else 0
        
        # Premium Capture Rate (P&L / Total Volume)
        if total_volume > 0:
            premium_capture_rate = (total_profit / total_volume) * 100
        else:
            premium_capture_rate = 0
        
        # TOTAL COMMISSION berechnen
        commission_cols = [col for col in trade_data.columns if col.lower() == 'commission']
        commission_close_cols = [col for col in trade_data.columns if col.lower() == 'commissionclose']
        
        total_commission = 0
        
        # Commission Spalte
        if commission_cols:
            commission_col = commission_cols[0]
            if pd.api.types.is_numeric_dtype(trade_data[commission_col]):
                total_commission += trade_data[commission_col].sum()
        
        # CommissionClose Spalte
        if commission_close_cols:
            commission_close_col = commission_close_cols[0]
            if pd.api.types.is_numeric_dtype(trade_data[commission_close_col]):
                total_commission += trade_data[commission_close_col].sum()
        
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
                    <div class="metric-icon">💰</div>
                    <div class="metric-title">TOTAL COMMISSION</div>
                </div>
                <div class="metric-value neutral">${total_commission:,.2f}</div>
                <div class="metric-description">Sum of all commissions</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📉</div>
                    <div class="metric-title">MAX DRAWDOWN</div>
                </div>
                <div class="metric-value negative">{max_drawdown:.1f}%</div>
                <div class="metric-description">Peak: ${peak_value:,.2f} am {peak_date}<br>Max DD: {max_dd_date}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
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
        
        with col5:
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
        
        # 2. Additional Metrics
        st.subheader("📊 Additional Metrics")
        
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        
        with col1:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">🪙</div>
                    <div class="metric-title">TOTAL LONG COSTS</div>
                </div>
                <div class="metric-value neutral">${total_long_costs:,.2f}</div>
                <div class="metric-description">Qty * 100 * PriceLong</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📊</div>
                    <div class="metric-title">AVG LONG PRICE</div>
                </div>
                <div class="metric-value neutral">${avg_long_price:,.2f}</div>
                <div class="metric-description">Average long price</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📈</div>
                    <div class="metric-title">MAX LONG PRICE</div>
                </div>
                <div class="metric-value neutral">${max_long_price:,.2f}</div>
                <div class="metric-description">Highest long price</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📉</div>
                    <div class="metric-title">MIN LONG PRICE</div>
                </div>
                <div class="metric-value neutral">${min_long_price:,.2f}</div>
                <div class="metric-description">Lowest long price</div>
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
        
        with col6:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📊</div>
                    <div class="metric-title">AVG SHORT PRICE</div>
                </div>
                <div class="metric-value neutral">${avg_short_price:,.2f}</div>
                <div class="metric-description">Average short price</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col7:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📈</div>
                    <div class="metric-title">MAX SHORT PRICE</div>
                </div>
                <div class="metric-value neutral">${max_short_price:,.2f}</div>
                <div class="metric-description">Highest short price</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 2.5. Daily Performance Metrics
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
        
        # 3. Trading Volume Metrics
        st.subheader("🪙 Trading Volume Metrics")
        
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        
        with col1:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">💰</div>
                    <div class="metric-title">TOTAL SHORT PREMIUM</div>
                </div>
                <div class="metric-value neutral">${total_short_premium:,.2f}</div>
                <div class="metric-description">Qty * 100 * PriceShort</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📉</div>
                    <div class="metric-title">MIN SHORT PRICE</div>
                </div>
                <div class="metric-value neutral">${min_short_price:,.2f}</div>
                <div class="metric-description">Lowest short price</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📊</div>
                    <div class="metric-title">TOTAL VOLUME</div>
                </div>
                <div class="metric-value neutral">${total_volume:,.2f}</div>
                <div class="metric-description">Short - Long Premiums</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📈</div>
                    <div class="metric-title">AVG TRADE SIZE</div>
                </div>
                <div class="metric-value neutral">${avg_trade_size:,.2f}</div>
                <div class="metric-description">Average premium per trade</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">⚖️</div>
                    <div class="metric-title">LONG/SHORT RATIO</div>
                </div>
                <div class="metric-value neutral">{long_short_ratio:.2f}</div>
                <div class="metric-description">Long vs Short volume</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col6:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">🎯</div>
                    <div class="metric-title">PREMIUM CAPTURE RATE</div>
                </div>
                <div class="metric-value neutral">{premium_capture_rate:.1f}%</div>
                <div class="metric-description">P&L / Total Volume</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col7:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-header">
                    <div class="metric-icon">📊</div>
                    <div class="metric-title">COMMISSION RATE</div>
                </div>
                <div class="metric-value neutral">0.00%</div>
                <div class="metric-description">Commission / Total Volume</div>
            </div>
            """, unsafe_allow_html=True)
        
        # P&L Chart mit Equity Curve
        if profit_cols and date_cols:
            st.markdown("---")
            st.subheader("📈 P&L Chart & Equity Curve")
            
            try:
                # Daten für Chart vorbereiten
                chart_data = trade_data.copy()
                
                # Datumsspalte als datetime konvertieren
                if chart_data[date_cols[0]].dtype == 'object':
                    chart_data[date_cols[0]] = pd.to_datetime(chart_data[date_cols[0]], errors='coerce')
                
                if pd.api.types.is_datetime64_any_dtype(chart_data[date_cols[0]]):
                    # Nach Datum sortieren
                    chart_data = chart_data.sort_values(date_cols[0])
                    
                    # Kumulative P&L berechnen
                    chart_data['Cumulative_PnL'] = chart_data[profit_cols[0]].cumsum()
                    
                    # Tägliche P&L gruppieren
                    daily_pnl = chart_data.groupby(chart_data[date_cols[0]].dt.date)[profit_cols[0]].sum().reset_index()
                    daily_pnl[date_cols[0]] = pd.to_datetime(daily_pnl[date_cols[0]])
                    daily_pnl = daily_pnl.sort_values(date_cols[0])
                    
                    # Kumulative P&L für Equity Curve
                    daily_pnl['Cumulative_PnL'] = daily_pnl[profit_cols[0]].cumsum()
                    
                    # Chart erstellen
                    import plotly.graph_objects as go
                    
                    # Einzelnes Chart mit zwei Y-Achsen
                    fig = go.Figure()
                    
                    # Tägliche P&L als Balken (linke Y-Achse) - grün für Gewinne, rot für Verluste
                    colors = ['green' if x >= 0 else 'red' for x in daily_pnl[profit_cols[0]]]
                    
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
                        title_x=0.5,
                        hovermode='x unified',
                        
                        # Linke Y-Achse (für Balken)
                        yaxis=dict(
                            title=dict(text="Tägliche P&L ($)", font=dict(color="black", size=14)),
                            tickfont=dict(color="black", size=12),
                            side="left",
                            showgrid=True,
                            gridcolor="lightgray",
                            gridwidth=1,
                            zeroline=True,
                            zerolinecolor="black",
                            zerolinewidth=1,
                            tickformat=",.0f",
                            separatethousands=True
                        ),
                        
                        # Rechte Y-Achse (für Equity Curve)
                        yaxis2=dict(
                            title=dict(text="Equity ($)", font=dict(color="#2E86AB", size=14)),
                            tickfont=dict(color="#2E86AB", size=12),
                            side="right",
                            overlaying="y",
                            showgrid=False,
                            zeroline=False,
                            tickformat=",.0f",
                            separatethousands=True
                        ),
                        
                        # X-Achse optimieren
                        xaxis=dict(
                            title=dict(text="Datum", font=dict(size=14)),
                            tickfont=dict(size=12),
                            showgrid=True,
                            gridcolor="lightgray",
                            gridwidth=1
                        )
                    )
                    
                    # Chart anzeigen
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Kalenderwochen-Verdichtung als Bar-Chart
                    if len(daily_pnl) > 0:
                        st.markdown("---")
                        st.caption("📊 **Kalenderwochen-Verdichtung als Bar-Chart**")
                        
                        # Erstelle Kalenderwochen-Gruppierung für das Chart
                        daily_pnl_chart = daily_pnl.copy()
                        daily_pnl_chart['Week'] = daily_pnl_chart[date_cols[0]].dt.isocalendar().week
                        daily_pnl_chart['Year'] = daily_pnl_chart[date_cols[0]].dt.isocalendar().year
                        daily_pnl_chart['Week_Label'] = daily_pnl_chart['Year'].astype(str) + '-KW' + daily_pnl_chart['Week'].astype(str).str.zfill(2)
                        
                        weekly_chart_data = daily_pnl_chart.groupby('Week_Label')[profit_cols[0]].sum().reset_index()
                        weekly_chart_data = weekly_chart_data.sort_values('Week_Label')
                        
                        # Erstelle Bar-Chart
                        fig_weekly = go.Figure()
                        
                        # Farben basierend auf Profit/Loss
                        colors = ['#28a745' if x >= 0 else '#dc3545' for x in weekly_chart_data[profit_cols[0]]]
                        
                        fig_weekly.add_trace(go.Bar(
                            x=weekly_chart_data['Week_Label'],
                            y=weekly_chart_data[profit_cols[0]],
                            marker_color=colors,
                            name='Wöchentlicher P&L',
                            hovertemplate='<b>%{x}</b><br>P&L: %{y:,.2f}€<extra></extra>'
                        ))
                        
                        fig_weekly.update_layout(
                            title="Wöchentliche P&L-Übersicht",
                            xaxis_title="Kalenderwoche",
                            yaxis_title="P&L (€)",
                            height=400,
                            showlegend=False,
                            margin=dict(l=50, r=50, t=80, b=50),
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                        
                        # X-Achse rotieren für bessere Lesbarkeit
                        fig_weekly.update_xaxes(tickangle=45, gridcolor='lightgray', gridwidth=1)
                        fig_weekly.update_yaxes(gridcolor='lightgray', gridwidth=1)
                        
                        st.plotly_chart(fig_weekly, use_container_width=True)
                    
                    # Monats-Verdichtung als Bar-Chart
                    if len(daily_pnl) > 0:
                        st.markdown("---")
                        st.caption("📅 **Monats-Verdichtung als Bar-Chart**")
                        
                        # Erstelle Monats-Gruppierung für das Chart
                        daily_pnl_monthly = daily_pnl.copy()
                        daily_pnl_monthly['Month'] = daily_pnl_monthly[date_cols[0]].dt.to_period('M')
                        monthly_chart_data = daily_pnl_monthly.groupby('Month')[profit_cols[0]].sum().reset_index()
                        monthly_chart_data['Month_Label'] = monthly_chart_data['Month'].dt.strftime('%b %Y')
                        monthly_chart_data = monthly_chart_data.sort_values('Month')
                        
                        # Erstelle Monats-Bar-Chart
                        fig_monthly = go.Figure()
                        
                        # Farben basierend auf Profit/Loss
                        colors_monthly = ['#28a745' if x >= 0 else '#dc3545' for x in monthly_chart_data[profit_cols[0]]]
                        
                        fig_monthly.add_trace(go.Bar(
                            x=monthly_chart_data['Month_Label'],
                            y=monthly_chart_data[profit_cols[0]],
                            marker_color=colors_monthly,
                            name='Monatlicher P&L',
                            hovertemplate='<b>%{x}</b><br>P&L: %{y:,.2f}€<extra></extra>'
                        ))
                        
                        fig_monthly.update_layout(
                            title="Monatliche P&L-Übersicht",
                            xaxis_title="Monat",
                            yaxis_title="P&L (€)",
                            height=350,
                            showlegend=False,
                            margin=dict(l=50, r=50, t=80, b=50),
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                        
                        # X-Achse rotieren für bessere Lesbarkeit
                        fig_monthly.update_xaxes(tickangle=45, gridcolor='lightgray', gridwidth=1)
                        fig_monthly.update_yaxes(gridcolor='lightgray', gridwidth=1)
                        
                        st.plotly_chart(fig_monthly, use_container_width=True)
                    
                    # Wochentag-Verdichtung als Bar-Chart
                    if len(daily_pnl) > 0:
                        st.markdown("---")
                        st.caption("📅 **Wochentag-Verdichtung als Bar-Chart**")
                        
                        # Erstelle Wochentag-Gruppierung für das Chart
                        daily_pnl_weekday = daily_pnl.copy()
                        daily_pnl_weekday['Weekday'] = daily_pnl_weekday[date_cols[0]].dt.dayofweek
                        daily_pnl_weekday['Weekday_Name'] = daily_pnl_weekday[date_cols[0]].dt.day_name()
                        
                        # Deutsche Wochentage
                        weekday_names_de = {
                            0: 'Montag', 1: 'Dienstag', 2: 'Mittwoch', 
                            3: 'Donnerstag', 4: 'Freitag', 5: 'Samstag', 6: 'Sonntag'
                        }
                        daily_pnl_weekday['Weekday_DE'] = daily_pnl_weekday['Weekday'].map(weekday_names_de)
                        
                        weekday_chart_data = daily_pnl_weekday.groupby(['Weekday', 'Weekday_DE'])[profit_cols[0]].sum().reset_index()
                        weekday_chart_data = weekday_chart_data.sort_values('Weekday')
                        
                        # Erstelle Wochentag-Bar-Chart
                        fig_weekday = go.Figure()
                        
                        # Farben basierend auf Profit/Loss
                        colors_weekday = ['#28a745' if x >= 0 else '#dc3545' for x in weekday_chart_data[profit_cols[0]]]
                        
                        fig_weekday.add_trace(go.Bar(
                            x=weekday_chart_data['Weekday_DE'],
                            y=weekday_chart_data[profit_cols[0]],
                            marker_color=colors_weekday,
                            name='Wochentag P&L',
                            hovertemplate='<b>%{x}</b><br>P&L: %{y:,.2f}€<extra></extra>'
                        ))
                        
                        fig_weekday.update_layout(
                            title="Wochentag P&L-Übersicht",
                            xaxis_title="Wochentag",
                            yaxis_title="P&L (€)",
                            height=350,
                            showlegend=False,
                            margin=dict(l=50, r=50, t=80, b=50),
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                        
                        # X-Achse rotieren für bessere Lesbarkeit
                        fig_weekday.update_xaxes(tickangle=45, gridcolor='lightgray', gridwidth=1)
                        fig_weekday.update_yaxes(gridcolor='lightgray', gridwidth=1)
                        
                        st.plotly_chart(fig_weekday, use_container_width=True)
                    
                    # Verdichtungen unter dem P&L Chart - KOMPAKT
                    st.markdown("---")
                    st.subheader("📊 Verdichtungen")
                    
                    # Zusätzliche Statistiken
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        initial_pnl = daily_pnl['Cumulative_PnL'].iloc[0] if len(daily_pnl) > 0 else 0
                        st.metric("Start P&L", f"${initial_pnl:,.2f}")
                    
                    with col2:
                        final_pnl = daily_pnl['Cumulative_PnL'].iloc[-1] if len(daily_pnl) > 0 else 0
                        st.metric("End P&L", f"${final_pnl:,.2f}")
                    
                    with col3:
                        total_return = final_pnl - initial_pnl
                        st.metric("Gesamt P&L", f"${total_return:,.2f}")
                    
                    with col4:
                        max_pnl = daily_pnl['Cumulative_PnL'].max()
                        current_drawdown = ((final_pnl - max_pnl) / max_pnl) * 100 if max_pnl > 0 else 0
                        st.metric("Aktueller Drawdown", f"{current_drawdown:.1f}%")
                    
                else:
                    st.warning("Datumsspalte konnte nicht als Datum interpretiert werden")
                    
            except Exception as e:
                st.error(f"Fehler beim Erstellen des P&L Charts: {e}")
                st.info("Stellen Sie sicher, dass Profit- und Datumsspalten verfügbar sind")
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Metriken: {e}")
        st.info("💡 Bitte stellen Sie sicher, dass die Trade-Tabelle verfügbar ist.")

def show_tat_navigator_page(data_loader, db_path):
    """Zeigt die TAT Tradenavigator-Seite an."""
    # Import für plotly und zusätzliche Module
    import plotly.graph_objects as go
    import numpy as np
    from datetime import datetime, timedelta
    import warnings
    import requests
    import json
    
    warnings.filterwarnings('ignore')
    
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
        
        # Profit-Spalten identifizieren
        profit_cols = [col for col in trade_data.columns if 'profit' in col.lower() or 'pnl' in col.lower()]
        
        # Datumsspalten identifizieren
        date_cols = [col for col in trade_data.columns if 'date' in col.lower() or 'datum' in col.lower()]
        
        # Session State für Navigation initialisieren
        if 'current_date_index' not in st.session_state:
            st.session_state.current_date_index = 0
        
        if 'selected_row_index' not in st.session_state:
            st.session_state.selected_row_index = None
        
        if 'date_range_mode' not in st.session_state:
            st.session_state.date_range_mode = False
        
        # Vorfilter für TradeType und Template
        st.subheader("🔍 Vorfilter")
        
        # Verfügbare TradeTypes und Templates ermitteln
        available_trade_types = ['Alle']
        available_templates = ['Alle']
        
        if 'TradeType' in trade_data.columns:
            available_trade_types.extend(sorted(trade_data['TradeType'].dropna().unique().tolist()))
        if 'Template' in trade_data.columns:
            available_templates.extend(sorted(trade_data['Template'].dropna().unique().tolist()))
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_trade_type = st.selectbox(
                "📊 Trade Type:",
                available_trade_types,
                key="trade_type_filter_main"
            )
        
        with col2:
            selected_template = st.selectbox(
                "📋 Template:",
                available_templates,
                key="template_filter_main"
            )
        
        # Daten nach Vorfilter filtern
        filtered_trade_data = trade_data.copy()
        
        if selected_trade_type != 'Alle':
            filtered_trade_data = filtered_trade_data[filtered_trade_data['TradeType'] == selected_trade_type]
        
        if selected_template != 'Alle':
            filtered_trade_data = filtered_trade_data[filtered_trade_data['Template'] == selected_template]
        
        # Verfügbare Daten nach Vorfilter ermitteln
        available_dates = []
        if date_cols and len(filtered_trade_data) > 0:
            date_col = date_cols[0]
            if filtered_trade_data[date_col].dtype == 'object':
                filtered_trade_data[date_col] = pd.to_datetime(filtered_trade_data[date_col], errors='coerce')
            available_dates = sorted(filtered_trade_data[date_col].dt.date.unique())
        
        if not available_dates:
            st.warning(f"⚠️ Keine Daten für die ausgewählten Filter gefunden!")
            st.info(f"📊 Gefilterte Daten: {len(filtered_trade_data)} Trades")
            return
        
        # Filter-Info anzeigen
        st.success(f"✅ Gefilterte Daten: {len(filtered_trade_data)} Trades ({len(available_dates)} Tage)")
        
        # Datumsbereich-Modus Auswahl
        st.subheader("🗓️ Datumsauswahl")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📅 Einzeltag", key="single_day_btn", use_container_width=True):
                st.session_state.date_range_mode = False
                st.rerun()
        
        with col2:
            if st.button("📊 Datumsbereich", key="date_range_btn", use_container_width=True):
                st.session_state.date_range_mode = True
                st.rerun()
        
        # Aktueller Modus anzeigen
        if st.session_state.date_range_mode:
            st.info("📊 **Datumsbereich-Modus aktiv** - Wählen Sie Start- und Enddatum")
        else:
            st.info("📅 **Einzeltag-Modus aktiv** - Wählen Sie ein spezifisches Datum")
        
        # Datumsauswahl basierend auf Modus
        if st.session_state.date_range_mode:
            # Datumsbereich-Auswahl
            st.subheader("📊 Datumsbereich auswählen")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "📅 Startdatum:",
                    value=available_dates[0] if available_dates else None,
                    min_value=available_dates[0] if available_dates else None,
                    max_value=available_dates[-1] if available_dates else None,
                    key="start_date_selector"
                )
            
            with col2:
                end_date = st.date_input(
                    "📅 Enddatum:",
                    value=available_dates[-1] if available_dates else None,
                    min_value=available_dates[0] if available_dates else None,
                    max_value=available_dates[-1] if available_dates else None,
                    key="end_date_selector"
                )
            
            # Validierung: Enddatum muss nach Startdatum sein
            if start_date and end_date and start_date > end_date:
                st.error("❌ Enddatum muss nach Startdatum liegen!")
                return
            
            # Trades für Datumsbereich laden
            if start_date and end_date:
                if date_cols:
                    date_col = date_cols[0]
                    daily_trades = filtered_trade_data[
                        (filtered_trade_data[date_col].dt.date >= start_date) & 
                        (filtered_trade_data[date_col].dt.date <= end_date)
                    ].copy()
                    current_date = start_date
                else:
                    daily_trades = pd.DataFrame()
                    current_date = available_dates[0] if available_dates else None
            else:
                daily_trades = pd.DataFrame()
                current_date = available_dates[0] if available_dates else None
        
        else:
            # Einzeltag-Auswahl
            st.subheader("📅 Einzeltag auswählen")
            
            current_date = available_dates[st.session_state.current_date_index] if st.session_state.current_date_index < len(available_dates) else available_dates[0]
            
            selected_date = st.date_input(
                "📅 Wählen Sie ein Datum:",
                value=current_date,
                min_value=available_dates[0] if available_dates else None,
                max_value=available_dates[-1] if available_dates else None,
                key="date_selector"
            )
            
            # Update current_date_index wenn sich die Auswahl ändert
            if selected_date != current_date:
                try:
                    selected_date_index = available_dates.index(selected_date)
                    if selected_date_index != st.session_state.current_date_index:
                        st.session_state.current_date_index = selected_date_index
                        st.rerun()
                except ValueError:
                    # Falls das Datum nicht in available_dates ist, suche das nächste
                    for i, date in enumerate(available_dates):
                        if date >= selected_date:
                            st.session_state.current_date_index = i
                            st.rerun()
                            break
            
            # Aktualisiere current_date und daily_trades
            current_date = available_dates[st.session_state.current_date_index]
            if date_cols:
                date_col = date_cols[0]
                daily_trades = filtered_trade_data[filtered_trade_data[date_col].dt.date == current_date].copy()
            else:
                daily_trades = pd.DataFrame()
        
        # Navigation-Buttons
        if len(available_dates) > 1:
            st.subheader("🧭 Navigation")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("⏮️ Erster Tag", key="first_day"):
                    st.session_state.current_date_index = 0
                    st.rerun()
            
            with col2:
                if st.button("⬅️ Vorheriger Tag", key="prev_day"):
                    if st.session_state.current_date_index > 0:
                        st.session_state.current_date_index -= 1
                        st.rerun()
            
            with col3:
                if st.button("➡️ Nächster Tag", key="next_day"):
                    if st.session_state.current_date_index < len(available_dates) - 1:
                        st.session_state.current_date_index += 1
                        st.rerun()
            
            with col4:
                if st.button("⏭️ Letzter Tag", key="last_day"):
                    st.session_state.current_date_index = len(available_dates) - 1
                    st.rerun()
        
        # Alle Trades in einer Tabelle
        if len(daily_trades) > 0:
            # Erfolgsmeldung mit Anzahl der Trades
            if st.session_state.date_range_mode:
                st.success(f"✅ {len(daily_trades)} Trades für {start_date.strftime('%d.%m.%Y')} bis {end_date.strftime('%d.%m.%Y')} gefunden")
            else:
                st.success(f"✅ {len(daily_trades)} Trades für {current_date.strftime('%d.%m.%Y')} gefunden")
            
            # Tabelle vorbereiten
            display_trades = daily_trades.copy()
            
            # Datum formatieren
            if date_cols:
                date_col = date_cols[0]
                display_trades['Date'] = display_trades[date_col].dt.strftime('%d.%m.%Y')
            
            # Metriken oberhalb der Tabelle
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_trades = len(daily_trades)
                st.metric("📈 Trades", total_trades)
            
            with col2:
                if profit_cols:
                    total_pnl = daily_trades[profit_cols[0]].sum()
                    st.metric("💰 P&L Gesamt", f"{total_pnl:.2f}")
                else:
                    st.metric("💰 P&L Gesamt", "N/A")
            
            with col3:
                if profit_cols and 'Qty' in daily_trades.columns:
                    # Normalisierte P&L über alle Trades
                    normalized_values = daily_trades.apply(
                        lambda row: row[profit_cols[0]] / row['Qty'] if pd.notna(row[profit_cols[0]]) and pd.notna(row['Qty']) and row['Qty'] != 0 else 0, 
                        axis=1
                    )
                    total_pnl_normalized = normalized_values.sum()
                    st.metric("💰 P&L norm. Gesamt", f"{total_pnl_normalized:.2f}")
                else:
                    st.metric("💰 P&L norm. Gesamt", "N/A")
            
            with col4:
                # Gestoppte Trades zählen
                if 'Status' in daily_trades.columns:
                    stopped_trades = daily_trades[daily_trades['Status'] == 'Stopped']
                    total_stopped = len(stopped_trades)
                    st.metric("🛑 Gestoppte Trades", total_stopped)
                else:
                    st.metric("🛑 Gestoppte Trades", "N/A")
            
            # Überschrift für Tabelle
            if st.session_state.date_range_mode:
                st.subheader(f"📋 Alle Trades: {start_date.strftime('%d.%m.%Y')} bis {end_date.strftime('%d.%m.%Y')}")
            else:
                st.subheader(f"📋 Alle Trades des Tages: {current_date.strftime('%d.%m.%Y')}")
            
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
                'TimeOpened': '🕐 Eröffnung',
                'PriceOpen': '💰 Preis Eröffnung',
                'TimeClosed': '🕐 Schließung',
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
                total_pnl = daily_trades[profit_cols[0]].sum()
                
                # Normalisierte P&L Summe berechnen
                total_pnl_normalized = 0
                if 'Qty' in daily_trades.columns:
                    normalized_values = daily_trades.apply(
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
            if 'ShortPut' in daily_trades.columns:
                for idx, trade in daily_trades.iterrows():
                    if pd.notna(trade['ShortPut']) and trade['ShortPut'] != 0:
                        trade_type = trade.get('TradeType', 'N/A')
                        time_opened = trade.get('TimeOpened', 'N/A')
                        short_options.append({
                            'row_index': idx,
                            'type': 'P',
                            'strike': int(trade['ShortPut']),
                            'trade_info': trade.to_dict(),
                            'label': f"🔴 Put {trade['ShortPut']:.0f} - {trade_type} - {time_opened}"
                        })
            
            # Short Call Optionen sammeln
            if 'ShortCall' in daily_trades.columns:
                for idx, trade in daily_trades.iterrows():
                    if pd.notna(trade['ShortCall']) and trade['ShortCall'] != 0:
                        trade_type = trade.get('TradeType', 'N/A')
                        time_opened = trade.get('TimeOpened', 'N/A')
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
                        date_col = date_cols[0]
                        if st.session_state.date_range_mode:
                            chart_date = start_date
                        else:
                            chart_date = current_date
                        
                        api_date = chart_date.strftime('%Y-%m-%d')
                        
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
                        if 'TimeOpened' in trade_info and pd.notna(trade_info['TimeOpened']):
                            st.metric("🕐 Eröffnung", str(trade_info['TimeOpened']))
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
            st.warning(f"⚠️ Keine Trades für {current_date.strftime('%d.%m.%Y')} gefunden!")
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der TAT Tradenavigator-Seite: {e}")
        st.info("💡 Bitte stellen Sie sicher, dass die Trade-Tabelle verfügbar ist.")

# API-Funktionen für Live-Daten
@st.cache_data(ttl=3600)  # Cache für 1 Stunde
def get_option_price_data(asset: str, date: str, option_type: str, strike: int) -> dict:
    """Lädt Optionspreis-Daten von der API mit Caching"""
    try:
        # API URL konstruieren
        symbol = f"-{option_type}{strike}"
        url = f"https://api.0dtespx.com/optionPrice?asset={asset}&date={date}&interval=1&symbol={symbol}"
        
        # API Request mit Timeout
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            st.warning(f"⚠️ Optionspreis API Response Status: {response.status_code}")
            return None
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ Optionspreis API Request Fehler: {e}")
        return None
    except json.JSONDecodeError as e:
        st.warning(f"⚠️ Optionspreis JSON Parse Fehler: {e}")
        return None
    except Exception as e:
        st.warning(f"⚠️ Optionspreis Allgemeiner Fehler: {e}")
        return None

@st.cache_data(ttl=3600)  # Cache für 1 Stunde
def get_spx_vix_data(date: str) -> list:
    """Lädt SPX und VIX Daten von der API mit Caching"""
    try:
        # API URL konstruieren
        url = f"https://api.0dtespx.com/aggregateData?series=spx,vix&date={date}&interval=1"
        
        # API Request
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            st.warning(f"⚠️ API Response Status: {response.status_code}")
            return None
        
        data = response.json()
        
        # Verschiedene mögliche Datenstrukturen prüfen
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], list):
                return data['data']
            elif 'results' in data and isinstance(data['results'], list):
                return data['results']
            elif 'spx' in data and 'vix' in data:
                spx_data = data.get('spx', [])
                vix_data = data.get('vix', [])
                return spx_data if len(spx_data) > len(vix_data) else vix_data
            else:
                st.warning(f"⚠️ Unbekannte Datenstruktur: {list(data.keys())}")
                return None
        else:
            st.warning(f"⚠️ Unerwarteter Datentyp: {type(data)}")
            return None
        
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ API Request Fehler: {e}")
        return None
    except json.JSONDecodeError as e:
        st.warning(f"⚠️ JSON Parse Fehler: {e}")
        return None
    except Exception as e:
        st.warning(f"⚠️ Allgemeiner Fehler: {e}")
        return None

def create_options_price_chart(option_data: dict, option_type: str, strike: int, trade_date: str, trade_info: dict = None) -> go.Figure:
    """Erstellt einen Chart mit Optionspreisen und SPX-Daten"""
    try:
        if not option_data:
            return None
        
        # SPX-Daten laden für Integration
        spx_data = get_spx_vix_data(trade_date)
        spx_timestamps = []
        spx_prices = []
        
        if spx_data:
            for entry in spx_data:
                if isinstance(entry, dict) and 'dateTime' in entry and 'spx' in entry:
                    try:
                        timestamp = entry['dateTime']
                        if isinstance(timestamp, (int, float)):
                            if timestamp > 1e10:  # Millisekunden
                                dt = datetime.fromtimestamp(timestamp / 1000)
                            else:  # Sekunden
                                dt = datetime.fromtimestamp(timestamp)
                        else:
                            dt = pd.to_datetime(timestamp)
                        
                        spx_price = float(entry['spx'])
                        if spx_price > 0:
                            spx_timestamps.append(dt)
                            spx_prices.append(spx_price)
                    except (ValueError, TypeError, OSError):
                        continue
        
        # Optionspreis-Daten verarbeiten
        price_data = None
        
        # Verschiedene mögliche Datenstrukturen prüfen
        if 'data' in option_data and option_data['data']:
            price_data = option_data['data']
        elif isinstance(option_data, list) and option_data:
            price_data = option_data
        elif 'prices' in option_data and option_data['prices']:
            price_data = option_data['prices']
        elif 'results' in option_data and option_data['results']:
            price_data = option_data['results']
        
        if not price_data:
            return None
        
        # Zeitstempel und Preise extrahieren
        timestamps = []
        prices = []
        
        for entry in price_data:
            if not isinstance(entry, dict):
                continue
                
            timestamp = entry.get('dateTime') or entry.get('timestamp') or entry.get('time') or entry.get('date')
            price = entry.get('price') or entry.get('value') or entry.get('close')
            
            if timestamp is not None and price is not None:
                try:
                    if isinstance(timestamp, (int, float)):
                        dt = datetime.fromtimestamp(timestamp)
                    else:
                        dt = pd.to_datetime(timestamp)
                    
                    price_float = abs(float(price))
                    timestamps.append(dt)
                    prices.append(price_float)
                except (ValueError, TypeError, OSError):
                    continue
        
        if not timestamps or not prices:
            return None
        
        # Chart erstellen
        fig = go.Figure()
        
        # Optionspreis-Linie (linke Y-Achse)
        option_name = "Put" if option_type == 'P' else "Call"
        line_color = '#ef476f' if option_type == 'P' else '#06d6a0'
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=prices,
            mode='lines',
            name=f'{option_name} {strike}',
            line=dict(color=line_color, width=2),
            fill='tonexty',
            fillcolor=line_color,
            opacity=0.2,
            yaxis='y',
            hovertemplate='<b>%{x|%H:%M:%S}</b><br>Optionspreis: %{y:.3f}<extra></extra>'
        ))
        
        # SPX-Linie hinzufügen (rechte Y-Achse)
        if spx_timestamps and spx_prices:
            fig.add_trace(go.Scatter(
                x=spx_timestamps,
                y=spx_prices,
                mode='lines',
                name='SPX',
                line=dict(color='#1f77b4', width=2),
                yaxis='y2',
                hovertemplate='<b>%{x|%H:%M:%S}</b><br>SPX: %{y:,.0f}<extra></extra>'
            ))
        
        # Trade-Marker hinzufügen
        if trade_info:
            # Eröffnungszeit
            if 'TimeOpened' in trade_info and pd.notna(trade_info['TimeOpened']):
                try:
                    time_opened_str = str(trade_info['TimeOpened'])
                    if ':' in time_opened_str and len(time_opened_str) <= 5:
                        combined_datetime = f"{trade_date} {time_opened_str}:00"
                        entry_time = pd.to_datetime(combined_datetime)
                        
                        # Eröffnungspreis
                        entry_price = 0.0
                        if 'PriceOpen' in trade_info and pd.notna(trade_info['PriceOpen']):
                            entry_price = abs(float(trade_info['PriceOpen']))
                        
                        if entry_price > 0:
                            fig.add_trace(go.Scatter(
                                x=[entry_time],
                                y=[entry_price],
                                mode='markers',
                                name='🚀 Einstieg',
                                marker=dict(
                                    symbol='triangle-up',
                                    size=15,
                                    color='#00ff00',
                                    line=dict(color='#000000', width=2)
                                ),
                                yaxis='y',
                                hovertemplate='<b>🚀 Einstieg</b><br>Zeit: %{x|%H:%M:%S}<br>Preis: <b>%{y:.3f}</b><extra></extra>',
                                showlegend=False
                            ))
                except Exception:
                    pass
            
            # Schließungszeit
            if 'TimeClosed' in trade_info and pd.notna(trade_info['TimeClosed']):
                try:
                    time_closed_str = str(trade_info['TimeClosed'])
                    if ':' in time_closed_str and len(time_closed_str) <= 5:
                        combined_datetime = f"{trade_date} {time_closed_str}:00"
                        exit_time = pd.to_datetime(combined_datetime)
                        
                        # Schließungspreis
                        exit_price = 0.0
                        if 'PriceClose' in trade_info and pd.notna(trade_info['PriceClose']):
                            exit_price = abs(float(trade_info['PriceClose']))
                        
                        if exit_price > 0:
                            fig.add_trace(go.Scatter(
                                x=[exit_time],
                                y=[exit_price],
                                mode='markers',
                                name='🔚 Schließung',
                                marker=dict(
                                    symbol='triangle-down',
                                    size=15,
                                    color='#ff0000',
                                    line=dict(color='#000000', width=2)
                                ),
                                yaxis='y',
                                hovertemplate='<b>🔚 Schließung</b><br>Zeit: %{x|%H:%M:%S}<br>Preis: <b>%{y:.3f}</b><extra></extra>',
                                showlegend=False
                            ))
                except Exception:
                    pass
            
            # Stoppreis
            if 'PriceStopTarget' in trade_info and pd.notna(trade_info['PriceStopTarget']) and trade_info['PriceStopTarget'] > 0:
                stop_price = abs(float(trade_info['PriceStopTarget']))
                fig.add_hline(
                    y=stop_price,
                    line_dash="dash",
                    line_color="red",
                    line_width=3,
                    annotation_text=f"Stoppreis: {stop_price:.2f}",
                    annotation_position="top right",
                    annotation=dict(
                        font=dict(size=16, color="red"),
                        bgcolor="rgba(255, 255, 255, 0.8)",
                        bordercolor="red",
                        borderwidth=1
                    )
                )
        
        # Chart-Layout
        fig.update_layout(
            title=f"{option_name} {strike} Optionspreis + SPX - {trade_date}",
            xaxis_title="Zeit",
            yaxis_title="Optionspreis ($)",
            xaxis=dict(
                type='date',
                showgrid=True,
                gridcolor='#f0f0f0',
                tickformat='%H:%M',
                rangeslider=dict(visible=True),
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1h", step="hour", stepmode="backward"),
                        dict(count=2, label="2h", step="hour", stepmode="backward"),
                        dict(count=4, label="4h", step="hour", stepmode="backward"),
                        dict(count=1, label="1d", step="day", stepmode="backward"),
                        dict(step="all", label="Alle")
                    ])
                )
            ),
            yaxis=dict(
                title="Optionspreis ($)",
                showgrid=True,
                gridcolor='#f0f0f0',
                zeroline=False,
                tickformat='.3f',
                tickmode='auto',
                nticks=10,
                side='left'
            ),
            yaxis2=dict(
                title="SPX",
                overlaying='y',
                side='right',
                showgrid=False,
                zeroline=False,
                tickformat=',.0f',
                tickmode='auto',
                nticks=6,
                tickfont=dict(color='#1f77b4')
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='#ccc',
                font_size=12
            )
        )
        
        return fig
        
    except Exception as e:
        st.error(f"❌ Fehler beim Erstellen des Optionspreis-Charts: {e}")
        return None

def create_spx_vix_chart(data: list, trade_date: str, trade_info: dict = None) -> go.Figure:
    """Erstellt Charts für SPX und VIX Daten"""
    try:
        if not data or not isinstance(data, list):
            st.warning("⚠️ Keine gültigen SPX/VIX Daten verfügbar")
            return None
        
        # Chart erstellen
        fig = go.Figure()
        
        # Daten aus dem Array extrahieren
        timestamps = []
        spx_prices = []
        vix_prices = []
        
        for entry in data:
            if isinstance(entry, dict):
                timestamp = (entry.get('dateTime') or 
                           entry.get('timestamp') or 
                           entry.get('time') or 
                           entry.get('date'))
                
                spx_price = (entry.get('spx') or 
                           entry.get('SPX') or 
                           entry.get('price') or 
                           entry.get('value'))
                
                vix_price = (entry.get('vix') or 
                           entry.get('VIX') or 
                           entry.get('volatility') or 
                           entry.get('vix_value'))
                
                if timestamp is not None and spx_price is not None and vix_price is not None:
                    try:
                        if isinstance(timestamp, (int, float)):
                            if timestamp > 1e10:  # Millisekunden
                                dt = datetime.fromtimestamp(timestamp / 1000)
                            else:  # Sekunden
                                dt = datetime.fromtimestamp(timestamp)
                        else:
                            dt = pd.to_datetime(timestamp)
                        
                        spx_float = float(spx_price)
                        vix_float = float(vix_price)
                        
                        if spx_float > 0 and vix_float > 0:
                            timestamps.append(dt)
                            spx_prices.append(spx_float)
                            vix_prices.append(vix_float)
                    except (ValueError, TypeError, OSError):
                        continue
        
        if not timestamps or not spx_prices or not vix_prices:
            st.warning(f"⚠️ Keine gültigen SPX/VIX Datenpunkte gefunden")
            return None
        
        # SPX Daten hinzufügen
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=spx_prices,
            mode='lines',
            name='SPX',
            line=dict(color='#1f77b4', width=2),
            yaxis='y',
            hovertemplate='<b>%{x|%H:%M:%S}</b><br>SPX: %{y:,.2f}<extra></extra>'
        ))
        
        # VIX Daten hinzufügen
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=vix_prices,
            mode='lines',
            name='VIX',
            line=dict(color='#ff7f0e', width=2),
            yaxis='y2',
            hovertemplate='<b>%{x|%H:%M:%S}</b><br>VIX: %{y:.2f}<extra></extra>'
        ))
        
        # Trade-Marker hinzufügen
        if trade_info and 'TimeOpened' in trade_info and pd.notna(trade_info['TimeOpened']):
            try:
                time_opened_str = str(trade_info['TimeOpened'])
                if ':' in time_opened_str and len(time_opened_str) <= 5:
                    combined_datetime = f"{trade_date} {time_opened_str}:00"
                    entry_time = pd.to_datetime(combined_datetime)
                    
                    fig.add_vline(
                        x=entry_time,
                        line_dash="dash",
                        line_color="red",
                        line_width=2,
                        annotation_text="Trade Eröffnung",
                        annotation_position="top right"
                    )
            except Exception:
                pass
        
        # Layout konfigurieren
        fig.update_layout(
            title=f"SPX & VIX - {trade_date}",
            xaxis_title="Zeit",
            yaxis_title="SPX",
            yaxis=dict(
                title="SPX",
                showgrid=True,
                gridcolor='#f0f0f0',
                zeroline=False,
                tickformat=',.0f',
                tickmode='auto',
                nticks=8,
                side='left'
            ),
            yaxis2=dict(
                title="VIX",
                overlaying='y',
                side='right',
                showgrid=False,
                zeroline=False,
                tickformat='.1f',
                tickmode='auto',
                nticks=6,
                tickfont=dict(color='#ff7f0e')
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                type='date',
                showgrid=True,
                gridcolor='#f0f0f0',
                tickformat='%H:%M',
                tickmode='auto',
                nticks=10
            ),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='#ccc',
                font_size=12
            )
        )
        
        return fig
        
    except Exception as e:
        st.error(f"❌ Fehler beim Erstellen des SPX/VIX Charts: {e}")
        return None

def test_api_connection():
    """Testet die API-Verbindung mit SPX/VIX und Optionspreis-Daten"""
    try:
        st.subheader("🧪 API-Verbindungstest")
        
        # Test 1: SPX/VIX API
        st.markdown("**1. SPX/VIX API Test:**")
        spx_vix_url = "https://api.0dtespx.com/aggregateData?series=spx,vix&date=2025-02-14&interval=1"
        
        with st.spinner("🔄 Teste SPX/VIX API..."):
            response = requests.get(spx_vix_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                st.success(f"✅ SPX/VIX API erfolgreich! Status: {response.status_code}")
                st.info(f"📊 Datenstruktur: {type(data)}")
                if isinstance(data, dict):
                    st.info(f"📋 Verfügbare Keys: {list(data.keys())}")
                elif isinstance(data, list):
                    st.info(f"📋 Anzahl Datenpunkte: {len(data)}")
                    if len(data) > 0:
                        st.info(f"📋 Erster Datenpunkt: {data[0]}")
            else:
                st.error(f"❌ SPX/VIX API fehlgeschlagen! Status: {response.status_code}")
        
        # Test 2: Optionspreis API
        st.markdown("**2. Optionspreis API Test:**")
        option_url = "https://api.0dtespx.com/optionPrice?asset=SPX&date=2025-02-14&interval=1&symbol=-P6110"
        
        with st.spinner("🔄 Teste Optionspreis API..."):
            response = requests.get(option_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                st.success(f"✅ Optionspreis API erfolgreich! Status: {response.status_code}")
                st.info(f"📊 Datenstruktur: {type(data)}")
                if isinstance(data, dict):
                    st.info(f"📋 Verfügbare Keys: {list(data.keys())}")
                elif isinstance(data, list):
                    st.info(f"📋 Anzahl Datenpunkte: {len(data)}")
                    if len(data) > 0:
                        st.info(f"📋 Erster Datenpunkt: {data[0]}")
            else:
                st.error(f"❌ Optionspreis API fehlgeschlagen! Status: {response.status_code}")
                
    except Exception as e:
        st.error(f"❌ API-Test Fehler: {e}")
        st.info("💡 Mögliche Ursachen: Netzwerkprobleme, API nicht verfügbar, oder falsche URL")

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
