"""
Chart Generator für Trade_Analysis
Erstellt verschiedene Charts und Visualisierungen für Handelsdaten.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class ChartGenerator:
    """Klasse zur Erstellung von Charts und Visualisierungen."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialisiert den ChartGenerator.
        
        Args:
            config: Konfigurationsdictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Matplotlib-Stil einrichten
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def create_candlestick_chart(self, data: pd.DataFrame, title: str = "Candlestick Chart") -> go.Figure:
        """
        Erstellt ein Candlestick-Chart mit Plotly.
        
        Args:
            data: DataFrame mit OHLCV-Daten
            title: Titel des Charts
            
        Returns:
            Plotly Figure-Objekt
        """
        try:
            self.logger.info("Erstelle Candlestick-Chart...")
            
            fig = go.Figure(data=[go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='OHLC'
            )])
            
            fig.update_layout(
                title=title,
                yaxis_title='Preis',
                xaxis_title='Datum',
                template='plotly_white'
            )
            
            self.logger.info("Candlestick-Chart erfolgreich erstellt")
            return fig
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Erstellung des Candlestick-Charts: {e}")
            raise
    
    def create_technical_analysis_chart(self, data: pd.DataFrame, title: str = "Technical Analysis") -> go.Figure:
        """
        Erstellt ein umfassendes Chart mit technischen Indikatoren.
        
        Args:
            data: DataFrame mit technischen Indikatoren
            title: Titel des Charts
            
        Returns:
            Plotly Figure-Objekt
        """
        try:
            self.logger.info("Erstelle Technical Analysis Chart...")
            
            # Subplots erstellen
            fig = make_subplots(
                rows=4, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=('Preis & Moving Averages', 'RSI', 'MACD', 'Bollinger Bands'),
                row_heights=[0.4, 0.2, 0.2, 0.2]
            )
            
            # Candlestick Chart
            fig.add_trace(go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='OHLC'
            ), row=1, col=1)
            
            # Moving Averages
            if 'SMA_20' in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['SMA_20'],
                    name='SMA 20', line=dict(color='blue')
                ), row=1, col=1)
            
            if 'SMA_50' in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['SMA_50'],
                    name='SMA 50', line=dict(color='red')
                ), row=1, col=1)
            
            # RSI
            if 'RSI' in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['RSI'],
                    name='RSI', line=dict(color='purple')
                ), row=2, col=1)
                
                # RSI Überkauft/Überverkauft Linien
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            # MACD
            if 'MACD' in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['MACD'],
                    name='MACD', line=dict(color='blue')
                ), row=3, col=1)
                
                if 'MACD_Signal' in data.columns:
                    fig.add_trace(go.Scatter(
                        x=data.index, y=data['MACD_Signal'],
                        name='MACD Signal', line=dict(color='red')
                    ), row=3, col=1)
            
            # Bollinger Bands
            if 'BB_Upper' in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['BB_Upper'],
                    name='BB Upper', line=dict(color='gray', dash='dash')
                ), row=4, col=1)
                
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['BB_Lower'],
                    name='BB Lower', line=dict(color='gray', dash='dash'),
                    fill='tonexty'
                ), row=4, col=1)
                
                if 'BB_Middle' in data.columns:
                    fig.add_trace(go.Scatter(
                        x=data.index, y=data['BB_Middle'],
                        name='BB Middle', line=dict(color='gray')
                    ), row=4, col=1)
            
            fig.update_layout(
                title=title,
                height=800,
                template='plotly_white'
            )
            
            self.logger.info("Technical Analysis Chart erfolgreich erstellt")
            return fig
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Erstellung des Technical Analysis Charts: {e}")
            raise
    
    def create_risk_analysis_chart(self, data: pd.DataFrame, title: str = "Risk Analysis") -> go.Figure:
        """
        Erstellt Charts für die Risikoanalyse.
        
        Args:
            data: DataFrame mit Handelsdaten
            title: Titel des Charts
            
        Returns:
            Plotly Figure-Objekt
        """
        try:
            self.logger.info("Erstelle Risk Analysis Chart...")
            
            # Returns berechnen
            returns = data['Close'].pct_change().dropna()
            
            # Subplots erstellen
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Returns Distribution', 'Cumulative Returns', 'Drawdown', 'Rolling Volatility'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Returns Distribution
            fig.add_trace(go.Histogram(
                x=returns, nbinsx=50, name='Returns',
                marker_color='lightblue'
            ), row=1, col=1)
            
            # Cumulative Returns
            cumulative_returns = (1 + returns).cumprod()
            fig.add_trace(go.Scatter(
                x=cumulative_returns.index, y=cumulative_returns,
                name='Cumulative Returns', line=dict(color='green')
            ), row=1, col=2)
            
            # Drawdown
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            fig.add_trace(go.Scatter(
                x=drawdown.index, y=drawdown,
                name='Drawdown', line=dict(color='red'),
                fill='tonexty'
            ), row=2, col=1)
            
            # Rolling Volatility
            rolling_vol = returns.rolling(window=20).std() * np.sqrt(252)
            fig.add_trace(go.Scatter(
                x=rolling_vol.index, y=rolling_vol,
                name='20-Day Volatility', line=dict(color='orange')
            ), row=2, col=2)
            
            fig.update_layout(
                title=title,
                height=600,
                template='plotly_white'
            )
            
            self.logger.info("Risk Analysis Chart erfolgreich erstellt")
            return fig
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Erstellung des Risk Analysis Charts: {e}")
            raise
    
    def create_trading_signals_chart(self, data: pd.DataFrame, title: str = "Trading Signals") -> go.Figure:
        """
        Erstellt ein Chart mit Trading-Signalen.
        
        Args:
            data: DataFrame mit Trading-Signalen
            title: Titel des Charts
            
        Returns:
            Plotly Figure-Objekt
        """
        try:
            self.logger.info("Erstelle Trading Signals Chart...")
            
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                subplot_titles=('Preis mit Signalen', 'Signal Stärke'),
                row_heights=[0.7, 0.3]
            )
            
            # Candlestick Chart
            fig.add_trace(go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='OHLC'
            ), row=1, col=1)
            
            # Trading Signale als Punkte
            if 'Combined_Signal' in data.columns:
                buy_signals = data[data['Combined_Signal'] > 0]
                sell_signals = data[data['Combined_Signal'] < 0]
                
                if not buy_signals.empty:
                    fig.add_trace(go.Scatter(
                        x=buy_signals.index, y=buy_signals['Low'] * 0.99,
                        mode='markers', name='Kauf-Signal',
                        marker=dict(symbol='triangle-up', size=10, color='green')
                    ), row=1, col=1)
                
                if not sell_signals.empty:
                    fig.add_trace(go.Scatter(
                        x=sell_signals.index, y=sell_signals['High'] * 1.01,
                        mode='markers', name='Verkauf-Signal',
                        marker=dict(symbol='triangle-down', size=10, color='red')
                    ), row=1, col=1)
            
            # Signal Stärke
            if 'Combined_Signal' in data.columns:
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['Combined_Signal'],
                    name='Signal Stärke', line=dict(color='purple'),
                    fill='tonexty'
                ), row=2, col=1)
                
                # Neutrale Linie
                fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
            
            fig.update_layout(
                title=title,
                height=700,
                template='plotly_white'
            )
            
            self.logger.info("Trading Signals Chart erfolgreich erstellt")
            return fig
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Erstellung des Trading Signals Charts: {e}")
            raise
    
    def save_chart(self, fig: go.Figure, file_path: str, format: str = 'html') -> None:
        """
        Speichert einen Chart in verschiedenen Formaten.
        
        Args:
            fig: Plotly Figure-Objekt
            file_path: Zielpfad
            format: Dateiformat ('html', 'png', 'pdf')
        """
        try:
            self.logger.info(f"Speichere Chart in {format}-Format: {file_path}")
            
            if format == 'html':
                fig.write_html(file_path)
            elif format == 'png':
                fig.write_image(file_path)
            elif format == 'pdf':
                fig.write_image(file_path)
            else:
                raise ValueError(f"Nicht unterstütztes Format: {format}")
                
            self.logger.info(f"Chart erfolgreich gespeichert: {file_path}")
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern des Charts: {e}")
            raise
