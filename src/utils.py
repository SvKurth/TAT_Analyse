"""
Utility-Funktionen für Trade_Analysis
Hilfsfunktionen für Logging, Konfiguration und andere allgemeine Aufgaben.
"""

import logging
import configparser
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
import yaml


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Richtet das Logging-System ein.
    
    Args:
        log_level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optionaler Pfad zur Log-Datei
    """
    # Log-Level konvertieren
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Ungültiges Log-Level: {log_level}")
    
    # Logging-Format konfigurieren
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Root Logger konfigurieren
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[]
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    
    # Root Logger Handler hinzufügen
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    
    # File Handler (optional)
    if log_file:
        # Logs-Verzeichnis erstellen, falls es nicht existiert
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        
        root_logger.addHandler(file_handler)
    
    # Logging-Start
    logging.info(f"Logging-System initialisiert mit Level: {log_level}")


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Lädt die Konfiguration aus einer Datei oder erstellt Standardwerte.
    
    Args:
        config_file: Optionaler Pfad zur Konfigurationsdatei
        
    Returns:
        Dictionary mit Konfigurationswerten
    """
    config = {}
    
    # Standard-Konfiguration
    default_config = {
        'data': {
            'data_dir': 'data',
            'output_dir': 'output',
            'cache_dir': 'cache'
        },
        'analysis': {
            'rsi_period': '14',
            'sma_short': '20',
            'sma_long': '50',
            'macd_fast': '12',
            'macd_slow': '26',
            'macd_signal': '9',
            'bb_period': '20',
            'bb_std': '2'
        },
        'visualization': {
            'chart_theme': 'plotly_white',
            'chart_height': '800',
            'save_format': 'html'
        },
        'logging': {
            'level': 'INFO',
            'log_file': 'logs/trade_analysis.log'
        }
    }
    
    # Konfigurationsdatei laden, falls vorhanden
    if config_file and os.path.exists(config_file):
        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(config_file)
            
            # Konfiguration in Dictionary konvertieren
            for section in config_parser.sections():
                config[section] = {}
                for key, value in config_parser.items(section):
                    config[section][key] = value
                    
            logging.info(f"Konfiguration aus {config_file} geladen")
        except Exception as e:
            logging.warning(f"Fehler beim Laden der Konfigurationsdatei: {e}")
            logging.info("Verwende Standard-Konfiguration")
            config = default_config
    else:
        logging.info("Keine Konfigurationsdatei gefunden, verwende Standard-Konfiguration")
        config = default_config
    
    # Verzeichnisse erstellen
    _create_directories(config)
    
    return config


def _create_directories(config: Dict[str, Any]) -> None:
    """
    Erstellt die in der Konfiguration definierten Verzeichnisse.
    
    Args:
        config: Konfigurationsdictionary
    """
    directories = []
    
    # Verzeichnisse aus der Konfiguration extrahieren
    if 'data' in config:
        data_config = config['data']
        directories.extend([
            data_config.get('data_dir', 'data'),
            data_config.get('output_dir', 'output'),
            data_config.get('cache_dir', 'cache')
        ])
    
    if 'logging' in config:
        log_config = config['logging']
        if 'log_file' in log_config:
            log_file = log_config['log_file']
            log_dir = Path(log_file).parent
            directories.append(str(log_dir))
    
    # Verzeichnisse erstellen
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logging.debug(f"Verzeichnis erstellt/überprüft: {directory}")
        except Exception as e:
            logging.warning(f"Konnte Verzeichnis {directory} nicht erstellen: {e}")


def load_yaml_config(config_file: str = "config/default.yaml") -> Dict[str, Any]:
    """
    Lädt die YAML-Konfiguration aus einer Datei.
    
    Args:
        config_file: Pfad zur YAML-Konfigurationsdatei
        
    Returns:
        Dictionary mit Konfigurationswerten
    """
    config = {}
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file) or {}
            logging.info(f"YAML-Konfiguration aus {config_file} geladen")
        else:
            logging.warning(f"Konfigurationsdatei {config_file} nicht gefunden")
            config = {}
    except Exception as e:
        logging.error(f"Fehler beim Laden der YAML-Konfiguration: {e}")
        config = {}
    
    return config


