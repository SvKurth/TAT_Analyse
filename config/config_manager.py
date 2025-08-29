"""
Einfacher Konfigurationsmanager für das Dashboard
Speichert den zuletzt verwendeten Dateipfad in einer einfachen Textdatei
"""

import os
from pathlib import Path

class ConfigManager:
    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.last_file_config = self.config_dir / "last_file.txt"
        self.auto_load_config = self.config_dir / "auto_load.txt"
    
    def save_last_file_path(self, file_path):
        """Speichert den zuletzt verwendeten Dateipfad"""
        try:
            with open(self.last_file_config, 'w', encoding='utf-8') as f:
                f.write(file_path)
            return True
        except Exception as e:
            print(f"Fehler beim Speichern des Dateipfads: {e}")
            return False
    
    def get_last_file_path(self):
        """Holt den zuletzt verwendeten Dateipfad"""
        try:
            if self.last_file_config.exists():
                with open(self.last_file_config, 'r', encoding='utf-8') as f:
                    path = f.read().strip()
                    if path and os.path.exists(path):
                        return path
            return None
        except Exception as e:
            print(f"Fehler beim Laden des Dateipfads: {e}")
            return None
    
    def clear_last_file_path(self):
        """Löscht den gespeicherten Dateipfad"""
        try:
            if self.last_file_config.exists():
                self.last_file_config.unlink()
            return True
        except Exception as e:
            print(f"Fehler beim Löschen des Dateipfads: {e}")
            return False
    
    def save_auto_load_setting(self, auto_load):
        """Speichert die Auto-Load-Einstellung"""
        try:
            with open(self.auto_load_config, 'w', encoding='utf-8') as f:
                f.write('true' if auto_load else 'false')
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Auto-Load-Einstellung: {e}")
            return False
    
    def get_auto_load_setting(self):
        """Holt die Auto-Load-Einstellung"""
        try:
            if self.auto_load_config.exists():
                with open(self.auto_load_config, 'r', encoding='utf-8') as f:
                    setting = f.read().strip().lower()
                    return setting == 'true'
            return True  # Standard: Auto-Load aktiviert
        except Exception as e:
            print(f"Fehler beim Laden der Auto-Load-Einstellung: {e}")
            return True  # Standard: Auto-Load aktiviert
