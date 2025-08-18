"""
API Cache Module für Tradelog Dashboard
Enthält SQLite-Cache-Funktionalität für API-Preise
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
import pandas as pd

class APIPriceCache:
    """SQLite-Cache für API-Preise zur Performance-Verbesserung"""
    
    def __init__(self, cache_db_path: str = "cache/api_prices.db"):
        """Initialisiert den API-Price-Cache"""
        self.cache_db_path = Path(cache_db_path)
        self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_cache_db()
    
    def _init_cache_db(self):
        """Initialisiert die Cache-Datenbank mit den notwendigen Tabellen"""
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            
            # Tabelle für API-Preise
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    asset TEXT NOT NULL,
                    date TEXT NOT NULL,
                    option_type TEXT NOT NULL,
                    strike INTEGER NOT NULL,
                    price_data TEXT NOT NULL,  -- JSON der API-Antwort
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1
                )
            """)
            
            # Index für schnelle Suche
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_prices_lookup 
                ON api_prices(asset, date, option_type, strike)
            """)
            
            # Index für Cache-Bereinigung
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_prices_created 
                ON api_prices(created_at)
            """)
            
            conn.commit()
    
    def _generate_cache_key(self, asset: str, date: str, option_type: str, strike: int) -> str:
        """Generiert einen eindeutigen Cache-Schlüssel"""
        key_string = f"{asset}_{date}_{option_type}_{strike}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cached_price(self, asset: str, date: str, option_type: str, strike: int) -> Optional[List[Dict]]:
        """Holt gecachte API-Preise aus der Datenbank"""
        cache_key = self._generate_cache_key(asset, date, option_type, strike)
        
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            
            # Prüfe ob Cache-Eintrag existiert und nicht zu alt ist (7 Tage)
            cursor.execute("""
                SELECT price_data, created_at FROM api_prices 
                WHERE cache_key = ? AND created_at > datetime('now', '-7 days')
            """, (cache_key,))
            
            result = cursor.fetchone()
            
            if result:
                price_data, created_at = result
                
                # Aktualisiere Zugriffszähler und Zeit
                cursor.execute("""
                    UPDATE api_prices 
                    SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                    WHERE cache_key = ?
                """, (cache_key,))
                
                conn.commit()
                
                # Parse JSON zurück zu Python-Liste
                try:
                    return json.loads(price_data)
                except json.JSONDecodeError:
                    return None
            
            return None
    
    def cache_price_data(self, asset: str, date: str, option_type: str, strike: int, price_data: List[Dict]):
        """Speichert API-Preise in der Datenbank"""
        cache_key = self._generate_cache_key(asset, date, option_type, strike)
        
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            
            # Konvertiere Python-Liste zu JSON-String
            price_data_json = json.dumps(price_data)
            
            # Upsert: Insert oder Update
            cursor.execute("""
                INSERT OR REPLACE INTO api_prices 
                (cache_key, asset, date, option_type, strike, price_data, created_at, last_accessed, access_count)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
            """, (cache_key, asset, date, option_type, strike, price_data_json))
            
            conn.commit()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über den Cache zurück"""
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            
            # Gesamtanzahl Einträge
            cursor.execute("SELECT COUNT(*) FROM api_prices")
            total_entries = cursor.fetchone()[0]
            
            # Einträge der letzten 7 Tage
            cursor.execute("""
                SELECT COUNT(*) FROM api_prices 
                WHERE created_at > datetime('now', '-7 days')
            """)
            recent_entries = cursor.fetchone()[0]
            
            # Cache-Größe
            cursor.execute("SELECT SUM(LENGTH(price_data)) FROM api_prices")
            total_size_bytes = cursor.fetchone()[0] or 0
            total_size_mb = total_size_bytes / (1024 * 1024)
            
            # Meist genutzte Einträge
            cursor.execute("""
                SELECT asset, date, option_type, strike, access_count 
                FROM api_prices 
                ORDER BY access_count DESC 
                LIMIT 5
            """)
            top_entries = cursor.fetchall()
            
            return {
                'total_entries': total_entries,
                'recent_entries': recent_entries,
                'total_size_mb': round(total_size_mb, 2),
                'top_entries': top_entries
            }
    
    def clear_old_cache(self, days: int = 30):
        """Bereinigt alte Cache-Einträge"""
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM api_prices 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count
    
    def clear_all_cache(self):
        """Löscht alle Cache-Einträge"""
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM api_prices")
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count

def get_cache_instance() -> APIPriceCache:
    """Gibt eine Instanz des API-Price-Caches zurück"""
    return APIPriceCache()
