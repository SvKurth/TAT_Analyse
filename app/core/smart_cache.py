"""
Smart Cache System für das Trade Analyse Tool
Intelligentes Caching mit TTL, LRU-Eviction und Performance-Monitoring.
"""

import time
import threading
from typing import Dict, Any, Optional, Callable, Tuple, Union
from collections import OrderedDict
from dataclasses import dataclass, field
from app.core.logging_service import get_logger


@dataclass
class CacheItem:
    """Einzelner Cache-Eintrag mit Metadaten."""
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Prüft ob der Cache-Eintrag abgelaufen ist."""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)
    
    def touch(self) -> None:
        """Aktualisiert den letzten Zugriff."""
        self.last_accessed = time.time()
        self.access_count += 1


class CacheStats:
    """Statistiken für den Cache."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0
        self.total_requests = 0
    
    @property
    def hit_rate(self) -> float:
        """Gibt die Hit-Rate zurück."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    def record_hit(self) -> None:
        """Zeichnet einen Cache-Hit auf."""
        self.hits += 1
        self.total_requests += 1
    
    def record_miss(self) -> None:
        """Zeichnet einen Cache-Miss auf."""
        self.misses += 1
        self.total_requests += 1
    
    def record_eviction(self) -> None:
        """Zeichnet eine Cache-Eviction auf."""
        self.evictions += 1
    
    def record_expiration(self) -> None:
        """Zeichnet eine Cache-Expiration auf."""
        self.expirations += 1
    
    def reset(self) -> None:
        """Setzt alle Statistiken zurück."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0
        self.total_requests = 0


