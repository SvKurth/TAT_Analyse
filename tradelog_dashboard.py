#!/usr/bin/env python3
"""
Tradelog Dashboard - Einfache Oberfläche für SQLite-Tradelogdateien
Zeigt nur die Trade-Tabelle an.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Projektverzeichnis zum Python-Pfad hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.data_loader import DataLoader
from src.utils import load_config

def is_sqlite_file(file_path: str) -> bool:
    """Prüft, ob eine Datei eine SQLite-Datenbank ist."""
    sqlite_extensions = ['.db', '.db3', '.sqlite', '.sqlite3']
    file_path = Path(file_path)
    
    # Prüfe Dateiendung
    if file_path.suffix.lower() in sqlite_extensions:
        return True
    
    # Prüfe Dateiinhalt (SQLite-Header)
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)
            return header.startswith(b'SQLite format 3')
    except:
        return False

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
            data_loader = DataLoader(config)
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

def show_overview_page(data_loader, db_path):
    """Zeigt die Übersichtsseite an."""
    st.header("📋 Übersicht")
    st.write("Willkommen beim Tradelog Dashboard!")
    
    try:
        # Datenbankinformationen anzeigen
        db_info = data_loader.get_sqlite_table_info(db_path)
        st.subheader("🗄️ Datenbankdetails")
        st.write(f"**Pfad:** {db_path}")
        st.write(f"**Größe:** {Path(db_path).stat().st_size / 1024 / 1024:.2f} MB")
        
        # Verfügbare Tabellen
        st.subheader("📋 Verfügbare Tabellen")
        for table_name, table_info in db_info['tables'].items():
            with st.expander(f"📊 {table_name} ({table_info['row_count']} Zeilen)"):
                st.write(f"**Spalten:** {len(table_info['columns'])}")
                
                # Spaltenliste
                st.write("**Spalten:**")
                for col in table_info['columns']:
                    pk_indicator = " 🔑" if col.get('pk', 0) > 0 else ""
                    st.write(f"- {col['name']} ({col['type']}){pk_indicator}")
                
                # Beispieldaten
                if table_info['sample_data']:
                    st.write("**Beispieldaten:**")
                    sample_df = pd.DataFrame(table_info['sample_data'], columns=table_info['column_names'])
                    st.dataframe(sample_df, use_container_width=True)
                    
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Datenbankinformationen: {e}")

def show_trade_table_page(data_loader, db_path):
    """Zeigt die Trade-Tabelle auf einer separaten Seite an."""
    st.header("📈 Trade-Tabelle")
    
    try:
        # Trade-Tabelle laden
        trade_data = data_loader.load_trade_table(db_path)
        st.success(f"✅ Trade-Tabelle geladen: {len(trade_data)} Zeilen, {len(trade_data.columns)} Spalten")
        

        
        # Metriken
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Gesamt Trades", len(trade_data))
        with col2:
            st.metric("Spalten", len(trade_data.columns))
        with col3:
            st.metric("Datenbank", Path(db_path).name)
        
        # Komplette Tabelle anzeigen
        st.subheader("📊 Komplette Trade-Tabelle")
        st.dataframe(trade_data, use_container_width=True)
        
        # CSV-Export
        csv = trade_data.to_csv(index=False)
        st.download_button(
            label="📥 CSV herunterladen",
            data=csv,
            file_name="trade_tabelle.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Trade-Tabelle: {e}")
        st.info("💡 Verfügbare Tabellen werden angezeigt...")
        
        # Fallback: Verfügbare Tabellen anzeigen
        try:
            db_info = data_loader.get_sqlite_table_info(db_path)
            st.subheader("📋 Verfügbare Tabellen in der Datenbank")
            
            for table_name, table_info in db_info['tables'].items():
                with st.expander(f"📊 {table_name} ({table_info['row_count']} Zeilen)"):
                    st.write(f"**Spalten:** {len(table_info['columns'])}")
                    
                    # Spaltenliste
                    st.write("**Spalten:**")
                    for col in table_info['columns']:
                        pk_indicator = " 🔑" if col.get('pk', 0) > 0 else ""
                        st.write(f"- {col['name']} ({col['type']}){pk_indicator}")
                    
                    # Beispieldaten
                    if table_info['sample_data']:
                        st.write("**Beispieldaten:**")
                        sample_df = pd.DataFrame(table_info['sample_data'], columns=table_info['column_names'])
                        st.dataframe(sample_df, use_container_width=True)
                        
        except Exception as e2:
            st.error(f"❌ Fehler beim Laden der Tabelleninformationen: {e2}")

def show_metrics_page(data_loader, db_path):
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
        col1, col2, col3, col4 = st.columns(4)
        
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
                <div class="metric-description">Peak: ${peak_value:,.2f}</div>
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
        
        # Erstelle zwei Spalten für die Hauptfunktionen
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Trading-Übersicht")
            
            # Trading-Performance-Metriken
            if profit_cols:
                profit_col = profit_cols[0]
            
            # Berechne Trading-Metriken
            total_trades = len(trade_data)
            total_profit = trade_data[profit_col].sum()
            avg_profit = trade_data[profit_col].mean()
            win_trades = len(trade_data[trade_data[profit_col] > 0])
            win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Metriken in Kacheln anzeigen
            metric_cols = st.columns(4)
            
            with metric_cols[0]:
                st.metric("Gesamt Trades", total_trades, delta=None)
            
            with metric_cols[1]:
                st.metric("Gewinnrate", f"{win_rate:.1f}%", delta=None)
            
            with metric_cols[2]:
                st.metric("Durchschnitt", f"${avg_profit:,.2f}", delta=None)
            
            with metric_cols[3]:
                st.metric("Gesamt P&L", f"${total_profit:,.2f}", 
                        delta=f"{'↗️' if total_profit >= 0 else '↘️'}")
        
        # Trading-Chart
        st.subheader("📈 Trading-Performance Chart")
        
        if profit_cols:
            # Erstelle kumulative P&L-Kurve
            cumulative_pnl = trade_data[profit_col].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(len(cumulative_pnl))),
                y=cumulative_pnl,
                mode='lines+markers',
                name='Kumulativer P&L',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=4)
            ))
            
            fig.update_layout(
                title="Trading-Performance Verlauf",
                xaxis_title="Trade Nummer",
                yaxis_title="Kumulativer P&L (€)",
                height=400,
                showlegend=True,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            fig.update_xaxes(gridcolor='lightgray', gridwidth=1)
            fig.update_yaxes(gridcolor='lightgray', gridwidth=1)
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Trading-Navigation")
            
            # Trading-Filter
            st.markdown("**🔍 Filter**")
            
            # Trade Type Filter
            type_cols = [col for col in trade_data.columns if 'type' in col.lower() or 'typ' in col.lower()]
            if type_cols:
                trade_types = trade_data[type_cols[0]].unique()
                selected_types = st.multiselect(
                    "Trade Type:",
                    options=trade_types,
                    default=trade_types[:3] if len(trade_types) <= 3 else trade_types[:5]
                )
            
            # Strategy Filter
            strategy_cols = [col for col in trade_data.columns if 'strategy' in col.lower() or 'strategie' in col.lower()]
            if strategy_cols:
                strategies = trade_data[strategy_cols[0]].unique()
                selected_strategies = st.multiselect(
                    "Strategie:",
                    options=strategies,
                    default=strategies[:3] if len(strategies) <= 3 else strategies[:5]
                )
            
            # Date Filter
            date_cols = [col for col in trade_data.columns if 'date' in col.lower() or 'opened' in col.lower()]
            if date_cols:
                st.markdown("**📅 Datumsbereich**")
                start_date = st.date_input("Von:", value=trade_data[date_cols[0]].min().date())
                end_date = st.date_input("Bis:", value=trade_data[date_cols[0]].max().date())
            
            # Filter anwenden Button
            if st.button("🔍 Filter anwenden", type="primary"):
                st.success("✅ Filter angewendet!")
                st.rerun()
        
        # Trading-Statistiken
        st.markdown("---")
        st.subheader("📊 Detaillierte Trading-Statistiken")
        
        # Erstelle drei Spalten für verschiedene Statistiken
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        
        with stat_col1:
            st.markdown("**📈 Gewinn/Verlust Verteilung**")
            if profit_cols:
                profit_col = profit_cols[0]
                profit_data = trade_data[profit_col]
                positive_trades = len(profit_data[profit_data > 0])
                negative_trades = len(profit_data[profit_data < 0])
                neutral_trades = len(profit_data[profit_data == 0])
                
                # Pie Chart für Gewinn/Verlust Verteilung
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Gewinne', 'Verluste', 'Neutral'],
                    values=[positive_trades, negative_trades, neutral_trades],
                    hole=0.3,
                    marker_colors=['#28a745', '#dc3545', '#6c757d']
                )])
                
                fig_pie.update_layout(
                    title="Trade-Verteilung",
                    height=300,
                    showlegend=True
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with stat_col2:
            st.markdown("**📊 Trade-Größen Verteilung**")
            if profit_cols:
                profit_col = profit_cols[0]
                profit_data = trade_data[profit_col]
                # Histogram der Trade-Größen
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Histogram(
                    x=profit_data,
                    nbinsx=20,
                    marker_color='#17a2b8',
                    opacity=0.7
                ))
                
                fig_hist.update_layout(
                    title="Trade-Größen Verteilung",
                    xaxis_title="P&L (€)",
                    yaxis_title="Anzahl Trades",
                    height=300,
                    showlegend=False
                )
                
                st.plotly_chart(fig_hist, use_container_width=True)
        
        with stat_col3:
            st.markdown("**🎯 Trading-Performance**")
            if profit_cols:
                profit_col = profit_cols[0]
                profit_data = trade_data[profit_col]
                # Performance-Metriken
                max_profit = profit_data.max()
                max_loss = profit_data.min()
                std_profit = profit_data.std()
                
                st.metric("Max. Gewinn", f"${max_profit:,.2f}")
                st.metric("Max. Verlust", f"${max_loss:,.2f}")
                st.metric("Standardabweichung", f"${std_profit:,.2f}")
                
                # Sharpe Ratio (vereinfacht)
                if std_profit > 0:
                    sharpe_ratio = avg_profit / std_profit
                    st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
        
        # Trading-Empfehlungen
        st.markdown("---")
        st.subheader("💡 Trading-Empfehlungen")
        
        if profit_cols:
            profit_col = profit_cols[0]
            profit_data = trade_data[profit_col]
            
            # Berechne zusätzliche Metriken für Empfehlungen
            avg_profit = profit_data.mean()
            
            col_rec1, col_rec2 = st.columns(2)
            
            with col_rec1:
                st.markdown("**📊 Performance-Analyse**")
                
                if win_rate > 60:
                    st.success("✅ Hohe Gewinnrate - Ihre Strategie funktioniert gut!")
                elif win_rate > 40:
                    st.warning("⚠️ Mittlere Gewinnrate - Überprüfen Sie Ihre Strategie")
                else:
                    st.error("❌ Niedrige Gewinnrate - Strategie überdenken erforderlich")
                
                if total_profit > 0:
                    st.success("✅ Positiver Gesamt-P&L - Sie sind profitabel!")
                else:
                    st.error("❌ Negativer Gesamt-P&L - Strategie überdenken erforderlich")
            
            with col_rec2:
                st.markdown("**🎯 Verbesserungsvorschläge**")
                
                if win_rate < 50:
                    st.info("💡 Erhöhen Sie Ihre Gewinnrate durch bessere Entry/Exit-Strategien")
                
                if abs(max_loss) > abs(max_profit):
                    st.info("💡 Reduzieren Sie Ihre Verlustgrößen durch besseres Risikomanagement")
                
                if std_profit > abs(avg_profit):
                    st.info("💡 Reduzieren Sie die Volatilität Ihrer Trades")
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der TAT Tradenavigator-Seite: {e}")
        st.info("💡 Bitte stellen Sie sicher, dass die Trade-Tabelle verfügbar ist.")

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
