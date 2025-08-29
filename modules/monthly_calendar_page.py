"""
Monthly Calendar Page Module für Tradelog Dashboard
Zeigt den Monatsgewinn pro Monat in einem Kalenderformat
"""

import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date, timedelta
from pathlib import Path

def show_monthly_calendar_page(data_loader, db_path):
    """Zeigt den Monatsgewinn pro Monat in einem Kalenderformat."""
    st.header("📅 Monatskalender - Monatsgewinn pro Monat")
    
    try:
        # Trade-Tabelle laden
        trade_data = data_loader.load_trade_table(db_path)
        
        # Intelligente Spaltenerkennung
        profit_cols = [col for col in trade_data.columns if 'profit' in col.lower() or 'pnl' in col.lower() or 'gewinn' in col.lower()]
        strategy_cols = [col for col in trade_data.columns if 'strategy' in col.lower() or 'strategie' in col.lower()]
        date_cols = [col for col in trade_data.columns if 'date' in col.lower() or 'datum' in col.lower() or 'time' in col.lower() or 'opened' in col.lower() or 'closed' in col.lower()]
        premium_cols = [col for col in trade_data.columns if 'premium' in col.lower() or 'prämie' in col.lower() or 'credit' in col.lower() or 'debit' in col.lower()]
        
        if not profit_cols or not date_cols:
            st.error("❌ Keine Profit- oder Datumsspalten gefunden")
            return
        
        profit_col = profit_cols[0]
        date_col = date_cols[0]
        
        # Strategy-Filter mit Multi-Select
        if strategy_cols:
            strategy_col = strategy_cols[0]
            # Verfügbare Strategien ermitteln
            available_strategies = trade_data[strategy_col].dropna().unique()
            available_strategies = sorted([str(s) for s in available_strategies if str(s) not in ['', 'None', 'nan', 'NaN']])
            
            if available_strategies:
                # Session State für ausgewählte Strategien initialisieren
                if 'selected_strategies_monthly' not in st.session_state:
                    st.session_state.selected_strategies_monthly = available_strategies.copy()
                
                # Multi-Select für Strategien
                selected_strategies = st.multiselect(
                    "🎯 Strategien auswählen (alle ausgewählt = alle Trades):",
                    available_strategies,
                    default=st.session_state.selected_strategies_monthly,
                    key="strategy_multiselect_monthly"
                )
                
                # Session State aktualisieren
                st.session_state.selected_strategies_monthly = selected_strategies
                
                # Daten nach ausgewählten Strategien filtern
                if selected_strategies:
                    trade_data = trade_data[trade_data[strategy_col].isin(selected_strategies)]
                else:
                    st.warning("⚠️ Keine Strategien ausgewählt - alle Trades werden angezeigt")
            else:
                st.warning("⚠️ Keine Strategien in den Daten gefunden")
        else:
            st.info("ℹ️ Keine Strategie-Spalte gefunden - alle Trades werden angezeigt")
        
        # Datumsspalte als datetime konvertieren
        if trade_data[date_col].dtype == 'object':
            trade_data[date_col] = pd.to_datetime(trade_data[date_col], errors='coerce')
        
        if not pd.api.types.is_datetime64_any_dtype(trade_data[date_col]):
            st.error("❌ Datumsspalte konnte nicht als Datum interpretiert werden")
            return
        
        # Profit-Spalte bereinigen und als numerisch konvertieren
        trade_data[profit_col] = trade_data[profit_col].replace(['', 'None', 'nan', 'NaN'], pd.NA)
        trade_data[profit_col] = pd.to_numeric(trade_data[profit_col], errors='coerce')
        trade_data = trade_data.dropna(subset=[profit_col, date_col])
        
        if len(trade_data) == 0:
            st.error("❌ Keine gültigen Daten für die Monatskalenderansicht verfügbar")
            return
        
        # Verwende die bereits vorhandenen Year/Month-Spalten
        if 'Year' in trade_data.columns and 'Month' in trade_data.columns:
            year_col_name = 'Year'
            month_col_name = 'Month'
            st.info("ℹ️ Verwende bestehende Year/Month-Spalten aus den Daten")
        else:
            st.error("❌ Keine Year/Month-Spalten in den Daten gefunden")
            st.info("💡 Erwartete Spalten: 'Year' und 'Month'")
            return
        
        # Prüfe ob die Spalten gültige Werte enthalten
        if trade_data[year_col_name].isna().all() or trade_data[month_col_name].isna().all():
            st.error("❌ Year/Month-Spalten enthalten keine gültigen Werte")
            return
        
        st.info(f"✅ Jahr-Spalte: {year_col_name}, Monat-Spalte: {month_col_name}")
        st.info(f"✅ Verfügbare Jahre: {sorted(trade_data[year_col_name].unique())}")
        st.info(f"✅ Verfügbare Monate: {sorted(trade_data[month_col_name].unique())}")
        
        # Monatliche P&L berechnen
        monthly_pnl = trade_data.groupby([year_col_name, month_col_name]).agg({
            profit_col: ['sum', 'count']
        }).reset_index()
        
        # Spaltennamen vereinfachen
        monthly_pnl.columns = ['year', 'month', 'monthly_pnl', 'trade_count']
        
        # Premium Capture Rate pro Monat berechnen
        monthly_pnl['premium_capture_rate'] = 0.0
        
        if len(premium_cols) > 0:
            premium_col = premium_cols[0]
            try:
                for idx, row in monthly_pnl.iterrows():
                    current_year = row['year']
                    current_month = row['month']
                    
                    month_trades = trade_data[
                        (trade_data[year_col_name] == current_year) & 
                        (trade_data[month_col_name] == current_month)
                    ]
                    
                    if len(month_trades) > 0:
                        # Prämien-Spalte bereinigen und als numerisch konvertieren
                        month_trades_copy = month_trades.copy()
                        month_trades_copy[premium_col] = month_trades_copy[premium_col].replace(['', 'None', 'nan', 'NaN'], pd.NA)
                        month_trades_copy[premium_col] = pd.to_numeric(month_trades_copy[premium_col], errors='coerce')
                        
                        # Nur Trades mit gültigen Prämien-Werten
                        valid_premium_trades = month_trades_copy.dropna(subset=[premium_col])
                        
                        if len(valid_premium_trades) > 0:
                            # Total verkaufte Prämie (positive Prämien)
                            sold_premiums = valid_premium_trades[valid_premium_trades[premium_col] > 0][premium_col].sum()
                            
                            # Total gekaufte Prämie (negative Prämien)
                            bought_premiums = abs(valid_premium_trades[valid_premium_trades[premium_col] < 0][premium_col].sum())
                            
                            # Monats-P&L
                            monthly_pnl_value = row['monthly_pnl']
                            
                            # Premium Capture Rate Formel: (P&L / (verkaufte - gekaufte Prämie)) * 100%
                            net_premiums = sold_premiums - bought_premiums
                            if net_premiums != 0:
                                premium_capture = (monthly_pnl_value / net_premiums) * 100
                                monthly_pnl.loc[idx, 'premium_capture_rate'] = premium_capture
                            else:
                                monthly_pnl.loc[idx, 'premium_capture_rate'] = 0.0
            except Exception as e:
                st.warning(f"⚠️ Warnung bei Premium Capture Rate Berechnung: {e}")
                # Bei Fehlern alle PCR auf 0 setzen
                monthly_pnl['premium_capture_rate'] = 0.0
        
        monthly_pnl = monthly_pnl.sort_values(['year', 'month'])
        
        # Jahr-Navigation
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            # Aktuelles Jahr
            if 'current_year_monthly' not in st.session_state:
                st.session_state.current_year_monthly = datetime.now().year
            
            st.markdown(f'<div class="year-header">{st.session_state.current_year_monthly}</div>', unsafe_allow_html=True)
        
        with col2:
            if st.button("**TODAY**", key="today_monthly_btn", use_container_width=True):
                st.session_state.current_year_monthly = datetime.now().year
                st.rerun()
        
        with col3:
            if st.button("**←**", key="prev_year_monthly", use_container_width=True):
                if 'current_year_monthly' not in st.session_state:
                    st.session_state.current_year_monthly = datetime.now().year
                
                st.session_state.current_year_monthly -= 1
                st.rerun()
        
        with col4:
            if st.button("**→**", key="next_year_monthly", use_container_width=True):
                if 'current_year_monthly' not in st.session_state:
                    st.session_state.current_year_monthly = datetime.now().year
                
                st.session_state.current_year_monthly += 1
                st.rerun()
        
        # Jahressumme berechnen
        year_data = monthly_pnl[monthly_pnl['year'] == st.session_state.current_year_monthly]
        
        if len(year_data) == 0:
            st.warning(f"⚠️ Keine Daten für das Jahr {st.session_state.current_year_monthly} gefunden")
            year_data = pd.DataFrame(columns=['year', 'month', 'monthly_pnl', 'trade_count', 'premium_capture_rate'])
        
        year_total = year_data['monthly_pnl'].sum() if len(year_data) > 0 else 0
        year_trades = year_data['trade_count'].sum() if len(year_data) > 0 else 0
        
        # Jahressumme anzeigen
        st.markdown("---")
        st.subheader("📊 Jahresstatistiken")
        st.markdown(f"### 💰 Jahressumme: ${year_total:,.2f} ({year_trades} Trades)")
        
        # CSS für Monatskalender
        st.markdown("""
        <style>
        .monthly-calendar-month {
            min-height: 120px;
            height: 120px;
            padding: 10px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            background-color: white;
            position: relative;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-sizing: border-box;
            margin: 3px;
        }
        .monthly-calendar-month.empty {
            background-color: #f8f9fa;
        }
        .monthly-calendar-month.positive {
            background-color: #d4edda;
            border-color: #28a745;
            border-width: 3px;
        }
        .monthly-calendar-month.negative {
            background-color: #f8d7da;
            border-color: #dc3545;
            border-width: 3px;
        }
        .month-name {
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 5px;
            color: #495057;
        }
        .monthly-pnl {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
            color: #000;
        }
        .trade-count {
            font-size: 12px;
            color: #6c757d;
            font-weight: bold;
            margin-bottom: 2px;
        }
        .premium-capture {
            font-size: 11px;
            color: #495057;
            font-weight: bold;
        }
        .year-header {
            font-size: 36px;
            font-weight: bold;
            color: #2c3e50;
            text-align: left;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            margin: 10px 0;
            letter-spacing: 2px;
            width: 100%;
            display: block;
        }
        .stButton > button {
            font-size: 18px !important;
            font-weight: bold !important;
            padding: 15px 20px !important;
            height: 80px !important;
            border-radius: 10px !important;
            border: 3px solid #4a5568 !important;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%) !important;
            color: white !important;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Monatskalender erstellen - 4 Reihen mit je 3 Monaten
        month_names = ["Januar", "Februar", "März", "April", "Mai", "Juni", 
                      "Juli", "August", "September", "Oktober", "November", "Dezember"]
        
        st.markdown('<div class="monthly-calendar-container">', unsafe_allow_html=True)
        
        # Monate in 4 Reihen mit je 3 Monaten anzeigen
        for row in range(4):
            month_cols = st.columns(4)  # 3 Monate + 1 Quartalssumme
            
            for col in range(3):
                month_num = row * 3 + col + 1
                
                with month_cols[col]:
                    if month_num <= 12:
                        # Monatsdaten finden
                        month_data = year_data[year_data['month'] == month_num]
                        
                        if len(month_data) > 0:
                            monthly_pnl_value = month_data.iloc[0]['monthly_pnl']
                            trade_count = month_data.iloc[0]['trade_count']
                            premium_capture = month_data.iloc[0]['premium_capture_rate']
                            
                            # CSS-Klasse basierend auf P&L
                            css_class = "positive" if monthly_pnl_value > 0 else "negative"
                            
                            # Monatsdetails - P&L, Anzahl Trades und Premium Capture Rate
                            pnl_text = f"${monthly_pnl_value:,.0f}" if monthly_pnl_value != 0 else "$0"
                            trade_text = f"{trade_count} Trade{'s' if trade_count != 1 else ''}"
                            premium_text = f"PCR: {premium_capture:.1f}%" if premium_capture != 0 else "PCR: N/A"
                            
                            # HTML für den Monat
                            month_html = f"""
                            <div class="monthly-calendar-month {css_class}">
                                <div class="month-name">{month_names[month_num - 1]}</div>
                                <div class="monthly-pnl">{pnl_text}</div>
                                <div class="trade-count">{trade_text}</div>
                                <div class="premium-capture">{premium_text}</div>
                            </div>
                            """
                            st.markdown(month_html, unsafe_allow_html=True)
                        else:
                            # Monat ohne Trades
                            month_html = f"""
                            <div class="monthly-calendar-month empty">
                                <div class="month-name">{month_names[month_num - 1]}</div>
                            </div>
                            """
                            st.markdown(month_html, unsafe_allow_html=True)
                    else:
                        st.markdown("")
            
            # Quartalssumme in der 4. Spalte anzeigen
            with month_cols[3]:
                quarter_start = row * 3 + 1
                quarter_end = min(row * 3 + 3, 12)
                
                quarter_data = year_data[
                    (year_data['month'] >= quarter_start) & 
                    (year_data['month'] <= quarter_end)
                ]
                
                if len(quarter_data) > 0:
                    quarter_pnl = quarter_data['monthly_pnl'].sum()
                    quarter_trades = quarter_data['trade_count'].sum()
                    
                    quarter_css_class = "positive" if quarter_pnl > 0 else "negative"
                    quarter_html = f"""
                    <div class="monthly-calendar-month {quarter_css_class}">
                        <div class="month-name">Q{row + 1}</div>
                        <div class="monthly-pnl">${quarter_pnl:,.0f}</div>
                        <div class="trade-count">{quarter_trades} Trade{'s' if quarter_trades != 1 else ''}</div>
                    </div>
                    """
                    st.markdown(quarter_html, unsafe_allow_html=True)
                else:
                    st.markdown("")
            
            # Abstand zwischen den Reihen
            st.markdown("---")
        
        # Quartalszusammenfassung
        st.markdown("---")
        st.subheader("📅 Quartalszusammenfassung")
        
        for quarter in range(4):
            quarter_start = quarter * 3 + 1
            quarter_end = min(quarter * 3 + 3, 12)
            
            quarter_data = year_data[
                (year_data['month'] >= quarter_start) & 
                (year_data['month'] <= quarter_end)
            ]
            
            if len(quarter_data) > 0:
                quarter_total = quarter_data['monthly_pnl'].sum()
                quarter_trades = quarter_data['trade_count'].sum()
                
                quarter_months = [month_names[m-1] for m in range(quarter_start, quarter_end + 1)]
                quarter_name = " - ".join(quarter_months)
                
                st.markdown(f"**Q{quarter + 1} ({quarter_name}): ${quarter_total:,.2f} ({quarter_trades} Trades)**")
        
        # Monatsvergleich mit Vorjahr
        st.markdown("---")
        st.subheader("📈 Monatsvergleich mit Vorjahr")
        
        prev_year_data = monthly_pnl[monthly_pnl['year'] == st.session_state.current_year_monthly - 1]
        
        if len(prev_year_data) > 0:
            comparison_cols = st.columns(12)
            
            for i, month_num in enumerate(range(1, 13)):
                with comparison_cols[i]:
                    current_month = year_data[year_data['month'] == month_num]
                    prev_month = prev_year_data[prev_year_data['month'] == month_num]
                    
                    if len(current_month) > 0 and len(prev_month) > 0:
                        current_pnl = current_month.iloc[0]['monthly_pnl']
                        prev_pnl = prev_month.iloc[0]['monthly_pnl']
                        
                        change = current_pnl - prev_pnl
                        change_percent = (change / prev_pnl * 100) if prev_pnl != 0 else 0
                        
                        st.metric(
                            month_names[month_num - 1][:3],
                            f"${current_pnl:,.0f}",
                            f"{change:+,.0f} ({change_percent:+.1f}%)"
                        )
                    else:
                        st.metric(month_names[month_num - 1][:3], "N/A")
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Monatskalenderansicht: {e}")
        st.info("💡 Bitte stellen Sie sicher, dass die Trade-Tabelle verfügbar ist.")
        
        # Debug-Informationen
        st.info("🔍 Debug-Informationen:")
        st.info(f"Fehlertyp: {type(e).__name__}")
        st.info(f"Fehlermeldung: {str(e)}")
        
        try:
            if 'data_loader' in locals() and 'db_path' in locals():
                st.info("Versuche Daten zu laden...")
                trade_data = data_loader.load_trade_table(db_path)
                st.info(f"Geladene Daten: {len(trade_data)} Zeilen, {len(trade_data.columns)} Spalten")
                st.info(f"Spaltennamen: {list(trade_data.columns)}")
                
                if 'Year' in trade_data.columns and 'Month' in trade_data.columns:
                    st.info("✅ Year/Month-Spalten gefunden")
                    st.info(f"Year-Datentyp: {trade_data['Year'].dtype}")
                    st.info(f"Month-Datentyp: {trade_data['Month'].dtype}")
                    st.info(f"Verfügbare Jahre: {sorted(trade_data['Year'].unique())}")
                    st.info(f"Verfügbare Monate: {sorted(trade_data['Month'].unique())}")
                
        except Exception as debug_e:
            st.error(f"Debug-Fehler: {debug_e}")