class SmartCache:
    """
    Intelligenter Cache mit TTL, LRU-Eviction und Performance-Monitoring.
    
    Features:
    - Time-To-Live (TTL) für automatische Expiration
    - LRU-Eviction bei Speicherüberlauf
    - Performance-Statistiken
    - Thread-Sicherheit
    - Konfigurierbare Eviction-Strategien
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = 300,  # 5 Minuten
        eviction_policy: str = "lru",  # lru, lfu, fifo
        enable_stats: bool = True,
        cleanup_interval: float = 60.0  # Sekunden
    ):
        """
        Initialisiert den SmartCache.
        
        Args:
            max_size: Maximale Anzahl der Cache-Einträge
            default_ttl: Standard-TTL in Sekunden (None = kein TTL)
            eviction_policy: Eviction-Strategie (lru, lfu, fifo)
            enable_stats: Aktiviert Performance-Statistiken
            cleanup_interval: Intervall für automatische Bereinigung
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.eviction_policy = eviction_policy
        self.enable_stats = enable_stats
        self.cleanup_interval = cleanup_interval
        
        self._cache: OrderedDict[str, CacheItem] = OrderedDict()
        self._lock = threading.RLock()
        self._logger = get_logger(__name__)
        self._stats = CacheStats() if enable_stats else None
        
        # Starte Cleanup-Thread
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self) -> None:
        """Startet den Cleanup-Thread."""
        if self.cleanup_interval > 0:
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_worker,
                daemon=True,
                name="SmartCache-Cleanup"
            )
            self._cleanup_thread.start()
    
    def _cleanup_worker(self) -> None:
        """Cleanup-Worker-Thread für abgelaufene Einträge."""
        while not self._stop_cleanup.wait(self.cleanup_interval):
            try:
                self._cleanup_expired()
            except Exception as e:
                self._logger.error(f"Fehler im Cleanup-Thread: {e}")
    
    def _cleanup_expired(self) -> None:
        """Entfernt abgelaufene Cache-Einträge."""
        with self._lock:
            expired_keys = [
                key for key, item in self._cache.items()
                if item.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                if self._stats:
                    self._stats.record_expiration()
            
            if expired_keys:
                self._logger.debug(f"{len(expired_keys)} abgelaufene Cache-Einträge entfernt")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Gibt einen Wert aus dem Cache zurück.
        
        Args:
            key: Cache-Schlüssel
            default: Standardwert bei Cache-Miss
            
        Returns:
            Gecachter Wert oder Standardwert
        """
        with self._lock:
            if key in self._cache:
                item = self._cache[key]
                
                # Prüfe TTL
                if item.is_expired():
                    del self._cache[key]
                    if self._stats:
                        self._stats.record_expiration()
                        self._stats.record_miss()
                    return default
                
                # Aktualisiere Zugriffsstatistiken
                item.touch()
                
                # LRU: Bewege an das Ende
                self._cache.move_to_end(key)
                
                if self._stats:
                    self._stats.record_hit()
                
                return item.value
            
            if self._stats:
                self._stats.record_miss()
            
            return default
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        force: bool = False
    ) -> None:
        """
        Speichert einen Wert im Cache.
        
        Args:
            key: Cache-Schlüssel
            value: Zu cachender Wert
            ttl: TTL in Sekunden (None = Standard-TTL)
            force: Überschreibt existierende Einträge
        """
        with self._lock:
            # Prüfe ob Key bereits existiert
            if key in self._cache and not force:
                self._logger.debug(f"Key '{key}' bereits im Cache, überspringe (force=False)")
                return
            
            # Entferne alten Eintrag falls vorhanden
            if key in self._cache:
                del self._cache[key]
            
            # Prüfe Cache-Größe
            if len(self._cache) >= self.max_size:
                self._evict_item()
            
            # Erstelle neuen Cache-Eintrag
            cache_ttl = ttl if ttl is not None else self.default_ttl
            item = CacheItem(value=value, ttl=cache_ttl)
            
            # Füge hinzu (LRU: am Ende)
            self._cache[key] = item
            
            self._logger.debug(f"Key '{key}' im Cache gespeichert (TTL: {cache_ttl}s)")
    
    def _evict_item(self) -> None:
        """Entfernt einen Eintrag basierend auf der Eviction-Strategie."""
        if not self._cache:
            return
        
        if self.eviction_policy == "lru":
            # LRU: Entferne den ältesten (am wenigsten kürzlich verwendeten)
            key_to_evict = next(iter(self._cache))
        elif self.eviction_policy == "lfu":
            # LFU: Entferne den am wenigsten häufig verwendeten
            key_to_evict = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].access_count
            )
        elif self.eviction_policy == "fifo":
            # FIFO: Entferne den ältesten (ersten)
            key_to_evict = next(iter(self._cache))
        else:
            # Fallback: LRU
            key_to_evict = next(iter(self._cache))
        
        del self._cache[key_to_evict]
        if self._stats:
            self._stats.record_eviction()
        
        self._logger.debug(f"Cache-Eintrag '{key_to_evict}' evicted ({self.eviction_policy})")
    
    def delete(self, key: str) -> bool:
        """
        Löscht einen Cache-Eintrag.
        
        Args:
            key: Cache-Schlüssel
            
        Returns:
            True wenn der Eintrag gelöscht wurde
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._logger.debug(f"Key '{key}' aus dem Cache gelöscht")
                return True
            return False
    
    def clear(self) -> None:
        """Löscht alle Cache-Einträge."""
        with self._lock:
            self._cache.clear()
            if self._stats:
                self._stats.reset()
            self._logger.info("Cache geleert")
    
    def exists(self, key: str) -> bool:
        """Prüft ob ein Key im Cache existiert (ohne TTL zu prüfen)."""
        with self._lock:
            return key in self._cache
    
    def size(self) -> int:
        """Gibt die aktuelle Cache-Größe zurück."""
        with self._lock:
            return len(self._cache)
    
    def keys(self) -> list:
        """Gibt alle Cache-Schlüssel zurück."""
        with self._lock:
            return list(self._cache.keys())
    
    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Gibt Cache-Statistiken zurück."""
        if not self._stats:
            return None
        
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': self._stats.hit_rate,
                'hits': self._stats.hits,
                'misses': self._stats.misses,
                'evictions': self._stats.evictions,
                'expirations': self._stats.expirations,
                'total_requests': self._stats.total_requests
            }
    
    def reset_stats(self) -> None:
        """Setzt alle Statistiken zurück."""
        if self._stats:
            with self._lock:
                self._stats.reset()
    
    def close(self) -> None:
        """Beendet den Cache und alle Threads."""
        self._stop_cleanup.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5.0)
        self.clear()
        self._logger.info("Cache geschlossen")
    
    def __enter__(self):
        """Context Manager Entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Exit."""
        self.close()


class CacheManager:
    """
    Manager für mehrere Cache-Instanzen.
    
    Ermöglicht die Verwaltung verschiedener Cache-Typen
    (z.B. API-Cache, Trade-Cache, etc.)
    """
    
    def __init__(self):
        self._caches: Dict[str, SmartCache] = {}
        self._lock = threading.Lock()
        self._logger = get_logger(__name__)
    
    def create_cache(
        self,
        name: str,
        max_size: int = 1000,
        default_ttl: Optional[float] = 300,
        eviction_policy: str = "lru",
        enable_stats: bool = True
    ) -> SmartCache:
        """
        Erstellt einen neuen Cache.
        
        Args:
            name: Name des Caches
            max_size: Maximale Cache-Größe
            default_ttl: Standard-TTL
            eviction_policy: Eviction-Strategie
            enable_stats: Aktiviert Statistiken
            
        Returns:
            Erstellter Cache
            
        Raises:
            ValueError: Wenn der Cache-Name bereits existiert
        """
        with self._lock:
            if name in self._caches:
                raise ValueError(f"Cache '{name}' existiert bereits")
            
            cache = SmartCache(
                max_size=max_size,
                default_ttl=default_ttl,
                eviction_policy=eviction_policy,
                enable_stats=enable_stats
            )
            
            self._caches[name] = cache
            self._logger.info(f"Cache '{name}' erstellt")
            
            return cache
    
    def get_cache(self, name: str) -> Optional[SmartCache]:
        """Gibt einen Cache zurück."""
        with self._lock:
            return self._caches.get(name)
    
    def remove_cache(self, name: str) -> bool:
        """Entfernt einen Cache."""
        with self._lock:
            if name in self._caches:
                cache = self._caches[name]
                cache.close()
                del self._caches[name]
                self._logger.info(f"Cache '{name}' entfernt")
                return True
            return False
    
    def list_caches(self) -> list:
        """Gibt alle Cache-Namen zurück."""
        with self._lock:
            return list(self._caches.keys())
    
    def close_all(self) -> None:
        """Schließt alle Caches."""
        with self._lock:
            for name, cache in self._caches.items():
                try:
                    cache.close()
                except Exception as e:
                    self._logger.error(f"Fehler beim Schließen des Caches '{name}': {e}")
            
            self._caches.clear()
            self._logger.info("Alle Caches geschlossen")


# Globale Cache-Instanzen
_cache_manager = CacheManager()

def get_cache_manager() -> CacheManager:
    """Gibt den globalen Cache-Manager zurück."""
    return _cache_manager

def get_cache(name: str) -> Optional[SmartCache]:
    """Gibt einen Cache aus dem globalen Manager zurück."""
    return _cache_manager.get_cache(name)

def create_cache(
    name: str,
    max_size: int = 1000,
    default_ttl: Optional[float] = 300,
    eviction_policy: str = "lru",
    enable_stats: bool = True
) -> SmartCache:
    """Erstellt einen neuen Cache im globalen Manager."""
    return _cache_manager.create_cache(
        name, max_size, default_ttl, eviction_policy, enable_stats
    )
