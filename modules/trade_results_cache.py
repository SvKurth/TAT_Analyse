"""
Trade Results Cache Module für Tradelog Dashboard
Enthält SQLite-Cache für bereits berechnete Handelsende- und Peak-Preise
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
import pandas as pd

class TradeResultsCache:
    """SQLite-Cache für bereits berechnete Trade-Ergebnisse"""
    
    def __init__(self, cache_db_path: str = "cache/trade_results.db"):
        """Initialisiert den Trade-Results-Cache"""
        self.cache_db_path = Path(cache_db_path)
        self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_cache_db()
    
    def _init_cache_db(self):
        """Initialisiert die Cache-Datenbank mit den notwendigen Tabellen"""
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            
            # Tabelle für Trade-Ergebnisse
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    trade_id TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    option_type TEXT NOT NULL,
                    strike INTEGER NOT NULL,
                    handelsende_preis REAL,
                    peak_preis REAL,
                    peak_zeit TEXT,
                    api_link TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1
                )
            """)
            
            # Index für schnelle Suche
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_results_lookup 
                ON trade_results(trade_id, trade_date, option_type, strike)
            """)
            
            # Index für Cache-Bereinigung
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_results_created 
                ON trade_results(created_at)
            """)
            
            conn.commit()
    
    def _generate_cache_key(self, trade_id: str, trade_date: str, option_type: str, strike: int) -> str:
        """Generiert einen eindeutigen Cache-Schlüssel"""
        key_string = f"{trade_id}_{trade_date}_{option_type}_{strike}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cached_results(self, trade_id: str, trade_date: str, option_type: str, strike: int) -> Optional[Dict]:
        """Holt gecachte Trade-Ergebnisse aus der Datenbank"""
        cache_key = self._generate_cache_key(trade_id, trade_date, option_type, strike)
        
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            
            # Prüfe ob Cache-Eintrag existiert und nicht zu alt ist (30 Tage)
            cursor.execute("""
                SELECT handelsende_preis, peak_preis, peak_zeit, api_link, created_at 
                FROM trade_results 
                WHERE cache_key = ? AND created_at > datetime('now', '-30 days')
            """, (cache_key,))
            
            result = cursor.fetchone()
            
            if result:
                handelsende_preis, peak_preis, peak_zeit, api_link, created_at = result
                
                # Aktualisiere Zugriffszähler und Zeit
                cursor.execute("""
                    UPDATE trade_results 
                    SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                    WHERE cache_key = ?
                """, (cache_key,))
                
                conn.commit()
                
                return {
                    'handelsende_preis': handelsende_preis,
                    'peak_preis': peak_preis,
                    'peak_zeit': peak_zeit,
                    'api_link': api_link,
                    'cache_hit': True
                }
            
            return None
    
    def cache_trade_results(self, trade_id: str, trade_date: str, option_type: str, strike: int, 
                           handelsende_preis: float, peak_preis: float, peak_zeit: str, api_link: str):
        """Speichert berechnete Trade-Ergebnisse in der Datenbank"""
        cache_key = self._generate_cache_key(trade_id, trade_date, option_type, strike)
        
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            
            # Upsert: Insert oder Update
            cursor.execute("""
                INSERT OR REPLACE INTO trade_results 
                (cache_key, trade_id, trade_date, option_type, strike, handelsende_preis, 
                 peak_preis, peak_zeit, api_link, created_at, last_accessed, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
            """, (cache_key, trade_id, trade_date, option_type, strike, handelsende_preis, 
                  peak_preis, peak_zeit, api_link))
            
            conn.commit()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über den Cache zurück"""
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            
            # Gesamtanzahl Einträge
            cursor.execute("SELECT COUNT(*) FROM trade_results")
            total_entries = cursor.fetchone()[0]
            
            # Einträge der letzten 30 Tage
            cursor.execute("""
                SELECT COUNT(*) FROM trade_results 
                WHERE created_at > datetime('now', '-30 days')
            """)
            recent_entries = cursor.fetchone()[0]
            
            # Cache-Größe (ungefähre Schätzung)
            cursor.execute("SELECT COUNT(*) * 200 FROM trade_results")  # ~200 Bytes pro Eintrag
            total_size_bytes = cursor.fetchone()[0] or 0
            total_size_kb = total_size_bytes / 1024
            
            # Meist genutzte Einträge
            cursor.execute("""
                SELECT trade_date, option_type, strike, access_count 
                FROM trade_results 
                ORDER BY access_count DESC 
                LIMIT 5
            """)
            top_entries = cursor.fetchall()
            
            return {
                'total_entries': total_entries,
                'recent_entries': recent_entries,
                'total_size_kb': round(total_size_kb, 2),
                'top_entries': top_entries
            }
    
    def clear_old_cache(self, days: int = 60):
        """Bereinigt alte Cache-Einträge"""
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM trade_results 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count
    
    def clear_all_cache(self):
        """Löscht alle Cache-Einträge"""
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trade_results")
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count

def get_trade_results_cache() -> TradeResultsCache:
    """Gibt eine Instanz des Trade-Results-Caches zurück"""
    return TradeResultsCache()
