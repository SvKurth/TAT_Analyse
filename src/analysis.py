"""
Trade Analyzer für Trade_Analysis
Führt verschiedene Analysen auf Handelsdaten durch.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
import ta


class TradeAnalyzer:
    """Klasse zur Analyse von Handelsdaten."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialisiert den TradeAnalyzer.
        
        Args:
            config: Konfigurationsdictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Berechnet technische Indikatoren für die Handelsdaten.
        
        Args:
            data: DataFrame mit OHLCV-Daten
            
        Returns:
            DataFrame mit zusätzlichen technischen Indikatoren
        """
        try:
            self.logger.info("Berechne technische Indikatoren...")
            
            # Sicherheitskopie erstellen
            df = data.copy()
            
            # Moving Averages
            df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['EMA_12'] = ta.trend.ema_indicator(df['Close'], window=12)
            df['EMA_26'] = ta.trend.ema_indicator(df['Close'], window=26)
            
            # RSI
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            
            # MACD
            df['MACD'] = ta.trend.macd_diff(df['Close'])
            df['MACD_Signal'] = ta.trend.macd_signal(df['Close'])
            
            # Bollinger Bands
            df['BB_Upper'] = ta.volatility.bollinger_hband(df['Close'])
            df['BB_Lower'] = ta.volatility.bollinger_lband(df['Close'])
            df['BB_Middle'] = ta.volatility.bollinger_mavg(df['Close'])
            
            # Stochastic
            df['Stoch_K'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'])
            df['Stoch_D'] = ta.momentum.stoch_signal(df['High'], df['Low'], df['Close'])
            
            # ATR (Average True Range)
            df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
            
            self.logger.info("Technische Indikatoren erfolgreich berechnet")
            return df
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Berechnung der technischen Indikatoren: {e}")
            raise
    
    def identify_support_resistance(self, data: pd.DataFrame, window: int = 20) -> Dict[str, List[float]]:
        """
        Identifiziert Unterstützungs- und Widerstandslevel.
        
        Args:
            data: DataFrame mit OHLCV-Daten
            window: Fenstergröße für die Analyse
            
        Returns:
            Dictionary mit Unterstützungs- und Widerstandslevel
        """
        try:
            self.logger.info("Identifiziere Unterstützungs- und Widerstandslevel...")
            
            highs = data['High'].rolling(window=window, center=True).max()
            lows = data['Low'].rolling(window=window, center=True).min()
            
            # Lokale Maxima und Minima finden
            resistance_levels = []
            support_levels = []
            
            for i in range(window, len(data) - window):
                if highs.iloc[i] == data['High'].iloc[i]:
                    resistance_levels.append(data['High'].iloc[i])
                if lows.iloc[i] == data['Low'].iloc[i]:
                    support_levels.append(data['Low'].iloc[i])
            
            # Duplikate entfernen und sortieren
            resistance_levels = sorted(list(set(resistance_levels)))
            support_levels = sorted(list(set(support_levels)))
            
            self.logger.info(f"Gefunden: {len(resistance_levels)} Widerstandslevel, {len(support_levels)} Unterstützungslevel")
            
            return {
                'resistance': resistance_levels,
                'support': support_levels
            }
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Identifikation von Unterstützungs- und Widerstandslevel: {e}")
            raise
    
    def calculate_risk_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Berechnet Risikometriken für die Handelsdaten.
        
        Args:
            data: DataFrame mit Handelsdaten
            
        Returns:
            Dictionary mit Risikometriken
        """
        try:
            self.logger.info("Berechne Risikometriken...")
            
            # Returns berechnen
            returns = data['Close'].pct_change().dropna()
            
            # Volatilität
            volatility = returns.std() * np.sqrt(252)  # Annualisiert
            
            # Value at Risk (VaR)
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            
            # Maximum Drawdown
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Sharpe Ratio (angenommen risikofreier Zinssatz = 0)
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
            
            # Sortino Ratio
            negative_returns = returns[returns < 0]
            downside_deviation = negative_returns.std() * np.sqrt(252)
            sortino_ratio = returns.mean() / downside_deviation if downside_deviation != 0 else 0
            
            metrics = {
                'volatility': volatility,
                'var_95': var_95,
                'var_99': var_99,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio
            }
            
            self.logger.info("Risikometriken erfolgreich berechnet")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Berechnung der Risikometriken: {e}")
            raise
    
    def generate_trading_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generiert Trading-Signale basierend auf technischen Indikatoren.
        
        Args:
            data: DataFrame mit technischen Indikatoren
            
        Returns:
            DataFrame mit Trading-Signalen
        """
        try:
            self.logger.info("Generiere Trading-Signale...")
            
            df = data.copy()
            
            # RSI-basierte Signale
            df['RSI_Signal'] = 0
            df.loc[df['RSI'] < 30, 'RSI_Signal'] = 1  # Überverkauft
            df.loc[df['RSI'] > 70, 'RSI_Signal'] = -1  # Überkauft
            
            # MACD-basierte Signale
            df['MACD_Signal_Cross'] = 0
            df.loc[df['MACD'] > df['MACD_Signal'], 'MACD_Signal_Cross'] = 1
            df.loc[df['MACD'] < df['MACD_Signal'], 'MACD_Signal_Cross'] = -1
            
            # Moving Average Crossover
            df['MA_Signal'] = 0
            df.loc[df['SMA_20'] > df['SMA_50'], 'MA_Signal'] = 1
            df.loc[df['SMA_20'] < df['SMA_50'], 'MA_Signal'] = -1
            
            # Bollinger Band Signale
            df['BB_Signal'] = 0
            df.loc[df['Close'] < df['BB_Lower'], 'BB_Signal'] = 1  # Untere Band berührt
            df.loc[df['Close'] > df['BB_Upper'], 'BB_Signal'] = -1  # Obere Band berührt
            
            # Kombinierte Signale
            df['Combined_Signal'] = (
                df['RSI_Signal'] + 
                df['MACD_Signal_Cross'] + 
                df['MA_Signal'] + 
                df['BB_Signal']
            )
            
            # Signal-Stärke kategorisieren
            df['Signal_Strength'] = pd.cut(
                df['Combined_Signal'], 
                bins=[-4, -2, 0, 2, 4], 
                labels=['Stark Verkaufen', 'Verkaufen', 'Neutral', 'Kaufen', 'Stark Kaufen']
            )
            
            self.logger.info("Trading-Signale erfolgreich generiert")
            return df
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Generierung der Trading-Signale: {e}")
            raise
