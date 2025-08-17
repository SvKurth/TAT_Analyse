"""
Data Processing Service für das Trade Analyse Tool
Verarbeitet und formatiert Handelsdaten.
"""

import pandas as pd
from typing import List, Optional
from app.core.logging_service import get_logger
from app.core.error_handler import safe_execute


class DataProcessingService:
    """Service für die Verarbeitung und Formatierung von Handelsdaten."""
    
    def __init__(self, config: dict):
        """
        Initialisiert den DataProcessingService.
        
        Args:
            config: Konfigurationsdictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        
    def format_trade_data(self, data: pd.DataFrame, primary_keys: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Formatiert die geladenen Trade-Daten in ein einheitliches Format.
        
        Args:
            data: Rohdaten aus der SQLite-Datenbank
            primary_keys: Liste der Primärschlüssel-Spalten
            
        Returns:
            Formatierte Daten
        """
        try:
            self.logger.info("Formatiere Trade-Daten...")
            
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
            
            self.logger.info(f"Trade-Daten erfolgreich formatiert: {len(formatted)} Zeilen")
            return formatted
            
        except Exception as e:
            self.logger.error(f"Fehler beim Formatieren der Trade-Daten: {e}")
            raise
    
    def get_data_info(self, data: pd.DataFrame) -> dict:
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
