"""
Configuration Service für das Trade Analyse Tool
Erweiterte Konfigurationsverwaltung mit Validierung und Umgebungsvariablen.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from .logging_service import get_logger


@dataclass
class DatabaseConfig:
    """Datenbank-Konfiguration."""
    file: str = "trades.db"
    max_connections: int = 10
    timeout: float = 30.0
    check_same_thread: bool = False
    
    def validate(self) -> bool:
        """Validiert die Datenbank-Konfiguration."""
        if self.max_connections <= 0:
            raise ValueError("max_connections muss größer als 0 sein")
        if self.timeout <= 0:
            raise ValueError("timeout muss größer als 0 sein")
        return True


@dataclass
class LoggingConfig:
    """Logging-Konfiguration."""
    level: str = "INFO"
    console: bool = True
    file: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    def validate(self) -> bool:
        """Validiert die Logging-Konfiguration."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValueError(f"level muss einer von {valid_levels} sein")
        if self.max_file_size <= 0:
            raise ValueError("max_file_size muss größer als 0 sein")
        if self.backup_count < 0:
            raise ValueError("backup_count darf nicht negativ sein")
        return True


@dataclass
class DashboardConfig:
    """Dashboard-Konfiguration."""
    port: int = 8501
    open_browser: bool = True
    headless: bool = False
    theme: str = "light"
    page_title: str = "Trade Analyse Tool"
    
    def validate(self) -> bool:
        """Validiert die Dashboard-Konfiguration."""
        if not (1024 <= self.port <= 65535):
            raise ValueError("port muss zwischen 1024 und 65535 liegen")
        valid_themes = ["light", "dark"]
        if self.theme not in valid_themes:
            raise ValueError(f"theme muss einer von {valid_themes} sein")
        return True


@dataclass
class AnalysisConfig:
    """Analyse-Konfiguration."""
    default_currency: str = "EUR"
    decimal_places: int = 2
    timezone: str = "Europe/Berlin"
    date_format: str = "%Y-%m-%d"
    datetime_format: str = "%Y-%m-%d %H:%M:%S"
    
    def validate(self) -> bool:
        """Validiert die Analyse-Konfiguration."""
        if self.decimal_places < 0:
            raise ValueError("decimal_places darf nicht negativ sein")
        if self.decimal_places > 10:
            raise ValueError("decimal_places darf nicht größer als 10 sein")
        return True


