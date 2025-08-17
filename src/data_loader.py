"""
Data Loader für Trade_Analysis
Lädt und verarbeitet Handelsdaten aus verschiedenen Quellen.
"""

import pandas as pd
import yfinance as yf
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import sqlite3


class DataLoader:
    """Klasse zum Laden und Verarbeiten von Handelsdaten."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialisiert den DataLoader.
        
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
                # Zuerst nach "Trade"-Tabelle suchen
                if 'Trade' in table_names:
                    table_name = 'Trade'
                    self.logger.info(f"Trade-Tabelle gefunden und ausgewählt: {table_name}")
                elif 'trade' in table_names:
                    table_name = 'trade'
                    self.logger.info(f"trade-Tabelle gefunden und ausgewählt: {table_name}")
                elif len(table_names) == 1:
                    table_name = table_names[0]
                    self.logger.info(f"Automatisch Tabelle ausgewählt: {table_name}")
                elif len(table_names) > 1:
                    # Versuche, die Tabelle mit den meisten Zeilen zu finden (wahrscheinlich die Haupttabelle)
                    max_rows = 0
                    for table in table_names:
                        cursor.execute(f"SELECT COUNT(*) FROM '{table}'")
                        row_count = cursor.fetchone()[0]
                        if row_count > max_rows:
                            max_rows = row_count
                            table_name = table
                    self.logger.info(f"Tabelle mit den meisten Zeilen ausgewählt: {table_name} ({max_rows} Zeilen)")
                else:
                    raise ValueError("Keine Tabellen in der Datenbank gefunden")
            
            # Tabellenstruktur analysieren
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            
            # Primärschlüssel identifizieren
            primary_keys = []
            for col in columns_info:
                if col[5] > 0:  # col[5] ist der Primärschlüssel-Index
                    primary_keys.append(col[1])
            
            self.logger.info(f"Tabellenspalten: {columns}")
            if primary_keys:
                self.logger.info(f"Primärschlüssel gefunden: {primary_keys}")
            
            # Alle Daten aus der Tabelle laden
            data = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
            conn.close()
            
            self.logger.info(f"Tradelog-Daten geladen: {len(data)} Zeilen, {len(columns)} Spalten")
            
            # Daten formatieren
            formatted_data = self._format_tradelog_data(data, primary_keys)
            
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Tradelog-Daten: {e}")
            raise
    
    def load_trade_table(self, db_path: str) -> pd.DataFrame:
        """
        Lädt spezifisch die Trade-Tabelle aus der SQLite-Datenbank.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            
        Returns:
            DataFrame mit den Trade-Daten
        """
        try:
            self.logger.info(f"Lade Trade-Tabelle aus SQLite: {db_path}")
            
            # Verbindung zur Datenbank herstellen
            conn = sqlite3.connect(db_path)
            
            # Tabellen in der Datenbank auflisten
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            self.logger.info(f"Verfügbare Tabellen: {table_names}")
            
            # Trade-Tabelle finden
            trade_table = None
            if 'Trade' in table_names:
                trade_table = 'Trade'
            elif 'trade' in table_names:
                trade_table = 'trade'
            else:
                # Nach Tabellen suchen, die "trade" im Namen enthalten
                for table in table_names:
                    if 'trade' in table.lower():
                        trade_table = table
                        break
            
            if trade_table is None:
                raise ValueError(f"Keine Trade-Tabelle gefunden. Verfügbare Tabellen: {table_names}")
            
            self.logger.info(f"Trade-Tabelle gefunden: {trade_table}")
            
            # Tabellenstruktur analysieren
            cursor.execute(f"PRAGMA table_info('{trade_table}')")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            
            # Primärschlüssel identifizieren
            primary_keys = []
            for col in columns_info:
                if col[5] > 0:  # col[5] ist der Primärschlüssel-Index
                    primary_keys.append(col[1])
            
            self.logger.info(f"Trade-Tabellenspalten: {columns}")
            if primary_keys:
                self.logger.info(f"Primärschlüssel gefunden: {primary_keys}")
            
            # Alle Daten aus der Trade-Tabelle laden
            data = pd.read_sql_query(f"SELECT * FROM '{trade_table}'", conn)
            conn.close()
            
            self.logger.info(f"Trade-Daten geladen: {len(data)} Zeilen, {len(columns)} Spalten")
            
            # Daten formatieren
            formatted_data = self._format_tradelog_data(data, primary_keys)
            
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Trade-Tabelle: {e}")
            raise
    
    def _format_tradelog_data(self, data: pd.DataFrame, primary_keys: Optional[List[str]] = None) -> pd.DataFrame:
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
            
            # Spaltennamen BEIBEHALTEN (ursprüngliche Namen aus der Datenbank)
            # formatted.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in formatted.columns]
            
            # .NET-Timestamp-Spalten identifizieren und konvertieren
            net_timestamp_columns = []
            for col in formatted.columns:
                if any(keyword in col.lower() for keyword in ['dateopened', 'dateclosed', 'opened', 'closed']):
                    net_timestamp_columns.append(col)
            
            for col in net_timestamp_columns:
                try:
                    # .NET-Timestamp zu Datetime konvertieren
                    # .NET-Timestamp ist die Anzahl der Ticks seit dem 1. Januar 0001
                    # 1 Tick = 100 Nanosekunden
                    # Konvertierung: (timestamp - 621355968000000000) / 10000000
                    formatted[col] = pd.to_datetime(
                        (formatted[col] - 621355968000000000) / 10000000, 
                        unit='s',
                        errors='coerce'
                    )
                    self.logger.info(f".NET-Timestamp-Spalte konvertiert: {col}")
                except Exception as e:
                    self.logger.warning(f"Konnte .NET-Timestamp-Spalte {col} nicht konvertieren: {e}")
                    # Fallback: Versuche normale Datumskonvertierung
                    try:
                        formatted[col] = pd.to_datetime(formatted[col], errors='coerce')
                        self.logger.info(f"Fallback-Datumskonvertierung für {col} erfolgreich")
                    except Exception as e2:
                        self.logger.warning(f"Auch Fallback-Datumskonvertierung für {col} fehlgeschlagen: {e2}")
            
            # Datumsspalten identifizieren und konvertieren (außer .NET-Timestamps)
            date_columns = []
            for col in formatted.columns:
                if (any(keyword in col.lower() for keyword in ['date', 'datum', 'time', 'zeit', 'timestamp']) and 
                    col not in net_timestamp_columns):
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
            
            # Primärschlüssel als erste Spalte setzen
            if primary_keys:
                # Primärschlüssel-Spalten zuerst setzen
                # Verwende die ursprünglichen Spaltennamen (ohne Änderung)
                pk_cols = []
                for pk in primary_keys:
                    # Suche nach der entsprechenden Spalte in den formatierten Daten
                    if pk in formatted.columns:
                        pk_cols.append(pk)
                    else:
                        # Fallback: Suche nach Spalten, die den Primärschlüssel-Namen enthalten
                        for col in formatted.columns:
                            if pk.lower() in col.lower() or col.lower() in pk.lower():
                                pk_cols.append(col)
                                break
                
                if pk_cols:
                    other_cols = [col for col in formatted.columns if col not in pk_cols]
                    
                    # Neue Spaltenreihenfolge: Primärschlüssel zuerst, dann andere Spalten
                    new_column_order = pk_cols + other_cols
                    formatted = formatted[new_column_order]
                    
                    self.logger.info(f"Primärschlüssel-Spalten als erste Spalten gesetzt: {pk_cols}")
                else:
                    self.logger.warning(f"Konnte keine der Primärschlüssel-Spalten {primary_keys} in den formatierten Daten finden")
            else:
                self.logger.warning("Keine Primärschlüssel-Spalten gefunden, daher keine Reihenfolge angepasst.")
            
            # INDEX NICHT auf Datum setzen - das könnte die DateOpened-Spalte verschwinden lassen
            # if date_columns or net_timestamp_columns:
            #     # Priorität: .NET-Timestamp-Spalten, dann normale Datumsspalten
            #     primary_date_col = net_timestamp_columns[0] if net_timestamp_columns else date_columns[0]
            #     formatted = formatted.set_index(primary_date_col)
            #     formatted = formatted.sort_index()
            #     self.logger.info(f"Index auf Datumsspalte gesetzt: {primary_date_col}")
            
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
                cursor.execute(f"PRAGMA table_info('{table_name}')")
                columns_info = cursor.fetchall()
                columns = [{'name': col[1], 'type': col[2], 'not_null': col[3], 'default': col[4], 'pk': col[5]} for col in columns_info]
                
                # Primärschlüssel identifizieren
                primary_keys = []
                for col in columns_info:
                    if col[5] > 0:  # col[5] ist der Primärschlüssel-Index
                        primary_keys.append(col[1])
                
                # Zeilenanzahl
                cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                row_count = cursor.fetchone()[0]
                
                # Beispieldaten (erste 5 Zeilen)
                cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 5")
                sample_data = cursor.fetchall()
                
                # Spaltennamen für Beispieldaten
                column_names = [col[1] for col in columns_info]
                
                db_info['tables'][table_name] = {
                    'columns': columns,
                    'primary_keys': primary_keys,
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
    
    def get_table_primary_keys(self, db_path: str, table_name: str) -> List[str]:
        """
        Identifiziert die Primärschlüssel einer bestimmten Tabelle.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            table_name: Name der Tabelle
            
        Returns:
            Liste der Primärschlüssel-Spaltennamen
        """
        try:
            self.logger.info(f"Identifiziere Primärschlüssel für Tabelle: {table_name}")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Tabellenstruktur analysieren
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns_info = cursor.fetchall()
            
            # Primärschlüssel identifizieren
            primary_keys = []
            for col in columns_info:
                if col[5] > 0:  # col[5] ist der Primärschlüssel-Index
                    primary_keys.append(col[1])
                    self.logger.info(f"Primärschlüssel gefunden: {col[1]} (Typ: {col[2]})")
            
            conn.close()
            
            if not primary_keys:
                self.logger.warning(f"Keine Primärschlüssel für Tabelle {table_name} gefunden")
            else:
                self.logger.info(f"Primärschlüssel für {table_name}: {primary_keys}")
            
            return primary_keys
            
        except Exception as e:
            self.logger.error(f"Fehler beim Identifizieren der Primärschlüssel: {e}")
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
