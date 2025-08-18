"""
API & Charts Module für Tradelog Dashboard
Enthält alle API-Funktionen und Chart-Erstellung
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import requests
import json

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
