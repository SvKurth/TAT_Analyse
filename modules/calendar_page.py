"""
Calendar Page Module für Tradelog Dashboard
Zeigt den Tagesgewinn pro Tag in einem Kalenderformat
"""

import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date, timedelta
from pathlib import Path

def show_calendar_page(data_loader, db_path):
    """Zeigt den Tagesgewinn pro Tag in einem Kalenderformat."""
    st.header("📅 Kalender - Tagesgewinn pro Tag")
    
    try:
        # Trade-Tabelle laden
        trade_data = data_loader.load_trade_table(db_path)
        
        # Intelligente Spaltenerkennung
        profit_cols = [col for col in trade_data.columns if 'profit' in col.lower() or 'pnl' in col.lower() or 'gewinn' in col.lower()]
        type_cols = [col for col in trade_data.columns if 'type' in col.lower() or 'typ' in col.lower()]
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
                if 'selected_strategies' not in st.session_state:
                    st.session_state.selected_strategies = available_strategies.copy()
                
                # Multi-Select für Strategien
                selected_strategies = st.multiselect(
                    "🎯 Strategien auswählen (alle ausgewählt = alle Trades):",
                    available_strategies,
                    default=st.session_state.selected_strategies,
                    key="strategy_multiselect"
                )
                
                # Session State aktualisieren
                st.session_state.selected_strategies = selected_strategies
                
                # Daten nach ausgewählten Strategien filtern
                if selected_strategies:
                    trade_data = trade_data[trade_data[strategy_col].isin(selected_strategies)]
                else:
                    st.warning("⚠️ Keine Strategien ausgewählt - alle Trades werden angezeigt")
            else:
                st.warning("⚠️ Keine Strategien in den Daten gefunden")
        else:
            st.info("ℹ️ Keine Strategie-Spalte gefunden - alle Trades werden angezeigt")
        
        # Monatsstatistiken über dem Kalender anzeigen
        if len(trade_data) > 0:
            st.markdown("---")
            st.subheader("📊 Monatsstatistiken")
            
            # Aktueller Monat und Jahr für Statistiken
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            # Monatsdaten filtern
            month_start = date(current_year, current_month, 1)
            if current_month == 12:
                month_end = date(current_year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(current_year, current_month + 1, 1) - timedelta(days=1)
            
            # Tagesstatistiken für den aktuellen Monat
            month_trades = trade_data[
                (trade_data[date_col].dt.date >= month_start) & 
                (trade_data[date_col].dt.date <= month_end)
            ]
            
            if len(month_trades) > 0:
                month_total = month_trades[profit_col].sum()
                month_trade_count = len(month_trades)
                
                # Monatssumme prominent anzeigen
                st.markdown(f"### 💰 Monatssumme: ${month_total:,.2f} ({month_trade_count} Trades)")
                st.markdown("---")
                
                # Tagesstatistiken für den aktuellen Monat berechnen
                month_daily_stats = month_trades.groupby(month_trades[date_col].dt.date).agg({
                    profit_col: 'sum'
                }).reset_index()
                month_daily_stats.columns = ['date', 'daily_pnl']
                
                # Positive und negative Tage
                positive_days = month_daily_stats[month_daily_stats['daily_pnl'] > 0]
                negative_days = month_daily_stats[month_daily_stats['daily_pnl'] < 0]
                
                # Erste Zeile: Positive und negative Tage
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Positive Tage", len(positive_days))
                
                with col2:
                    st.metric("Negative Tage", len(negative_days))
                
                with col3:
                    if len(positive_days) > 0:
                        avg_positive_day = positive_days['daily_pnl'].mean()
                        st.metric("Ø Positiver Tag", f"${avg_positive_day:,.2f}")
                    else:
                        st.metric("Ø Positiver Tag", "$0.00")
                
                with col4:
                    if len(negative_days) > 0:
                        avg_negative_day = negative_days['daily_pnl'].mean()
                        st.metric("Ø Negativer Tag", f"${avg_negative_day:,.2f}")
                    else:
                        st.metric("Ø Negativer Tag", "$0.00")
                
                with col5:
                    # Durchschnittliche Premium Capture Rate für den Monat
                    if len(premium_cols) > 0:
                        premium_col = premium_cols[0]
                        # Prämien-Spalte bereinigen
                        month_trades[premium_col] = month_trades[premium_col].replace(['', 'None', 'nan', 'NaN'], pd.NA)
                        month_trades[premium_col] = pd.to_numeric(month_trades[premium_col], errors='coerce')
                        
                        valid_premium_trades = month_trades.dropna(subset=[premium_col])
                        if len(valid_premium_trades) > 0:
                            # Premium Capture Rate für den Monat berechnen
                            sold_premiums = valid_premium_trades[valid_premium_trades[premium_col] > 0][premium_col].sum()
                            bought_premiums = abs(valid_premium_trades[valid_premium_trades[premium_col] < 0][premium_col].sum())
                            net_premiums = sold_premiums - bought_premiums
                            
                            if net_premiums != 0:
                                avg_premium_capture = (month_total / net_premiums) * 100
                                st.metric("Ø Premium Capture", f"{avg_premium_capture:.1f}%")
                            else:
                                st.metric("Ø Premium Capture", "N/A")
                        else:
                            st.metric("Ø Premium Capture", "N/A")
                    else:
                        st.metric("Ø Premium Capture", "N/A")
                
                # Zweite Zeile: Min/Max für positive und negative Tage
                st.markdown("---")
                col6, col7, col8, col9, col10 = st.columns(5)
                
                with col6:
                    if len(positive_days) > 0:
                        min_positive_day = positive_days['daily_pnl'].min()
                        st.metric("Min Positiver Tag", f"${min_positive_day:,.2f}")
                    else:
                        st.metric("Min Positiver Tag", "$0.00")
                
                with col7:
                    if len(positive_days) > 0:
                        max_positive_day = positive_days['daily_pnl'].max()
                        st.metric("Max Positiver Tag", f"${max_positive_day:,.2f}")
                    else:
                        st.metric("Max Positiver Tag", "$0.00")
                
                with col8:
                    if len(negative_days) > 0:
                        min_negative_day = negative_days['daily_pnl'].min()
                        st.metric("Min Negativer Tag", f"${min_negative_day:,.2f}")
                    else:
                        st.metric("Min Negativer Tag", "$0.00")
                
                with col9:
                    if len(negative_days) > 0:
                        max_negative_day = negative_days['daily_pnl'].max()
                        st.metric("Max Negativer Tag", f"${max_negative_day:,.2f}")
                    else:
                        st.metric("Max Negativer Tag", "$0.00")
                
                with col10:
                    # Leere Spalte für bessere Ausrichtung
                    st.markdown("")
            
            st.markdown("---")
        
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
            st.error("❌ Keine gültigen Daten für die Kalenderansicht verfügbar")
            return
        
        # Nach Datum gruppieren und tägliche P&L sowie Premium Capture Rate berechnen
        daily_stats = trade_data.groupby(trade_data[date_col].dt.date).agg({
            profit_col: ['sum', 'count'],
            date_col: 'first'
        }).reset_index()
        
        # Spaltennamen vereinfachen
        daily_stats.columns = ['date', 'daily_pnl', 'trade_count', 'datetime']
        
        # Premium Capture Rate pro Tag berechnen
        daily_stats['premium_capture_rate'] = 0.0
        
        for idx, row in daily_stats.iterrows():
            current_date = row['date']
            day_trades = trade_data[trade_data[date_col].dt.date == current_date]
            
            if len(day_trades) > 0 and len(premium_cols) > 0:
                premium_col = premium_cols[0]
                
                # Prämien-Spalte bereinigen und als numerisch konvertieren
                day_trades[premium_col] = day_trades[premium_col].replace(['', 'None', 'nan', 'NaN'], pd.NA)
                day_trades[premium_col] = pd.to_numeric(day_trades[premium_col], errors='coerce')
                
                # Nur Trades mit gültigen Prämien-Werten
                valid_premium_trades = day_trades.dropna(subset=[premium_col])
                
                if len(valid_premium_trades) > 0:
                    # Total verkaufte Prämie (positive Prämien)
                    sold_premiums = valid_premium_trades[valid_premium_trades[premium_col] > 0][premium_col].sum()
                    
                    # Total gekaufte Prämie (negative Prämien)
                    bought_premiums = abs(valid_premium_trades[valid_premium_trades[premium_col] < 0][premium_col].sum())
                    
                    # Tages-P&L
                    daily_pnl_value = row['daily_pnl']
                    
                    # Neue Premium Capture Rate Formel: (P&L / (verkaufte - gekaufte Prämie)) * 100%
                    net_premiums = sold_premiums - bought_premiums
                    if net_premiums != 0:
                        premium_capture = (daily_pnl_value / net_premiums) * 100
                        daily_stats.loc[idx, 'premium_capture_rate'] = premium_capture
                    else:
                        daily_stats.loc[idx, 'premium_capture_rate'] = 0.0
        
        daily_pnl = daily_stats.sort_values('date')
        
        # Monats-Navigation
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            # Aktueller Monat und Jahr
            if 'current_month' not in st.session_state:
                st.session_state.current_month = datetime.now().month
                st.session_state.current_year = datetime.now().year
            
            month_names = ["Januar", "Februar", "März", "April", "Mai", "Juni", 
                          "Juli", "August", "September", "Oktober", "November", "Dezember"]
            month_name = month_names[st.session_state.current_month - 1]
            st.markdown(f'<div class="month-header">{month_name} {st.session_state.current_year}</div>', unsafe_allow_html=True)
        
        with col2:
            if st.button("**TODAY**", key="today_btn", use_container_width=True):
                st.session_state.current_month = datetime.now().month
                st.session_state.current_year = datetime.now().year
                st.rerun()
        
        with col3:
            if st.button("**←**", key="prev_month", use_container_width=True):
                if 'current_month' not in st.session_state:
                    st.session_state.current_month = datetime.now().month
                    st.session_state.current_year = datetime.now().year
                
                st.session_state.current_month -= 1
                if st.session_state.current_month < 1:
                    st.session_state.current_month = 12
                    st.session_state.current_year -= 1
                st.rerun()
        
        with col4:
            if st.button("**→**", key="next_month", use_container_width=True):
                if 'current_month' not in st.session_state:
                    st.session_state.current_month = datetime.now().month
                    st.session_state.current_year = datetime.now().year
                
                st.session_state.current_month += 1
                if st.session_state.current_month > 12:
                    st.session_state.current_month = 1
                    st.session_state.current_year += 1
                st.rerun()
        
        # Monatssumme berechnen
        month_start = date(st.session_state.current_year, st.session_state.current_month, 1)
        if st.session_state.current_month == 12:
            month_end = date(st.session_state.current_year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(st.session_state.current_year, st.session_state.current_month + 1, 1) - timedelta(days=1)
        
        month_data = daily_pnl[
            (daily_pnl['date'] >= month_start) & 
            (daily_pnl['date'] <= month_end)
        ]
        
        month_total = month_data['daily_pnl'].sum()
        month_trades = month_data['trade_count'].sum()
        
        # CSS für Kalender - Vereinfacht und größer
        st.markdown("""
        <style>
        .calendar-day {
            min-height: 140px;
            height: 140px;
            padding: 8px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            background-color: white;
            position: relative;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-sizing: border-box;
        }
        .calendar-day.empty {
            background-color: #f8f9fa;
            min-height: 140px;
            height: 140px;
        }
        .calendar-day.positive {
            background-color: #d4edda;
            border-color: #c3e6cb;
        }
        .calendar-day.negative {
            background-color: #f8d7da;
            border-color: #f5c6cb;
        }
        .calendar-day.saturday {
            background-color: #e2e3e5;
            border-color: #d6d8db;
        }
        .day-number {
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 6px;
            color: #495057;
        }
        .daily-pnl {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 6px;
            color: #000;
        }
        .trade-count {
            font-size: 13px;
            color: #6c757d;
            font-weight: bold;
            margin-bottom: 4px;
        }
        .premium-capture {
            font-size: 13px;
            color: #495057;
            font-weight: bold;
            margin-top: 2px;
        }
        .week-summary {
            border-width: 3px;
            font-weight: bold;
        }
        .week-summary.positive {
            background-color: #d4edda !important;
            border-color: #28a745 !important;
            color: #155724 !important;
        }
        .week-summary.negative {
            background-color: #f8d7da !important;
            border-color: #dc3545 !important;
            color: #721c24 !important;
        }
        .week-summary .day-number {
            font-size: 22px;
        }
        /* Wochentags-Header zentrieren */
        .stMarkdown {
            text-align: center !important;
        }
        /* Spezifisch für Header-Spalten */
        .stMarkdown p {
            text-align: center !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        /* Prominenter Monatsheader */
        .month-header {
            font-size: 36px;
            font-weight: bold;
            color: #2c3e50;
            text-align: left;
            padding: 20px;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            margin: 10px 0;
            letter-spacing: 2px;
            width: 100%;
            display: block;
        }
        /* Große Navigation-Buttons */
        .stButton > button {
            font-size: 24px !important;
            font-weight: 900 !important;
            padding: 20px 25px !important;
            height: 140px !important;
            min-height: 140px !important;
            border-radius: 15px !important;
            border: 4px solid #4a5568 !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3) !important;
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
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent) !important;
            transition: left 0.5s !important;
        }
        
        .stButton > button:hover::before {
            left: 100% !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
            border-color: #764ba2 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Kalender erstellen - Immer 5 Wochen (35 Tage) für konsistente Darstellung
        cal = calendar.monthcalendar(st.session_state.current_year, st.session_state.current_month)
        
        # Wochentage-Header
        weekday_names = ['SUN', 'MON', 'TUE', 'WED', 'THR', 'FRI', 'SAT']
        
        st.markdown('<div class="calendar-container">', unsafe_allow_html=True)
        
        # Wochentags-Header mit Streamlit Columns (garantiert funktioniert)
        header_cols = st.columns(8)  # 7 Wochentage + 1 Wochensumme
        for i, day_name in enumerate(weekday_names):
            with header_cols[i]:
                st.markdown(f"**{day_name}**", help="")
        
        # Wochensumme-Header
        with header_cols[7]:
            st.markdown("**📊**", help="")
        
        st.markdown("---")
        
        # Erste Woche des Monats finden
        first_weekday = date(st.session_state.current_year, st.session_state.current_month, 1).weekday()
        # In Python ist Montag=0, Sonntag=6, aber wir wollen Sonntag=0
        first_weekday = (first_weekday + 1) % 7
        
        # Monatslänge
        if st.session_state.current_month == 12:
            next_month = date(st.session_state.current_year + 1, 1, 1)
        else:
            next_month = date(st.session_state.current_year, st.session_state.current_month + 1, 1)
        month_length = (next_month - date(st.session_state.current_year, st.session_state.current_month, 1)).days
        
        # 5 Wochen durchgehen - jede Woche in einer eigenen Zeile
        for week in range(5):
            # Für jede Woche 8 Spalten erstellen (7 Tage + 1 Wochensumme)
            week_cols = st.columns(8)
            
            # Variablen für Wochenberechnung
            week_pnl = 0
            week_trades = 0
            
            for day_of_week in range(7):  # 7 Tage pro Woche
                # Tag-Nummer berechnen
                day_number = week * 7 + day_of_week - first_weekday + 1
                
                with week_cols[day_of_week]:
                    if day_number < 1 or day_number > month_length:
                        # Tag außerhalb des Monats - leerer Tag
                        st.markdown("")
                    else:
                        current_date = date(st.session_state.current_year, st.session_state.current_month, day_number)
                        
                        # Tagesdaten finden - Konvertierung zu date für Vergleich
                        day_data = daily_pnl[daily_pnl['date'] == current_date]
                        
                        if len(day_data) > 0:
                            daily_pnl_value = day_data.iloc[0]['daily_pnl']
                            trade_count = day_data.iloc[0]['trade_count']
                            premium_capture = day_data.iloc[0]['premium_capture_rate']
                            
                            # Wochenwerte akkumulieren
                            week_pnl += daily_pnl_value
                            week_trades += trade_count
                            
                            # CSS-Klasse basierend auf P&L
                            css_class = "positive" if daily_pnl_value > 0 else "negative"
                            if current_date.weekday() == 5:  # Samstag
                                css_class += " saturday"
                            
                            # Tagesdetails - P&L, Anzahl Trades und Premium Capture Rate
                            pnl_text = f"${daily_pnl_value:,.2f}" if daily_pnl_value != 0 else "$0"
                            trade_text = f"{trade_count} Trade{'s' if trade_count != 1 else ''}"
                            premium_text = f"PCR: {premium_capture:.1f}%" if premium_capture != 0 else "PCR: N/A"
                            
                            # HTML für den Tag mit Premium Capture Rate
                            day_html = f"""
                            <div class="calendar-day {css_class}">
                                <div class="day-number">{day_number}</div>
                                <div class="daily-pnl">{pnl_text}</div>
                                <div class="trade-count">{trade_text}</div>
                                <div class="premium-capture">{premium_text}</div>
                            </div>
                            """
                            st.markdown(day_html, unsafe_allow_html=True)
                        else:
                            # Tag ohne Trades
                            css_class = "saturday" if current_date.weekday() == 5 else ""
                            day_html = f"""
                            <div class="calendar-day {css_class}">
                                <div class="day-number">{day_number}</div>
                            </div>
                            """
                            st.markdown(day_html, unsafe_allow_html=True)
            
            # Wochensumme in der 8. Spalte anzeigen
            with week_cols[7]:
                if week_trades > 0:
                    # CSS-Klasse für positive/negative Wochen
                    week_css_class = "positive" if week_pnl > 0 else "negative"
                    week_html = f"""
                    <div class="calendar-day week-summary {week_css_class}">
                        <div class="day-number">📊</div>
                        <div class="daily-pnl">${week_pnl:,.2f}</div>
                        <div class="trade-count">{week_trades} Trade{'s' if week_trades != 1 else ''}</div>
                    </div>
                    """
                    st.markdown(week_html, unsafe_allow_html=True)
                else:
                    st.markdown("")
            
            # Abstand zwischen den Wochen
            st.markdown("---")
        
        # Monatsstatistiken werden jetzt über dem Kalender angezeigt
        
        # Wöchentliche Zusammenfassung (Samstags)
        st.markdown("---")
        st.subheader("📅 Wöchentliche Zusammenfassung")
        
        saturdays_data = month_data[month_data['date'].apply(lambda x: x.weekday() == 5)]
        
        if len(saturdays_data) > 0:
            for _, saturday in saturdays_data.iterrows():
                week_start = saturday['date'] - timedelta(days=saturday['date'].weekday())
                week_end = saturday['date']
                
                week_data = month_data[
                    (month_data['date'] >= week_start) & 
                    (month_data['date'] <= week_end)
                ]
                
                week_total = week_data['daily_pnl'].sum()
                week_trades = week_data['trade_count'].sum()
                
                st.markdown(f"**{week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m')}: ${week_total:,.2f} ({week_trades} Trades)**")
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Kalenderansicht: {e}")
        st.info("💡 Bitte stellen Sie sicher, dass die Trade-Tabelle verfügbar ist.")