@dataclass
class Config:
    """Hauptkonfiguration des Trade Analyse Tools."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    environment: str = "development"
    debug: bool = False
    
    def validate(self) -> bool:
        """Validiert die gesamte Konfiguration."""
        self.database.validate()
        self.logging.validate()
        self.dashboard.validate()
        self.analysis.validate()
        return True


class ConfigService:
    """Service für die Konfigurationsverwaltung."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisiert den ConfigService.
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
        """
        self.logger = get_logger(__name__)
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self._load_environment_variables()
        self._validate_config()
    
    def _get_default_config_path(self) -> str:
        """Gibt den Standard-Konfigurationspfad zurück."""
        project_root = Path(__file__).parent.parent.parent
        return str(project_root / "config" / "default.yaml")
    
    def _load_config(self) -> Config:
        """Lädt die Konfiguration aus der YAML-Datei."""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    yaml_data = yaml.safe_load(f)
                    self.logger.info(f"✅ Konfiguration geladen von: {self.config_path}")
                    return self._dict_to_config(yaml_data)
            else:
                self.logger.warning(f"⚠️ Konfigurationsdatei nicht gefunden: {self.config_path}")
                self.logger.info("📝 Verwende Standard-Konfiguration")
                return Config()
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Laden der Konfiguration: {e}")
            self.logger.info("📝 Verwende Standard-Konfiguration")
            return Config()
    
    def _dict_to_config(self, data: Dict[str, Any]) -> Config:
        """Konvertiert ein Dictionary in ein Config-Objekt."""
        config = Config()
        
        if 'database' in data:
            config.database = DatabaseConfig(**data['database'])
        if 'logging' in data:
            config.logging = LoggingConfig(**data['logging'])
        if 'dashboard' in data:
            config.dashboard = DashboardConfig(**data['dashboard'])
        if 'analysis' in data:
            config.analysis = AnalysisConfig(**data['analysis'])
        if 'environment' in data:
            config.environment = data['environment']
        if 'debug' in data:
            config.debug = data['debug']
        
        return config
    
    def _load_environment_variables(self):
        """Lädt Konfiguration aus Umgebungsvariablen."""
        # Datenbank
        if db_file := os.getenv('TAT_DB_FILE'):
            self.config.database.file = db_file
        if db_connections := os.getenv('TAT_DB_MAX_CONNECTIONS'):
            self.config.database.max_connections = int(db_connections)
        
        # Logging
        if log_level := os.getenv('TAT_LOG_LEVEL'):
            self.config.logging.level = log_level
        if log_file := os.getenv('TAT_LOG_FILE'):
            self.config.logging.file = log_file
        
        # Dashboard
        if dashboard_port := os.getenv('TAT_DASHBOARD_PORT'):
            self.config.dashboard.port = int(dashboard_port)
        if dashboard_headless := os.getenv('TAT_DASHBOARD_HEADLESS'):
            self.config.dashboard.headless = dashboard_headless.lower() == 'true'
        
        # Umgebung
        if env := os.getenv('TAT_ENVIRONMENT'):
            self.config.environment = env
        if debug := os.getenv('TAT_DEBUG'):
            self.config.debug = debug.lower() == 'true'
        
        self.logger.info("✅ Umgebungsvariablen geladen")
    
    def _validate_config(self):
        """Validiert die geladene Konfiguration."""
        try:
            self.config.validate()
            self.logger.info("✅ Konfiguration erfolgreich validiert")
        except Exception as e:
            self.logger.error(f"❌ Konfigurationsvalidierung fehlgeschlagen: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Gibt einen Konfigurationswert zurück.
        
        Args:
            key: Konfigurationsschlüssel (z.B. 'database.file')
            default: Standardwert bei fehlendem Schlüssel
            
        Returns:
            Konfigurationswert oder Standardwert
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = getattr(value, k)
            return value
        except AttributeError:
            return default
    
    def set(self, key: str, value: Any):
        """
        Setzt einen Konfigurationswert.
        
        Args:
            key: Konfigurationsschlüssel (z.B. 'database.file')
            value: Neuer Wert
        """
        keys = key.split('.')
        config_obj = self.config
        
        # Zum vorletzten Objekt navigieren
        for k in keys[:-1]:
            config_obj = getattr(config_obj, k)
        
        # Letzten Wert setzen
        setattr(config_obj, keys[-1], value)
        self.logger.info(f"🔧 Konfiguration aktualisiert: {key} = {value}")
    
    def save(self, path: Optional[str] = None):
        """
        Speichert die aktuelle Konfiguration.
        
        Args:
            path: Speicherpfad (optional)
        """
        save_path = path or self.config_path
        
        try:
            # Konfiguration in Dictionary konvertieren
            config_dict = {
                'database': {
                    'file': self.config.database.file,
                    'max_connections': self.config.database.max_connections,
                    'timeout': self.config.database.timeout,
                    'check_same_thread': self.config.database.check_same_thread
                },
                'logging': {
                    'level': self.config.logging.level,
                    'console': self.config.logging.console,
                    'file': self.config.logging.file,
                    'max_file_size': self.config.logging.max_file_size,
                    'backup_count': self.config.logging.backup_count
                },
                'dashboard': {
                    'port': self.config.dashboard.port,
                    'open_browser': self.config.dashboard.open_browser,
                    'headless': self.config.dashboard.headless,
                    'theme': self.config.dashboard.theme,
                    'page_title': self.config.dashboard.page_title
                },
                'analysis': {
                    'default_currency': self.config.analysis.default_currency,
                    'decimal_places': self.config.analysis.decimal_places,
                    'timezone': self.config.analysis.timezone,
                    'date_format': self.config.analysis.date_format,
                    'datetime_format': self.config.analysis.datetime_format
                },
                'environment': self.config.environment,
                'debug': self.config.debug
            }
            
            # YAML-Datei speichern
            save_dir = Path(save_path).parent
            save_dir.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            
            self.logger.info(f"💾 Konfiguration gespeichert in: {save_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Speichern der Konfiguration: {e}")
            raise
    
    def reload(self):
        """Lädt die Konfiguration neu."""
        self.logger.info("🔄 Konfiguration wird neu geladen...")
        self.config = self._load_config()
        self._load_environment_variables()
        self._validate_config()
        self.logger.info("✅ Konfiguration erfolgreich neu geladen")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung der Konfiguration zurück."""
        return {
            'environment': self.config.environment,
            'debug': self.config.debug,
            'database_file': self.config.database.file,
            'dashboard_port': self.config.dashboard.port,
            'log_level': self.config.logging.level,
            'currency': self.config.analysis.default_currency
        }


# Globale Instanz
_config_service = None


def get_config_service(config_path: Optional[str] = None) -> ConfigService:
    """
    Gibt die globale ConfigService-Instanz zurück.
    
    Args:
        config_path: Pfad zur Konfigurationsdatei
        
    Returns:
        ConfigService-Instanz
    """
    global _config_service
    
    if _config_service is None:
        _config_service = ConfigService(config_path)
    
    return _config_service


def get_config(key: str, default: Any = None) -> Any:
    """
    Kurzform für Konfigurationszugriff.
    
    Args:
        key: Konfigurationsschlüssel
        default: Standardwert
        
    Returns:
        Konfigurationswert
    """
    return get_config_service().get(key, default)
