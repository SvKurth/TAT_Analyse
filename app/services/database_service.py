"""
Database Service für das Trade Analyse Tool
Verwaltet alle Datenbankverbindungen und -operationen.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from contextlib import contextmanager
from app.core.logging_service import get_logger
from app.core.error_handler import safe_execute, retry_on_error


class DatabaseService:
    """Service für alle Datenbankoperationen."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialisiert den DatabaseService.
        
        Args:
            config: Konfigurationsdictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        self._connection_pool = {}
        
    @contextmanager
    def get_connection(self, db_path: str):
        """
        Kontextmanager für Datenbankverbindungen.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            
        Yields:
            SQLite-Verbindung
        """
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            self.logger.debug(f"Datenbankverbindung zu {db_path} hergestellt")
            yield conn
        except Exception as e:
            self.logger.error(f"Fehler bei der Datenbankverbindung zu {db_path}: {e}")
            raise
        finally:
            if conn:
                conn.close()
                self.logger.debug(f"Datenbankverbindung zu {db_path} geschlossen")
    
    def is_sqlite_file(self, file_path: str) -> bool:
        """
        Prüft, ob eine Datei eine SQLite-Datenbank ist.
        
        Args:
            file_path: Pfad zur zu prüfenden Datei
            
        Returns:
            True wenn es sich um eine SQLite-Datenbank handelt
        """
        try:
            file_path = Path(file_path)
            
            # Prüfe Dateiendung
            sqlite_extensions = ['.db', '.db3', '.sqlite', '.sqlite3']
            if file_path.suffix.lower() in sqlite_extensions:
                # Prüfe Dateiinhalt (SQLite-Header)
                with open(file_path, 'rb') as f:
                    header = f.read(16)
                return header.startswith(b'SQLite format 3')
            
            return False
        except Exception as e:
            self.logger.error(f"Fehler beim Prüfen der SQLite-Datei {file_path}: {e}")
            return False
    
    def get_table_info(self, db_path: str) -> Dict[str, Any]:
        """
        Gibt detaillierte Informationen über die SQLite-Datenbank zurück.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            
        Returns:
            Dictionary mit Datenbankinformationen
        """
        try:
            self.logger.info(f"Analysiere SQLite-Datenbank: {db_path}")
            
            with self.get_connection(db_path) as conn:
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
                
                self.logger.info(f"Datenbankanalyse abgeschlossen: {len(table_names)} Tabellen gefunden")
                return db_info
                
        except Exception as e:
            self.logger.error(f"Fehler bei der Datenbankanalyse: {e}")
            raise
    
    def find_trade_table(self, db_path: str) -> Optional[str]:
        """
        Findet die Trade-Tabelle in der Datenbank.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            
        Returns:
            Name der Trade-Tabelle oder None
        """
        try:
            with self.get_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Tabellen auflisten
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
                    self.logger.warning(f"Keine Trade-Tabelle gefunden. Verfügbare Tabellen: {table_names}")
                    return None
                
                self.logger.info(f"Trade-Tabelle gefunden: {trade_table}")
                return trade_table
                
        except Exception as e:
            self.logger.error(f"Fehler beim Finden der Trade-Tabelle: {e}")
            raise
    
    def load_table_data(self, db_path: str, table_name: str) -> Tuple[pd.DataFrame, List[str]]:
        """
        Lädt alle Daten aus einer Tabelle.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            table_name: Name der Tabelle
            
        Returns:
            Tuple aus (DataFrame, Primärschlüssel-Liste)
        """
        try:
            self.logger.info(f"Lade Daten aus Tabelle: {table_name}")
            
            with self.get_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Prüfe ob Tabelle existiert
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if not cursor.fetchone():
                    raise ValueError(f"Tabelle '{table_name}' existiert nicht in der Datenbank")
                
                # Tabellenstruktur analysieren
                cursor.execute(f"PRAGMA table_info('{table_name}')")
                columns_info = cursor.fetchall()
                
                if not columns_info:
                    self.logger.warning(f"Tabelle '{table_name}' hat keine Spalten")
                    return pd.DataFrame(), []
                
                columns = [col[1] for col in columns_info]
                
                # Prüfe ob Tabelle Spalten hat
                if len(columns) == 0:
                    self.logger.warning(f"Tabelle '{table_name}' hat keine Spalten")
                    return pd.DataFrame(), []
                
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
                
                # Prüfe ob Daten geladen wurden
                if data.empty:
                    self.logger.warning(f"Tabelle '{table_name}' ist leer (keine Zeilen)")
                    return data, primary_keys
                
                # Prüfe ob DataFrame Spalten hat
                if len(data.columns) == 0:
                    self.logger.warning(f"Tabelle '{table_name}' hat keine Spalten in den geladenen Daten")
                    return data, primary_keys
                
                self.logger.info(f"Tabellendaten geladen: {len(data)} Zeilen, {len(columns)} Spalten")
                return data, primary_keys
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Tabellendaten: {e}")
            raise
    
    def execute_query(self, db_path: str, query: str) -> pd.DataFrame:
        """
        Führt eine SQL-Abfrage aus.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            query: SQL-Abfrage
            
        Returns:
            DataFrame mit den Abfrageergebnissen
        """
        try:
            self.logger.info(f"Führe SQL-Abfrage aus: {query[:50]}...")
            
            with self.get_connection(db_path) as conn:
                data = pd.read_sql_query(query, conn)
                
                self.logger.info(f"SQL-Abfrage erfolgreich ausgeführt: {len(data)} Zeilen")
                return data
                
        except Exception as e:
            self.logger.error(f"Fehler bei der SQL-Abfrage: {e}")
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
            
            with self.get_connection(db_path) as conn:
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
                
                if not primary_keys:
                    self.logger.warning(f"Keine Primärschlüssel für Tabelle {table_name} gefunden")
                else:
                    self.logger.info(f"Primärschlüssel für {table_name}: {primary_keys}")
                
                return primary_keys
                
        except Exception as e:
            self.logger.error(f"Fehler beim Identifizieren der Primärschlüssel: {e}")
            raise
