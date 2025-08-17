"""
Vereinfachter Data Loader für Trade_Analysis
Funktioniert ohne das ta Modul für technische Analysen.
"""

import pandas as pd
import yfinance as yf
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import sqlite3


class SimpleDataLoader:
    """Vereinfachte Klasse zum Laden und Verarbeiten von Handelsdaten."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialisiert den vereinfachten DataLoader.
        
        Args:
            config: Konfigurationsdictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_cache = {}
        
    def load_csv_data(self, file_path: str) -> pd.DataFrame:
        """
        Lädt Daten aus einer CSV-Datei.
        
        Args:
            file_path: Pfad zur CSV-Datei
            
        Returns:
            DataFrame mit den geladenen Daten
        """
        try:
            self.logger.info(f"Lade CSV-Daten aus: {file_path}")
            data = pd.read_csv(file_path)
            self.logger.info(f"CSV-Daten erfolgreich geladen: {len(data)} Zeilen")
            return data
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der CSV-Daten: {e}")
            raise
    
    def load_yahoo_finance_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Lädt Aktiendaten von Yahoo Finance.
        
        Args:
            symbol: Aktiensymbol (z.B. 'AAPL')
            start_date: Startdatum im Format 'YYYY-MM-DD'
            end_date: Enddatum im Format 'YYYY-MM-DD'
            
        Returns:
            DataFrame mit den Aktiendaten
        """
        try:
            self.logger.info(f"Lade Yahoo Finance Daten für {symbol}")
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            self.logger.info(f"Yahoo Finance Daten geladen: {len(data)} Zeilen")
            return data
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Yahoo Finance Daten: {e}")
            raise
    
    def load_sqlite_data(self, db_path: str, query: str) -> pd.DataFrame:
        """
        Lädt Daten aus einer SQLite-Datenbank.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            query: SQL-Abfrage
            
        Returns:
            DataFrame mit den Abfrageergebnissen
        """
        try:
            self.logger.info(f"Lade SQLite-Daten aus: {db_path}")
            conn = sqlite3.connect(db_path)
            data = pd.read_sql_query(query, conn)
            conn.close()
            self.logger.info(f"SQLite-Daten geladen: {len(data)} Zeilen")
            return data
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der SQLite-Daten: {e}")
            raise
    
    def load_tradelog_sqlite(self, db_path: str, table_name: Optional[str] = None) -> pd.DataFrame:
        """
        Lädt Tradelog-Daten aus einer SQLite-Datenbank und formatiert sie entsprechend.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            table_name: Name der Tabelle (optional, wird automatisch erkannt wenn None)
            
        Returns:
            DataFrame mit den formatierten Tradelog-Daten
        """
        try:
            self.logger.info(f"Lade Tradelog-Daten aus SQLite: {db_path}")
            
            # Verbindung zur Datenbank herstellen
            conn = sqlite3.connect(db_path)
            
            # Tabellen in der Datenbank auflisten
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            self.logger.info(f"Verfügbare Tabellen: {table_names}")
            
            # Tabelle auswählen (automatisch oder manuell)
            if table_name is None:
                if len(table_names) == 1:
                    table_name = table_names[0]
                    self.logger.info(f"Automatisch Tabelle ausgewählt: {table_name}")
                elif len(table_names) > 1:
                    # Versuche, die Tabelle mit den meisten Zeilen zu finden (wahrscheinlich die Haupttabelle)
                    max_rows = 0
                    for table in table_names:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        row_count = cursor.fetchone()[0]
                        if row_count > max_rows:
                            max_rows = row_count
                            table_name = table
                    self.logger.info(f"Tabelle mit den meisten Zeilen ausgewählt: {table_name} ({max_rows} Zeilen)")
                else:
                    raise ValueError("Keine Tabellen in der Datenbank gefunden")
            
            # Tabellenstruktur analysieren
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            
            self.logger.info(f"Tabellenspalten: {columns}")
            
            # Alle Daten aus der Tabelle laden
            data = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            conn.close()
            
            self.logger.info(f"Tradelog-Daten geladen: {len(data)} Zeilen, {len(columns)} Spalten")
            
            # Daten formatieren
            formatted_data = self._format_tradelog_data(data)
            
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Tradelog-Daten: {e}")
            raise
    
    def _format_tradelog_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Formatiert die geladenen Tradelog-Daten in ein einheitliches Format.
        
        Args:
            data: Rohdaten aus der SQLite-Datenbank
            
        Returns:
            Formatierte Daten
        """
        try:
            self.logger.info("Formatiere Tradelog-Daten...")
            
            # Kopie der Daten erstellen
            formatted = data.copy()
            
            # Spaltennamen standardisieren (kleinbuchstaben, Leerzeichen durch Unterstriche ersetzen)
            formatted.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in formatted.columns]
            
            # Datumsspalten identifizieren und konvertieren
            date_columns = []
            for col in formatted.columns:
                if any(keyword in col.lower() for keyword in ['date', 'datum', 'time', 'zeit', 'timestamp']):
                    date_columns.append(col)
            
            for col in date_columns:
                try:
                    formatted[col] = pd.to_datetime(formatted[col], errors='coerce')
                    self.logger.info(f"Datumsspalte konvertiert: {col}")
                except Exception as e:
                    self.logger.warning(f"Konnte Datumsspalte {col} nicht konvertieren: {e}")
            
            # Numerische Spalten identifizieren und konvertieren
            numeric_columns = []
            for col in formatted.columns:
                if any(keyword in col.lower() for keyword in ['price', 'preis', 'amount', 'betrag', 'quantity', 'menge', 'profit', 'gewinn', 'loss', 'verlust']):
                    numeric_columns.append(col)
            
            for col in numeric_columns:
                try:
                    formatted[col] = pd.to_numeric(formatted[col], errors='coerce')
                    self.logger.info(f"Numerische Spalte konvertiert: {col}")
                except Exception as e:
                    self.logger.warning(f"Konnte numerische Spalte {col} nicht konvertieren: {e}")
            
            # Index auf Datum setzen, falls verfügbar
            if date_columns:
                primary_date_col = date_columns[0]
                formatted = formatted.set_index(primary_date_col)
                formatted = formatted.sort_index()
                self.logger.info(f"Index auf Datumsspalte gesetzt: {primary_date_col}")
            
            # Duplikate entfernen
            initial_rows = len(formatted)
            formatted = formatted.drop_duplicates()
            if len(formatted) < initial_rows:
                self.logger.info(f"Duplikate entfernt: {initial_rows - len(formatted)} Zeilen")
            
            # Fehlende Werte behandeln
            missing_count = formatted.isnull().sum().sum()
            if missing_count > 0:
                self.logger.info(f"Fehlende Werte gefunden: {missing_count} insgesamt")
                
                # Numerische Spalten mit 0 füllen
                numeric_cols = formatted.select_dtypes(include=['number']).columns
                formatted[numeric_cols] = formatted[numeric_cols].fillna(0)
                
                # Textspalten mit 'Unbekannt' füllen
                text_cols = formatted.select_dtypes(include=['object']).columns
                formatted[text_cols] = formatted[text_cols].fillna('Unbekannt')
            
            self.logger.info(f"Tradelog-Daten erfolgreich formatiert: {len(formatted)} Zeilen")
            return formatted
            
        except Exception as e:
            self.logger.error(f"Fehler beim Formatieren der Tradelog-Daten: {e}")
            raise
    
    def get_sqlite_table_info(self, db_path: str) -> Dict[str, Any]:
        """
        Gibt detaillierte Informationen über die SQLite-Datenbank zurück.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            
        Returns:
            Dictionary mit Datenbankinformationen
        """
        try:
            self.logger.info(f"Analysiere SQLite-Datenbank: {db_path}")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Tabellen auflisten
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            db_info = {
                'database_path': db_path,
                'tables': {},
                'total_tables': len(table_names)
            }
            
            # Für jede Tabelle detaillierte Informationen sammeln
            for table_name in table_names:
                # Tabellenstruktur
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                columns = [{'name': col[1], 'type': col[2], 'not_null': col[3], 'default': col[4]} for col in columns_info]
                
                # Zeilenanzahl
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                # Beispieldaten (erste 5 Zeilen)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample_data = cursor.fetchall()
                
                # Spaltennamen für Beispieldaten
                column_names = [col[1] for col in columns_info]
                
                db_info['tables'][table_name] = {
                    'columns': columns,
                    'row_count': row_count,
                    'sample_data': sample_data,
                    'column_names': column_names
                }
            
            conn.close()
            
            self.logger.info(f"Datenbankanalyse abgeschlossen: {len(table_names)} Tabellen gefunden")
            return db_info
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Datenbankanalyse: {e}")
            raise
    
    def save_data(self, data: pd.DataFrame, file_path: str, format: str = 'csv') -> None:
        """
        Speichert Daten in verschiedenen Formaten.
        
        Args:
            data: Zu speichernde Daten
            file_path: Zielpfad
            format: Dateiformat ('csv', 'excel', 'parquet')
        """
        try:
            self.logger.info(f"Speichere Daten in {format}-Format: {file_path}")
            
            if format == 'csv':
                data.to_csv(file_path, index=False)
            elif format == 'excel':
                data.to_excel(file_path, index=False)
            elif format == 'parquet':
                data.to_parquet(file_path, index=False)
            else:
                raise ValueError(f"Nicht unterstütztes Format: {format}")
                
            self.logger.info(f"Daten erfolgreich gespeichert: {file_path}")
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Daten: {e}")
            raise
    
    def get_data_info(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Gibt Informationen über die geladenen Daten zurück.
        
        Args:
            data: Zu analysierende Daten
            
        Returns:
            Dictionary mit Dateninformationen
        """
        info = {
            'shape': data.shape,
            'columns': list(data.columns),
            'dtypes': data.dtypes.to_dict(),
            'missing_values': data.isnull().sum().to_dict(),
            'memory_usage': data.memory_usage(deep=True).sum()
        }
        
        if not data.empty:
            info.update({
                'first_date': data.index.min() if hasattr(data.index, 'min') else None,
                'last_date': data.index.max() if hasattr(data.index, 'max') else None,
                'numeric_columns': list(data.select_dtypes(include=['number']).columns)
            })
        
        return info
