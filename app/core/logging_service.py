"""
Logging Service für das Trade Analyse Tool
Zentrale Verwaltung aller Logs mit konfigurierbaren Levels.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class LoggingService:
    """Zentraler Logging-Service für alle Anwendungskomponenten."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialisiert den LoggingService.
        
        Args:
            config: Konfigurationsdictionary mit Logging-Einstellungen
        """
        self.config = config
        self.loggers = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Richtet das Logging-System ein."""
        logging_config = self.config.get('logging', {})
        
        # Standard-Logging-Konfiguration
        log_level = getattr(logging, logging_config.get('level', 'INFO').upper())
        console_output = logging_config.get('console', True)
        log_file = logging_config.get('file')
        
        # Root-Logger konfigurieren
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Bestehende Handler entfernen
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console-Handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # File-Handler (optional)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Gibt einen Logger für den angegebenen Namen zurück.
        
        Args:
            name: Name des Loggers (normalerweise __name__)
            
        Returns:
            Konfigurierter Logger
        """
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        
        return self.loggers[name]
    
    def set_level(self, level: str):
        """
        Ändert das Log-Level für alle Logger.
        
        Args:
            level: Neues Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = getattr(logging, level.upper())
        
        # Root-Logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Alle Handler
        for handler in root_logger.handlers:
            handler.setLevel(log_level)
        
        # Alle registrierten Logger
        for logger in self.loggers.values():
            logger.setLevel(log_level)
    
    def log_startup(self):
        """Loggt den Anwendungsstart."""
        logger = self.get_logger(__name__)
        logger.info("=" * 60)
        logger.info("🚀 Trade Analyse Tool gestartet")
        logger.info(f"📅 Startzeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🐍 Python Version: {sys.version}")
        logger.info("=" * 60)
    
    def log_shutdown(self):
        """Loggt das Herunterfahren der Anwendung."""
        logger = self.get_logger(__name__)
        logger.info("=" * 60)
        logger.info("🛑 Trade Analyse Tool wird beendet")
        logger.info(f"📅 Endzeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)


# Globale Instanz
_logging_service = None


def get_logging_service(config: Optional[Dict[str, Any]] = None) -> LoggingService:
    """
    Gibt die globale Logging-Service-Instanz zurück.
    
    Args:
        config: Konfiguration (nur beim ersten Aufruf erforderlich)
        
    Returns:
        LoggingService-Instanz
    """
    global _logging_service
    
    if _logging_service is None and config is not None:
        _logging_service = LoggingService(config)
    
    return _logging_service


def get_logger(name: str) -> logging.Logger:
    """
    Kurzform für Logger-Erstellung.
    
    Args:
        name: Name des Loggers
        
    Returns:
        Logger-Instanz
    """
    if _logging_service is None:
        # Fallback: Standard-Logger
        return logging.getLogger(name)
    
    return _logging_service.get_logger(name)
