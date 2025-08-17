#!/usr/bin/env python3
"""
Beispielskript für das Laden von SQLite-Tradelogdateien
Demonstriert die Verwendung des erweiterten DataLoaders.
"""

import sys
import logging
from pathlib import Path
import pandas as pd

# Projektverzeichnis zum Python-Pfad hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.data_loader import DataLoader
from src.utils import setup_logging, load_config


def main():
    """Hauptfunktion für das Laden von Tradelog-Daten."""
    
    # Logging einrichten
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Tradelog-Loader wird gestartet...")
        
        # Konfiguration laden
        config = load_config()
        logger.info("Konfiguration erfolgreich geladen")
        
        # DataLoader initialisieren
        data_loader = DataLoader(config)
        logger.info("DataLoader initialisiert")
        
        # Pfad zu Ihrer SQLite-Tradelogdatei
        # Ändern Sie diesen Pfad entsprechend Ihrer Dateistruktur
        tradelog_db_path = "path/to/your/tradelog.db"  # Hier Ihren tatsächlichen Pfad eintragen
        
        # Überprüfen, ob die Datei existiert
        if not Path(tradelog_db_path).exists():
            logger.error(f"Tradelog-Datei nicht gefunden: {tradelog_db_path}")
            logger.info("Bitte passen Sie den Pfad in der Variable 'tradelog_db_path' an")
            return
        
        # 1. Datenbankstruktur analysieren
        logger.info("Analysiere Datenbankstruktur...")
        db_info = data_loader.get_sqlite_table_info(tradelog_db_path)
        
        print("\n=== DATENBANKSTRUKTUR ===")
        print(f"Datenbank: {db_info['database_path']}")
        print(f"Anzahl Tabellen: {db_info['total_tables']}")
        
        for table_name, table_info in db_info['tables'].items():
            print(f"\nTabelle: {table_name}")
            print(f"  Zeilen: {table_info['row_count']}")
            print(f"  Spalten: {len(table_info['columns'])}")
            print("  Spaltenstruktur:")
            for col in table_info['columns']:
                print(f"    - {col['name']}: {col['type']}")
            
            print("  Beispieldaten (erste 3 Zeilen):")
            for i, row in enumerate(table_info['sample_data'][:3]):
                print(f"    Zeile {i+1}: {dict(zip(table_info['column_names'], row))}")
        
        # 2. Tradelog-Daten laden (automatische Tabellenerkennung)
        logger.info("Lade Tradelog-Daten...")
        tradelog_data = data_loader.load_tradelog_sqlite(tradelog_db_path)
        
        print(f"\n=== GELADENE DATEN ===")
        print(f"Anzahl Zeilen: {len(tradelog_data)}")
        print(f"Anzahl Spalten: {len(tradelog_data.columns)}")
        print(f"Spalten: {list(tradelog_data.columns)}")
        print(f"Datentypen:\n{tradelog_data.dtypes}")
        
        # 3. Dateninformationen anzeigen
        data_info = data_loader.get_data_info(tradelog_data)
        
        print(f"\n=== DATENINFORMATIONEN ===")
        print(f"Form: {data_info['shape']}")
        print(f"Fehlende Werte: {data_info['missing_values']}")
        print(f"Speicherverbrauch: {data_info['memory_usage'] / 1024:.2f} KB")
        
        if data_info['first_date'] and data_info['last_date']:
            print(f"Zeitraum: {data_info['first_date']} bis {data_info['last_date']}")
        
        # 4. Erste Zeilen der Daten anzeigen
        print(f"\n=== ERSTE 5 ZEILEN ===")
        print(tradelog_data.head())
        
        # 5. Daten in verschiedenen Formaten speichern
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Als CSV speichern
        csv_path = output_dir / "tradelog_data.csv"
        data_loader.save_data(tradelog_data, str(csv_path), 'csv')
        logger.info(f"Tradelog-Daten als CSV gespeichert: {csv_path}")
        
        # Als Excel speichern
        excel_path = output_dir / "tradelog_data.xlsx"
        data_loader.save_data(tradelog_data, str(excel_path), 'excel')
        logger.info(f"Tradelog-Daten als Excel gespeichert: {excel_path}")
        
        # 6. Zusätzliche Analysen
        print(f"\n=== ZUSÄTZLICHE ANALYSEN ===")
        
        # Numerische Spalten analysieren
        numeric_cols = tradelog_data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            print(f"Numerische Spalten: {list(numeric_cols)}")
            print(f"Statistiken für numerische Spalten:")
            print(tradelog_data[numeric_cols].describe())
        
        # Kategorische Spalten analysieren
        categorical_cols = tradelog_data.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            print(f"\nKategorische Spalten: {list(categorical_cols)}")
            for col in categorical_cols[:3]:  # Nur erste 3 Spalten
                unique_values = tradelog_data[col].nunique()
                print(f"  {col}: {unique_values} eindeutige Werte")
                if unique_values <= 10:  # Nur anzeigen wenn nicht zu viele
                    print(f"    Werte: {tradelog_data[col].unique()}")
        
        logger.info("Tradelog-Loader erfolgreich abgeschlossen!")
        
    except Exception as e:
        logger.error(f"Fehler im Tradelog-Loader: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
