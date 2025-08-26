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
                    key="strategy_filter"
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
            st.error("❌ Keine gültigen Daten für die Kalenderansicht verfügbar")
            return
        
        # Nach Datum gruppieren und tägliche P&L berechnen
        daily_pnl = trade_data.groupby(trade_data[date_col].dt.date).agg({
            profit_col: ['sum', 'count'],
            date_col: 'first'
        }).reset_index()
        
        # Spaltennamen vereinfachen
        daily_pnl.columns = ['date', 'daily_pnl', 'trade_count', 'datetime']
        daily_pnl = daily_pnl.sort_values('date')
        
        # Monats-Navigation
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
        
        with col1:
            if st.button("Today", key="today_btn"):
                st.session_state.current_month = datetime.now().month
                st.session_state.current_year = datetime.now().year
                st.rerun()
        
        with col2:
            if st.button("←", key="prev_month"):
                if 'current_month' not in st.session_state:
                    st.session_state.current_month = datetime.now().month
                    st.session_state.current_year = datetime.now().year
                
                st.session_state.current_month -= 1
                if st.session_state.current_month < 1:
                    st.session_state.current_month = 12
                    st.session_state.current_year -= 1
                st.rerun()
        
        with col3:
            if st.button("→", key="next_month"):
                if 'current_month' not in st.session_state:
                    st.session_state.current_month = datetime.now().month
                    st.session_state.current_year = datetime.now().year
                
                st.session_state.current_month += 1
                if st.session_state.current_month > 12:
                    st.session_state.current_month = 1
                    st.session_state.current_year += 1
                st.rerun()
        
        with col4:
            # Aktueller Monat und Jahr
            if 'current_month' not in st.session_state:
                st.session_state.current_month = datetime.now().month
                st.session_state.current_year = datetime.now().year
            
            month_names = ["Januar", "Februar", "März", "April", "Mai", "Juni", 
                          "Juli", "August", "September", "Oktober", "November", "Dezember"]
            month_name = month_names[st.session_state.current_month - 1]
            st.markdown(f"**{month_name} {st.session_state.current_year}**")
        
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
        
        st.markdown(f"**Monatssumme: ${month_total:,.2f} ({month_trades} Trades)**")
        
        # CSS für Kalender - Vereinfacht und größer
        st.markdown("""
        <style>
        .calendar-day {
            min-height: 100px;
            padding: 10px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            background-color: white;
            position: relative;
            text-align: center;
        }
        .calendar-day.empty {
            background-color: #f8f9fa;
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
            font-size: 16px;
            margin-bottom: 8px;
            color: #495057;
        }
        .daily-pnl {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
            color: #000;
        }
        .trade-count {
            font-size: 14px;
            color: #6c757d;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Kalender erstellen - Immer 5 Wochen (35 Tage) für konsistente Darstellung
        cal = calendar.monthcalendar(st.session_state.current_year, st.session_state.current_month)
        
        # Wochentage-Header
        weekday_names = ['SUN', 'MON', 'TUE', 'WED', 'THR', 'FRI', 'SAT']
        
        st.markdown('<div class="calendar-container">', unsafe_allow_html=True)
        
        # Wochentags-Header mit Streamlit Columns (garantiert funktioniert)
        st.markdown("**📅 Wochentage:**")
        header_cols = st.columns(7)
        for i, day_name in enumerate(weekday_names):
            with header_cols[i]:
                st.markdown(f"**{day_name}**")
        
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
            # Für jede Woche 7 Spalten erstellen
            week_cols = st.columns(7)
            
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
                            
                            # CSS-Klasse basierend auf P&L
                            css_class = "positive" if daily_pnl_value > 0 else "negative"
                            if current_date.weekday() == 5:  # Samstag
                                css_class += " saturday"
                            
                            # Tagesdetails - Nur P&L und Anzahl Trades
                            pnl_text = f"${daily_pnl_value:,.2f}" if daily_pnl_value != 0 else "$0"
                            trade_text = f"{trade_count} Trade{'s' if trade_count != 1 else ''}"
                            
                            # HTML für den Tag - Vereinfacht
                            day_html = f"""
                            <div class="calendar-day {css_class}">
                                <div class="day-number">{day_number}</div>
                                <div class="daily-pnl">{pnl_text}</div>
                                <div class="trade-count">{trade_text}</div>
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
            
            # Abstand zwischen den Wochen
            st.markdown("---")
        
        # Zusätzliche Statistiken
        st.markdown("---")
        st.subheader("📊 Monatsstatistiken")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            positive_days = month_data[month_data['daily_pnl'] > 0]
            negative_days = month_data[month_data['daily_pnl'] < 0]
            
            st.metric("Positive Tage", len(positive_days))
        
        with col2:
            st.metric("Negative Tage", len(negative_days))
        
        with col3:
            if len(positive_days) > 0:
                avg_positive = positive_days['daily_pnl'].mean()
                st.metric("Ø Positiver Tag", f"${avg_positive:,.2f}")
            else:
                st.metric("Ø Positiver Tag", "$0.00")
        
        with col4:
            if len(negative_days) > 0:
                avg_negative = negative_days['daily_pnl'].mean()
                st.metric("Ø Negativer Tag", f"${avg_negative:,.2f}")
            else:
                st.metric("Ø Negativer Tag", "$0.00")
        
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
