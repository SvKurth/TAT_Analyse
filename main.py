#!/usr/bin/env python3
"""
Trade_Analysis - Hauptprogramm
Ein umfassendes Tool zur Analyse von Handelsdaten und Trading-Strategien.
"""

import sys
import logging
from pathlib import Path

# Projektverzeichnis zum Python-Pfad hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.data_loader import DataLoader
from src.analysis import TradeAnalyzer
from src.visualization import ChartGenerator
from src.utils import setup_logging, load_config


def main():
    """Hauptfunktion des Trade_Analysis Programms."""
    
    # Logging einrichten
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Trade_Analysis wird gestartet...")
        
        # Konfiguration laden
        config = load_config()
        logger.info("Konfiguration erfolgreich geladen")
        
        # Datenlader initialisieren
        data_loader = DataLoader(config)
        logger.info("Datenlader initialisiert")
        
        # Trade Analyzer initialisieren
        analyzer = TradeAnalyzer(config)
        logger.info("Trade Analyzer initialisiert")
        
        # Chart Generator initialisieren
        chart_gen = ChartGenerator(config)
        logger.info("Chart Generator initialisiert")
        
        # Beispiel-Analyse durchführen
        logger.info("Starte Beispiel-Analyse...")
        
        # Hier können Sie Ihre spezifische Analyse-Logik implementieren
        
        logger.info("Trade_Analysis erfolgreich abgeschlossen!")
        
    except Exception as e:
        logger.error(f"Fehler in Trade_Analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
