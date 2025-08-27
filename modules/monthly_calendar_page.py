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
        st.success(f"✅ Trade-Daten geladen: {len(trade_data)} Trades, {len(trade_data.columns)} Spalten")
        
        # Intelligente Spaltenerkennung
        profit_cols = [col for col in trade_data.columns if 'profit' in col.lower() or 'pnl' in col.lower() or 'gewinn' in col.lower()]
        type_cols = [col for col in trade_data.columns if 'type' in col.lower() or 'typ' in col.lower()]
        strategy_cols = [col for col in trade_data.columns if 'strategy' in col.lower() or 'strategie' in col.lower()]
        date_cols = [col for col in trade_data.columns if 'date' in col.lower() or 'datum' in col.lower() or 'time' in col.lower() or 'opened' in col.lower() or 'closed' in col.lower()]
        
        if not profit_cols or not date_cols:
            st.error("❌ Keine Profit- oder Datumsspalten gefunden")
            return
        
        profit_col = profit_cols[0]
        date_col = date_cols[0]
        
        # Strategy-Filter
        if strategy_cols:
            strategy_col = strategy_cols[0]
            # Verfügbare Strategien ermitteln
            available_strategies = trade_data[strategy_col].dropna().unique()
            available_strategies = sorted([str(s) for s in available_strategies if str(s) not in ['', 'None', 'nan', 'NaN']])
            
            if available_strategies:
                # "Alle Strategien" Option hinzufügen
                all_strategies = ["Alle Strategien"] + available_strategies
                selected_strategy = st.selectbox(
                    "🎯 Strategie auswählen:",
                    all_strategies,
                    key="monthly_strategy_filter"
                )
                
                # Daten nach Strategie filtern
                if selected_strategy != "Alle Strategien":
                    trade_data = trade_data[trade_data[strategy_col] == selected_strategy]
                    st.info(f"📊 Gefiltert nach Strategie: **{selected_strategy}** ({len(trade_data)} Trades)")
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
        
        # Nach Monat gruppieren und monatliche P&L berechnen
        # Zuerst Jahr und Monat als separate Spalten hinzufügen
        trade_data['year'] = trade_data[date_col].dt.year
        trade_data['month'] = trade_data[date_col].dt.month
        
        monthly_pnl = trade_data.groupby(['year', 'month']).agg({
            profit_col: ['sum', 'count']
        }).reset_index()
        
        # Spaltennamen vereinfachen
        monthly_pnl.columns = ['year', 'month', 'monthly_pnl', 'trade_count']
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
        
        year_total = year_data['monthly_pnl'].sum()
        year_trades = year_data['trade_count'].sum()
        
        # CSS für Monatskalender - Vereinfacht und größer
        st.markdown("""
        <style>
        .monthly-calendar-month {
            min-height: 150px;
            height: 150px;
            padding: 15px;
            border: 2px solid #dee2e6;
            border-radius: 10px;
            background-color: white;
            position: relative;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-sizing: border-box;
            margin: 5px;
        }
        .monthly-calendar-month.empty {
            background-color: #f8f9fa;
            min-height: 150px;
            height: 150px;
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
        .monthly-calendar-month.quarter {
            background-color: #e3f2fd !important;
            border-color: #2196f3 !important;
            border-width: 4px;
        }
        .month-name {
            font-weight: bold;
            font-size: 20px;
            margin-bottom: 10px;
            color: #495057;
        }
        .monthly-pnl {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #000;
        }
        .trade-count {
            font-size: 16px;
            color: #6c757d;
            font-weight: bold;
        }
        .quarter-summary {
            background-color: #fff3cd !important;
            border-color: #ffc107 !important;
            border-width: 4px;
        }
        .quarter-summary .month-name {
            font-size: 24px;
        }
        /* Prominenter Jahresheader */
        .year-header {
            font-size: 48px;
            font-weight: bold;
            color: #2c3e50;
            text-align: left;
            padding: 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
            text-shadow: 2px 2px 4px rgba(0,0,0,0.4);
            margin: 15px 0;
            letter-spacing: 3px;
            width: 100%;
            display: block;
        }
        /* Große Navigation-Buttons */
        .stButton > button {
            font-size: 28px !important;
            font-weight: 900 !important;
            padding: 25px 30px !important;
            height: 150px !important;
            min-height: 150px !important;
            border-radius: 20px !important;
            border: 5px solid #4a5568 !important;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%) !important;
            color: white !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4) !important;
            transition: all 0.3s ease !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            position: relative !important;
            overflow: hidden !important;
        }
        
        .stButton > button::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent) !important;
            transition: left 0.5s !important;
        }
        
        .stButton > button:hover::before {
            left: 100% !important;
        }
        .stButton > button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important;
            border-color: #ee5a24 !important;
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
                            
                            # CSS-Klasse basierend auf P&L
                            css_class = "positive" if monthly_pnl_value > 0 else "negative"
                            
                            # Monatsdetails
                            pnl_text = f"${monthly_pnl_value:,.2f}" if monthly_pnl_value != 0 else "$0"
                            trade_text = f"{trade_count} Trade{'s' if trade_count != 1 else ''}"
                            
                            # HTML für den Monat
                            month_html = f"""
                            <div class="monthly-calendar-month {css_class}">
                                <div class="month-name">{month_names[month_num - 1]}</div>
                                <div class="monthly-pnl">{pnl_text}</div>
                                <div class="trade-count">{trade_text}</div>
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
                    <div class="monthly-calendar-month {quarter_css_class} quarter-summary">
                        <div class="month-name">Q{row + 1}</div>
                        <div class="monthly-pnl">${quarter_pnl:,.2f}</div>
                        <div class="trade-count">{quarter_trades} Trade{'s' if quarter_trades != 1 else ''}</div>
                    </div>
                    """
                    st.markdown(quarter_html, unsafe_allow_html=True)
                else:
                    st.markdown("")
            
            # Abstand zwischen den Reihen
            st.markdown("---")
        
        # Zusätzliche Statistiken
        st.markdown("---")
        st.subheader("📊 Jahresstatistiken")
        
        # Jahressumme prominent anzeigen
        st.markdown(f"### 💰 Jahressumme: ${year_total:,.2f} ({year_trades} Trades)")
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            positive_months = year_data[year_data['monthly_pnl'] > 0]
            negative_months = year_data[year_data['monthly_pnl'] < 0]
            
            st.metric("Positive Monate", len(positive_months))
        
        with col2:
            st.metric("Negative Monate", len(negative_months))
        
        with col3:
            if len(positive_months) > 0:
                avg_positive = positive_months['monthly_pnl'].mean()
                st.metric("Ø Positiver Monat", f"${avg_positive:,.2f}")
            else:
                st.metric("Ø Positiver Monat", "$0.00")
        
        with col4:
            if len(negative_months) > 0:
                avg_negative = negative_months['monthly_pnl'].mean()
                st.metric("Ø Negativer Monat", f"${avg_negative:,.2f}")
            else:
                st.metric("Ø Negativer Monat", "$0.00")
        
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
