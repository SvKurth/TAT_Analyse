"""
Database Utils Module für Tradelog Dashboard
Enthält SQLite-Funktionen und Hilfsfunktionen
"""

from pathlib import Path

def is_sqlite_file(file_path: str) -> bool:
    """Prüft, ob eine Datei eine SQLite-Datenbank ist."""
    sqlite_extensions = ['.db', '.db3', '.sqlite', '.sqlite3']
    file_path = Path(file_path)
    
    # Prüfe Dateiendung
    if file_path.suffix.lower() in sqlite_extensions:
        return True
    
    # Prüfe Dateiinhalt (SQLite-Header)
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)
            return header.startswith(b'SQLite format 3')
    except:
        return False

def load_database(file_path: str) -> str:
    """Lädt eine Datenbank und gibt den Pfad zurück."""
    if is_sqlite_file(file_path):
        return file_path
    else:
        raise ValueError(f"Die Datei {file_path} scheint keine gültige SQLite-Datenbank zu sein.")
