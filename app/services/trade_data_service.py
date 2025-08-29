"""
Trade Data Service für das Trade Analyse Tool
Hauptservice für alle Trade-Daten-Operationen.
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple
from app.services.database_service import DatabaseService
from app.services.data_processing_service import DataProcessingService
from app.core.logging_service import get_logger
from app.core.error_handler import safe_execute


class TradeDataService:
    """Hauptservice für alle Trade-Daten-Operationen."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialisiert den TradeDataService.
        
        Args:
            config: Konfigurationsdictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Services initialisieren
        self.database_service = DatabaseService(config)
        self.data_processing_service = DataProcessingService(config)
        
    def is_sqlite_file(self, file_path: str) -> bool:
        """
        Prüft, ob eine Datei eine SQLite-Datenbank ist.
        
        Args:
            file_path: Pfad zur zu prüfenden Datei
            
        Returns:
            True wenn es sich um eine SQLite-Datenbank handelt
        """
        return self.database_service.is_sqlite_file(file_path)
    
    def get_sqlite_table_info(self, db_path: str) -> Dict[str, Any]:
        """
        Gibt detaillierte Informationen über die SQLite-Datenbank zurück.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            
        Returns:
            Dictionary mit Datenbankinformationen
        """
        return self.database_service.get_table_info(db_path)
    
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
            
            # Trade-Tabelle finden
            trade_table = self.database_service.find_trade_table(db_path)
            if trade_table is None:
                self.logger.error(f"Keine Trade-Tabelle in der Datenbank {db_path} gefunden")
                # Fallback: Alle verfügbaren Tabellen anzeigen
                db_info = self.database_service.get_table_info(db_path)
                available_tables = list(db_info['tables'].keys())
                raise ValueError(f"Keine Trade-Tabelle in der Datenbank {db_path} gefunden. Verfügbare Tabellen: {available_tables}")
            
            # Daten laden
            data, primary_keys = self.database_service.load_table_data(db_path, trade_table)
            
            # Prüfe ob Daten geladen wurden
            if data is None:
                self.logger.error("Keine Daten aus der Trade-Tabelle geladen")
                raise ValueError("Keine Daten aus der Trade-Tabelle geladen")
            
            # Prüfe ob DataFrame leer ist
            if data.empty:
                self.logger.warning(f"Trade-Tabelle '{trade_table}' ist leer")
                return data  # Leerer DataFrame zurückgeben
            
            # Prüfe ob DataFrame Spalten hat
            if len(data.columns) == 0:
                self.logger.warning(f"Trade-Tabelle '{trade_table}' hat keine Spalten")
                return data  # DataFrame ohne Spalten zurückgeben
            
            # Prüfe ob DateOpened-Spalte bereits existiert und Probleme verursacht
            if 'DateOpened' in data.columns:
                self.logger.info("DateOpened-Spalte gefunden - prüfe auf Duplikate")
                
                # Verwende die spezielle Funktion zum Beheben von DateOpened-Problemen
                data = self.data_processing_service.fix_dateopened_issues(data)
            
            # Daten formatieren
            try:
                formatted_data = self.data_processing_service.format_trade_data(data, primary_keys)
            except Exception as format_error:
                self.logger.error(f"Fehler beim Formatieren der Daten: {format_error}")
                # Fallback: Verwende unformatierte Daten
                self.logger.warning("Verwende unformatierte Daten als Fallback")
                formatted_data = data
            
            # Prüfe ob formatierte Daten gültig sind
            if formatted_data is None:
                self.logger.error("Formatierte Daten sind None")
                raise ValueError("Formatierte Daten sind None")
            
            self.logger.info(f"Trade-Tabelle erfolgreich geladen: {len(formatted_data)} Zeilen")
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Trade-Tabelle: {e}")
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
            
            # Tabelle auswählen
            if table_name is None:
                table_name = self.database_service.find_trade_table(db_path)
                if table_name is None:
                    raise ValueError("Keine Trade-Tabelle in der Datenbank gefunden")
            
            # Daten laden
            data, primary_keys = self.database_service.load_table_data(db_path, table_name)
            
            # Daten formatieren
            formatted_data = self.data_processing_service.format_trade_data(data, primary_keys)
            
            self.logger.info(f"Tradelog-Daten erfolgreich geladen: {len(formatted_data)} Zeilen")
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Tradelog-Daten: {e}")
            raise
    
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
    
    def load_sqlite_data(self, db_path: str, query: str) -> pd.DataFrame:
        """
        Lädt Daten aus einer SQLite-Datenbank.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            query: SQL-Abfrage
            
        Returns:
            DataFrame mit den Abfrageergebnissen
        """
        return self.database_service.execute_query(db_path, query)
    
    def get_data_info(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Gibt Informationen über die geladenen Daten zurück.
        
        Args:
            data: Zu analysierende Daten
            
        Returns:
            Dictionary mit Dateninformationen
        """
        return self.data_processing_service.get_data_info(data)
    
    def save_data(self, data: pd.DataFrame, file_path: str, format: str = 'csv') -> None:
        """
        Speichert Daten in verschiedenen Formaten.
        
        Args:
            data: Zu speichernde Daten
            file_path: Zielpfad
            format: Dateiformat ('csv', 'excel', 'parquet')
        """
        self.data_processing_service.save_data(data, file_path, format)
    
    def get_table_primary_keys(self, db_path: str, table_name: str) -> list:
        """
        Identifiziert die Primärschlüssel einer bestimmten Tabelle.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            table_name: Name der Tabelle
            
        Returns:
            Liste der Primärschlüssel-Spaltennamen
        """
        return self.database_service.get_table_primary_keys(db_path, table_name)