def save_yaml_config(config: Dict[str, Any], config_file: str = "config/default.yaml") -> bool:
    """
    Speichert die YAML-Konfiguration in eine Datei.
    
    Args:
        config: Konfigurationsdictionary
        config_file: Pfad zur YAML-Konfigurationsdatei
        
    Returns:
        True wenn erfolgreich gespeichert, False sonst
    """
    try:
        # Verzeichnis erstellen, falls es nicht existiert
        config_dir = Path(config_file).parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False, allow_unicode=True, indent=2)
        
        logging.info(f"YAML-Konfiguration in {config_file} gespeichert")
        return True
    except Exception as e:
        logging.error(f"Fehler beim Speichern der YAML-Konfiguration: {e}")
        return False


def update_config_value(key_path: str, value: Any, config_file: str = "config/default.yaml") -> bool:
    """
    Aktualisiert einen einzelnen Wert in der YAML-Konfiguration.
    
    Args:
        key_path: Pfad zum Wert (z.B. "dashboard.last_file_path")
        value: Neuer Wert
        config_file: Pfad zur YAML-Konfigurationsdatei
        
    Returns:
        True wenn erfolgreich aktualisiert, False sonst
    """
    try:
        # Konfiguration laden
        config = load_yaml_config(config_file)
        
        # Wert in der verschachtelten Struktur setzen
        keys = key_path.split('.')
        current = config
        
        # Zum vorletzten Schlüssel navigieren
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Wert setzen
        current[keys[-1]] = value
        
        # Konfiguration speichern
        return save_yaml_config(config, config_file)
        
    except Exception as e:
        logging.error(f"Fehler beim Aktualisieren der Konfiguration: {e}")
        return False


def get_config_value(key_path: str, default: Any = None, config_file: str = "config/default.yaml") -> Any:
    """
    Holt einen einzelnen Wert aus der YAML-Konfiguration.
    
    Args:
        key_path: Pfad zum Wert (z.B. "dashboard.last_file_path")
        default: Standardwert falls der Schlüssel nicht gefunden wird
        config_file: Pfad zur YAML-Konfigurationsdatei
        
    Returns:
        Wert aus der Konfiguration oder Standardwert
    """
    try:
        config = load_yaml_config(config_file)
        
        # Wert in der verschachtelten Struktur suchen
        keys = key_path.split('.')
        current = config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
        
    except Exception as e:
        logging.error(f"Fehler beim Abrufen des Konfigurationswerts: {e}")
        return default


def save_config(config: Dict[str, Any], config_file: str) -> None:
    """
    Speichert die Konfiguration in eine Datei.
    
    Args:
        config: Konfigurationsdictionary
        config_file: Pfad zur Konfigurationsdatei
    """
    try:
        config_parser = configparser.ConfigParser()
        
        # Konfiguration in ConfigParser konvertieren
        for section, section_data in config.items():
            config_parser.add_section(section)
            for key, value in section_data.items():
                config_parser.set(section, key, str(value))
        
        # Konfigurationsdatei speichern
        config_dir = Path(config_file).parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            config_parser.write(f)
            
        logging.info(f"Konfiguration gespeichert in: {config_file}")
        
    except Exception as e:
        logging.error(f"Fehler beim Speichern der Konfiguration: {e}")
        raise


def get_project_root() -> Path:
    """
    Gibt den Projektroot-Pfad zurück.
    
    Returns:
        Path-Objekt zum Projektroot
    """
    return Path(__file__).parent.parent


def ensure_file_exists(file_path: str, create_if_missing: bool = True) -> bool:
    """
    Überprüft, ob eine Datei existiert und erstellt sie bei Bedarf.
    
    Args:
        file_path: Pfad zur Datei
        create_if_missing: Ob die Datei erstellt werden soll, falls sie fehlt
        
    Returns:
        True, wenn die Datei existiert oder erstellt wurde
    """
    path = Path(file_path)
    
    if path.exists():
        return True
    
    if create_if_missing:
        try:
            # Verzeichnis erstellen, falls es nicht existiert
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Leere Datei erstellen
            path.touch()
            logging.info(f"Datei erstellt: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Erstellen der Datei {file_path}: {e}")
            return False
    
    return False


def format_number(value: float, decimals: int = 2) -> str:
    """
    Formatiert eine Zahl mit der angegebenen Anzahl von Dezimalstellen.
    
    Args:
        value: Zu formatierende Zahl
        decimals: Anzahl der Dezimalstellen
        
    Returns:
        Formatierte Zahl als String
    """
    return f"{value:.{decimals}f}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Berechnet die prozentuale Änderung zwischen zwei Werten.
    
    Args:
        old_value: Alter Wert
        new_value: Neuer Wert
        
    Returns:
        Prozentuale Änderung
    """
    if old_value == 0:
        return 0.0
    
    return ((new_value - old_value) / old_value) * 100
