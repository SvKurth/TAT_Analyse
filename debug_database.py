#!/usr/bin/env python3
"""
Debug-Skript für Datenbankprobleme
Hilft bei der Diagnose von "single positional indexer is out-of-bounds" Fehlern
"""

import sys
from pathlib import Path
import pandas as pd
import sqlite3

# Projektverzeichnisse zum Python-Pfad hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def debug_database(db_path: str):
    """Debuggt eine SQLite-Datenbank und zeigt detaillierte Informationen."""
    print(f"🔍 Debugge Datenbank: {db_path}")
    print("=" * 50)
    
    try:
        # Verbindung herstellen
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"📋 Verfügbare Tabellen: {table_names}")
        print()
        
        if not table_names:
            print("❌ Keine Tabellen in der Datenbank gefunden!")
            return
        
        # Für jede Tabelle detaillierte Informationen
        for table_name in table_names:
            print(f"📊 Tabelle: {table_name}")
            print("-" * 30)
            
            try:
                # Tabellenstruktur
                cursor.execute(f"PRAGMA table_info('{table_name}')")
                columns_info = cursor.fetchall()
                
                if not columns_info:
                    print("  ⚠️  Keine Spalteninformationen verfügbar")
                    continue
                
                print(f"  📝 Spalten: {len(columns_info)}")
                for col in columns_info:
                    pk_indicator = " 🔑" if col[5] > 0 else ""
                    print(f"    - {col[1]} ({col[2]}){pk_indicator}")
                
                # Zeilenanzahl
                cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                row_count = cursor.fetchone()[0]
                print(f"  📊 Zeilen: {row_count}")
                
                if row_count > 0:
                    # Beispieldaten (erste 3 Zeilen)
                    cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 3")
                    sample_data = cursor.fetchall()
                    
                    if sample_data:
                        print("  🔍 Beispieldaten:")
                        for i, row in enumerate(sample_data):
                            print(f"    Zeile {i+1}: {row[:5]}...")  # Erste 5 Spalten
                
                # Prüfe auf leere Spalten
                if row_count > 0:
                    cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 1")
                    first_row = cursor.fetchone()
                    if first_row:
                        print(f"  ✅ Erste Zeile hat {len(first_row)} Werte")
                        
                        # Prüfe auf None/leere Werte
                        none_count = sum(1 for val in first_row if val is None)
                        if none_count > 0:
                            print(f"  ⚠️  {none_count} None-Werte in der ersten Zeile")
                
                print()
                
            except Exception as e:
                print(f"  ❌ Fehler beim Analysieren der Tabelle {table_name}: {e}")
                print()
        
        # Spezielle Prüfung für Trade-Tabellen
        trade_tables = [t for t in table_names if 'trade' in t.lower()]
        if trade_tables:
            print("🎯 Trade-Tabellen gefunden:")
            for trade_table in trade_tables:
                print(f"  - {trade_table}")
                
                try:
                    # Versuche Daten zu laden
                    df = pd.read_sql_query(f"SELECT * FROM '{trade_table}'", conn)
                    print(f"    ✅ DataFrame geladen: {df.shape}")
                    
                    if not df.empty:
                        print(f"    📊 Spalten: {list(df.columns)}")
                        print(f"    🔢 Datentypen: {df.dtypes.to_dict()}")
                        
                        # Prüfe auf leere Spalten
                        empty_cols = [col for col in df.columns if df[col].isna().all()]
                        if empty_cols:
                            print(f"    ⚠️  Leere Spalten: {empty_cols}")
                        
                        # Prüfe auf Duplikate
                        duplicates = df.duplicated().sum()
                        if duplicates > 0:
                            print(f"    ⚠️  Duplikate: {duplicates}")
                    
                except Exception as e:
                    print(f"    ❌ Fehler beim Laden der Daten: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler beim Verbinden zur Datenbank: {e}")

def main():
    """Hauptfunktion."""
    if len(sys.argv) != 2:
        print("Verwendung: python debug_database.py <pfad_zur_datenbank>")
        print("Beispiel: python debug_database.py ./data/tradelog.db3")
        return
    
    db_path = sys.argv[1]
    
    if not Path(db_path).exists():
        print(f"❌ Datei nicht gefunden: {db_path}")
        return
    
    debug_database(db_path)

if __name__ == "__main__":
    main()
