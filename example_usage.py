#!/usr/bin/env python3
"""
Beispiel für die Verwendung von Trade_Analysis
Zeigt, wie die verschiedenen Module verwendet werden können.
"""

import sys
from pathlib import Path

# Projektverzeichnis zum Python-Pfad hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.data_loader import DataLoader
from src.analysis import TradeAnalyzer
from src.visualization import ChartGenerator
from src.utils import setup_logging, load_config


def main():
    """Beispiel für die Verwendung von Trade_Analysis."""
    
    print("=== Trade_Analysis Beispiel ===\n")
    
    # 1. Logging einrichten
    print("1. Richte Logging ein...")
    setup_logging(log_level="INFO")
    
    # 2. Konfiguration laden
    print("2. Lade Konfiguration...")
    config = load_config("config/config.ini")
    
    # 3. Module initialisieren
    print("3. Initialisiere Module...")
    data_loader = DataLoader(config)
    analyzer = TradeAnalyzer(config)
    chart_gen = ChartGenerator(config)
    
    # 4. Beispiel mit Yahoo Finance Daten
    print("4. Lade Beispiel-Daten von Yahoo Finance...")
    try:
        # Apple Aktiendaten der letzten 6 Monate laden
        data = data_loader.load_yahoo_finance_data(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-06-30"
        )
        
        print(f"   Geladen: {len(data)} Datenpunkte für AAPL")
        
        # 5. Technische Analyse durchführen
        print("5. Führe technische Analyse durch...")
        data_with_indicators = analyzer.calculate_technical_indicators(data)
        
        # 6. Trading-Signale generieren
        print("6. Generiere Trading-Signale...")
        data_with_signals = analyzer.generate_trading_signals(data_with_indicators)
        
        # 7. Risikometriken berechnen
        print("7. Berechne Risikometriken...")
        risk_metrics = analyzer.calculate_risk_metrics(data)
        
        print(f"   Volatilität: {risk_metrics['volatility']:.2%}")
        print(f"   Max Drawdown: {risk_metrics['max_drawdown']:.2%}")
        print(f"   Sharpe Ratio: {risk_metrics['sharpe_ratio']:.2f}")
        
        # 8. Charts erstellen
        print("8. Erstelle Charts...")
        
        # Candlestick Chart
        candlestick_fig = chart_gen.create_candlestick_chart(
            data, "AAPL - Candlestick Chart"
        )
        
        # Technical Analysis Chart
        tech_analysis_fig = chart_gen.create_technical_analysis_chart(
            data_with_indicators, "AAPL - Technical Analysis"
        )
        
        # Trading Signals Chart
        signals_fig = chart_gen.create_trading_signals_chart(
            data_with_signals, "AAPL - Trading Signals"
        )
        
        # Risk Analysis Chart
        risk_fig = chart_gen.create_risk_analysis_chart(
            data, "AAPL - Risk Analysis"
        )
        
        # 9. Charts speichern
        print("9. Speichere Charts...")
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        chart_gen.save_chart(candlestick_fig, "output/aapl_candlestick.html")
        chart_gen.save_chart(tech_analysis_fig, "output/aapl_technical_analysis.html")
        chart_gen.save_chart(signals_fig, "output/aapl_trading_signals.html")
        chart_gen.save_chart(risk_fig, "output/aapl_risk_analysis.html")
        
        print("   Charts gespeichert im 'output' Verzeichnis")
        
        # 10. Dateninformationen anzeigen
        print("10. Zeige Dateninformationen...")
        data_info = data_loader.get_data_info(data)
        print(f"   Datenform: {data_info['shape']}")
        print(f"   Spalten: {', '.join(data_info['columns'])}")
        print(f"   Zeitraum: {data_info['first_date']} bis {data_info['last_date']}")
        
        print("\n=== Beispiel erfolgreich abgeschlossen! ===")
        print("Öffnen Sie die HTML-Dateien im 'output' Verzeichnis, um die Charts zu betrachten.")
        
    except Exception as e:
        print(f"Fehler beim Ausführen des Beispiels: {e}")
        print("Stellen Sie sicher, dass alle Abhängigkeiten installiert sind.")
        print("Führen Sie 'pip install -r requirements.txt' aus.")


if __name__ == "__main__":
    main()
