"""
Database Connection Pool für das Trade Analyse Tool
Verwaltet Datenbankverbindungen effizient mit Pooling und Prepared Statements.
"""

import sqlite3
import threading
import time
from typing import Dict, Any, Optional, List, Tuple, Callable
from contextlib import contextmanager
from queue import Queue, Empty
from dataclasses import dataclass, field
from app.core.logging_service import get_logger
from app.core.performance_monitor import monitor_function


@dataclass
class ConnectionConfig:
    """Konfiguration für Datenbankverbindungen."""
    max_connections: int = 10
    timeout: float = 30.0
    check_same_thread: bool = False
    enable_wal: bool = True
    cache_size: int = 10000
    synchronous: str = "NORMAL"
    journal_mode: str = "WAL"
    temp_store: str = "MEMORY"
    mmap_size: int = 268435456  # 256MB


@dataclass
class ConnectionStats:
    """Statistiken für Connection Pool."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    connection_errors: int = 0
    total_queries: int = 0
    slow_queries: int = 0
    slow_query_threshold: float = 1.0  # Sekunden


class DatabaseConnection:
    """Einzelne Datenbankverbindung mit Metadaten."""
    
    def __init__(self, connection: sqlite3.Connection, db_path: str):
        self.connection = connection
        self.db_path = db_path
        self.created_at = time.time()
        self.last_used = time.time()
        self.query_count = 0
        self.is_active = False
        
        # SQLite-Optimierungen
        self._optimize_connection()
    
    def _optimize_connection(self) -> None:
        """Optimiert die SQLite-Verbindung für bessere Performance."""
        try:
            cursor = self.connection.cursor()
            
            # WAL-Modus für bessere Performance
            cursor.execute(f"PRAGMA journal_mode={self.connection.journal_mode}")
            
            # Cache-Größe
            cursor.execute(f"PRAGMA cache_size={self.connection.cache_size}")
            
            # Synchronisation
            cursor.execute(f"PRAGMA synchronous={self.connection.synchronous}")
            
            # Temporärer Speicher
            cursor.execute(f"PRAGMA temp_store={self.connection.temp_store}")
            
            # MMAP für bessere Performance bei großen Datenbanken
            cursor.execute(f"PRAGMA mmap_size={self.connection.mmap_size}")
            
            # Foreign Keys aktivieren
            cursor.execute("PRAGMA foreign_keys=ON")
            
            # Optimierungen für bessere Performance
            cursor.execute("PRAGMA optimize")
            
        except Exception as e:
            # Logge Fehler, aber fahre fort
            logger = get_logger(__name__)
            logger.warning(f"Fehler beim Optimieren der Verbindung: {e}")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> sqlite3.Cursor:
        """Führt eine SQL-Query aus."""
        start_time = time.time()
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            execution_time = time.time() - start_time
            
            # Aktualisiere Statistiken
            self.query_count += 1
            self.last_used = time.time()
            
            # Logge langsame Queries
            if execution_time > 1.0:
                logger = get_logger(__name__)
                logger.warning(f"Langsame Query ({execution_time:.4f}s): {query[:100]}...")
            
            return cursor
            
        except Exception as e:
            # Logge Fehler
            logger = get_logger(__name__)
            logger.error(f"Fehler bei Query '{query[:100]}...': {e}")
            raise
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Führt mehrere SQL-Queries aus."""
        start_time = time.time()
        
        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, params_list)
            
            execution_time = time.time() - start_time
            
            # Aktualisiere Statistiken
            self.query_count += 1
            self.last_used = time.time()
            
            # Logge langsame Queries
            if execution_time > 1.0:
                logger = get_logger(__name__)
                logger.warning(f"Langsame Batch-Query ({execution_time:.4f}s): {len(params_list)} Queries")
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Fehler bei Batch-Query '{query[:100]}...': {e}")
            raise
    
    def commit(self) -> None:
        """Führt einen Commit aus."""
        self.connection.commit()
        self.last_used = time.time()
    
    def rollback(self) -> None:
        """Führt einen Rollback aus."""
        self.connection.rollback()
        self.last_used = time.time()
    
    def close(self) -> None:
        """Schließt die Verbindung."""
        if self.connection:
            self.connection.close()
    
    def is_valid(self) -> bool:
        """Prüft ob die Verbindung noch gültig ist."""
        try:
            # Einfache Test-Query
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except Exception:
            return False


class ConnectionPool:
    """
    Pool für Datenbankverbindungen.
    
    Features:
    - Automatisches Connection Pooling
    - Prepared Statements
    - Connection-Validierung
    - Performance-Monitoring
    - Automatische Cleanup
    """
    
    def __init__(self, db_path: str, config: ConnectionConfig):
        """
        Initialisiert den Connection Pool.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            config: Verbindungskonfiguration
        """
        self.db_path = db_path
        self.config = config
        self.logger = get_logger(__name__)
        
        # Connection Pool
        self._pool: Queue[DatabaseConnection] = Queue(maxsize=config.max_connections)
        self._active_connections: List[DatabaseConnection] = []
        self._lock = threading.RLock()
        
        # Statistiken
        self._stats = ConnectionStats()
        self._stats.slow_query_threshold = config.timeout
        
        # Prepared Statements Cache
        self._prepared_statements: Dict[str, sqlite3.Connection] = {}
        
        # Cleanup-Thread
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()
        
        # Initialisiere Pool
        self._initialize_pool()
    
    def _start_cleanup_thread(self) -> None:
        """Startet den Cleanup-Thread."""
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True,
            name=f"ConnectionPool-Cleanup-{self.db_path}"
        )
        self._cleanup_thread.start()
    
    def _cleanup_worker(self) -> None:
        """Cleanup-Worker für inaktive Verbindungen."""
        while not self._stop_cleanup.wait(60.0):  # Alle 60 Sekunden
            try:
                self._cleanup_idle_connections()
            except Exception as e:
                self.logger.error(f"Fehler im Cleanup-Thread: {e}")
    
    def _cleanup_idle_connections(self) -> None:
        """Entfernt inaktive Verbindungen."""
        with self._lock:
            current_time = time.time()
            idle_timeout = 300.0  # 5 Minuten
            
            # Prüfe aktive Verbindungen
            active_connections = []
            for conn in self._active_connections:
                if current_time - conn.last_used > idle_timeout:
                    # Verbindung war lange inaktiv, schließe sie
                    try:
                        conn.close()
                        self._stats.active_connections -= 1
                        self.logger.debug(f"Inaktive Verbindung geschlossen: {conn.db_path}")
                    except Exception as e:
                        self.logger.error(f"Fehler beim Schließen der Verbindung: {e}")
                else:
                    active_connections.append(conn)
            
            self._active_connections = active_connections
    
    def _initialize_pool(self) -> None:
        """Initialisiert den Connection Pool."""
        try:
            # Erstelle initiale Verbindungen
            for _ in range(min(3, self.config.max_connections)):
                connection = self._create_connection()
                if connection:
                    self._pool.put(connection)
                    self._stats.total_connections += 1
                    self._stats.idle_connections += 1
            
            self.logger.info(f"Connection Pool für {self.db_path} initialisiert")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren des Connection Pools: {e}")
    
    def _create_connection(self) -> Optional[DatabaseConnection]:
        """Erstellt eine neue Datenbankverbindung."""
        try:
            connection = sqlite3.connect(
                self.db_path,
                timeout=self.config.timeout,
                check_same_thread=self.config.check_same_thread
            )
            
            # Erstelle DatabaseConnection-Objekt
            db_connection = DatabaseConnection(connection, self.db_path)
            
            return db_connection
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Verbindung: {e}")
            self._stats.connection_errors += 1
            return None
    
    @contextmanager
    def get_connection(self, timeout: Optional[float] = None):
        """
        Kontextmanager für Datenbankverbindungen.
        
        Args:
            timeout: Timeout für das Warten auf eine Verbindung
            
        Yields:
            DatabaseConnection-Objekt
        """
        connection = None
        try:
            connection = self._get_connection(timeout)
            if connection:
                yield connection
            else:
                raise Exception("Keine Verbindung verfügbar")
        finally:
            if connection:
                self._return_connection(connection)
    
    def _get_connection(self, timeout: Optional[float] = None) -> Optional[DatabaseConnection]:
        """Holt eine Verbindung aus dem Pool."""
        timeout = timeout or self.config.timeout
        
        try:
            # Versuche Verbindung aus dem Pool zu holen
            connection = self._pool.get(timeout=timeout)
            
            with self._lock:
                self._stats.idle_connections -= 1
                self._stats.active_connections += 1
                connection.is_active = True
                self._active_connections.append(connection)
            
            return connection
            
        except Empty:
            # Pool ist leer, erstelle neue Verbindung
            if len(self._active_connections) < self.config.max_connections:
                connection = self._create_connection()
                if connection:
                    with self._lock:
                        self._stats.total_connections += 1
                        self._stats.active_connections += 1
                        connection.is_active = True
                        self._active_connections.append(connection)
                    
                    return connection
            
            # Keine Verbindung verfügbar
            self.logger.warning("Keine Datenbankverbindung verfügbar")
            return None
    
    def _return_connection(self, connection: DatabaseConnection) -> None:
        """Gibt eine Verbindung an den Pool zurück."""
        with self._lock:
            if connection in self._active_connections:
                self._active_connections.remove(connection)
                self._stats.active_connections -= 1
                connection.is_active = False
                
                # Prüfe ob Verbindung noch gültig ist
                if connection.is_valid():
                    try:
                        self._pool.put(connection, timeout=1.0)
                        self._stats.idle_connections += 1
                    except Exception:
                        # Pool ist voll, schließe Verbindung
                        connection.close()
                        self._stats.total_connections -= 1
                else:
                    # Ungültige Verbindung, schließe sie
                    connection.close()
                    self._stats.total_connections -= 1
    
    @monitor_function(slow_threshold=0.5)
    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> Any:
        """
        Führt eine SQL-Query aus.
        
        Args:
            query: SQL-Query
            params: Query-Parameter
            fetch: Ob das Ergebnis geholt werden soll
            
        Returns:
            Query-Ergebnis
        """
        with self.get_connection() as connection:
            cursor = connection.execute_query(query, params)
            
            if fetch:
                return cursor.fetchall()
            else:
                return cursor
    
    @monitor_function(slow_threshold=1.0)
    def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Führt mehrere SQL-Queries aus."""
        with self.get_connection() as connection:
            connection.execute_many(query, params_list)
            connection.commit()
    
    def get_table_info(self) -> Dict[str, Any]:
        """Gibt Informationen über die Datenbank zurück."""
        with self.get_connection() as connection:
            cursor = connection.execute_query("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            table_info = {}
            for (table_name,) in tables:
                cursor = connection.execute_query(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                table_info[table_name] = columns
            
            return table_info
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Pool-Statistiken zurück."""
        with self._lock:
            return {
                'db_path': self.db_path,
                'total_connections': self._stats.total_connections,
                'active_connections': self._stats.active_connections,
                'idle_connections': self._stats.idle_connections,
                'connection_errors': self._stats.connection_errors,
                'total_queries': self._stats.total_queries,
                'slow_queries': self._stats.slow_queries,
                'pool_size': self._pool.qsize(),
                'max_connections': self.config.max_connections
            }
    
    def close(self) -> None:
        """Schließt den Connection Pool."""
        self._stop_cleanup.set()
        
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5.0)
        
        with self._lock:
            # Schließe alle aktiven Verbindungen
            for connection in self._active_connections:
                try:
                    connection.close()
                except Exception as e:
                    self.logger.error(f"Fehler beim Schließen der Verbindung: {e}")
            
            # Schließe alle Verbindungen im Pool
            while not self._pool.empty():
                try:
                    connection = self._pool.get_nowait()
                    connection.close()
                except Empty:
                    break
                except Exception as e:
                    self.logger.error(f"Fehler beim Schließen der Pool-Verbindung: {e}")
            
            self._active_connections.clear()
            self._stats.active_connections = 0
            self._stats.idle_connections = 0
        
        self.logger.info(f"Connection Pool für {self.db_path} geschlossen")
    
    def __enter__(self):
        """Context Manager Entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Exit."""
        self.close()


class ConnectionPoolManager:
    """Manager für mehrere Connection Pools."""
    
    def __init__(self):
        self._pools: Dict[str, ConnectionPool] = {}
        self._lock = threading.Lock()
        self._logger = get_logger(__name__)
    
    def create_pool(
        self,
        db_path: str,
        config: Optional[ConnectionConfig] = None
    ) -> ConnectionPool:
        """
        Erstellt einen neuen Connection Pool.
        
        Args:
            db_path: Pfad zur Datenbank
            config: Verbindungskonfiguration
            
        Returns:
            Erstellter Connection Pool
        """
        if config is None:
            config = ConnectionConfig()
        
        with self._lock:
            if db_path in self._pools:
                raise ValueError(f"Connection Pool für {db_path} existiert bereits")
            
            pool = ConnectionPool(db_path, config)
            self._pools[db_path] = pool
            
            self._logger.info(f"Connection Pool für {db_path} erstellt")
            
            return pool
    
    def get_pool(self, db_path: str) -> Optional[ConnectionPool]:
        """Gibt einen Connection Pool zurück."""
        with self._lock:
            return self._pools.get(db_path)
    
    def remove_pool(self, db_path: str) -> bool:
        """Entfernt einen Connection Pool."""
        with self._lock:
            if db_path in self._pools:
                pool = self._pools[db_path]
                pool.close()
                del self._pools[db_path]
                self._logger.info(f"Connection Pool für {db_path} entfernt")
                return True
            return False
    
    def list_pools(self) -> List[str]:
        """Gibt alle Pool-Pfade zurück."""
        with self._lock:
            return list(self._pools.keys())
    
    def close_all(self) -> None:
        """Schließt alle Connection Pools."""
        with self._lock:
            for db_path, pool in self._pools.items():
                try:
                    pool.close()
                except Exception as e:
                    self._logger.error(f"Fehler beim Schließen des Pools {db_path}: {e}")
            
            self._pools.clear()
            self._logger.info("Alle Connection Pools geschlossen")


# Globale Connection Pool Manager Instanz
_connection_pool_manager = ConnectionPoolManager()

def get_connection_pool_manager() -> ConnectionPoolManager:
    """Gibt den globalen Connection Pool Manager zurück."""
    return _connection_pool_manager

def create_connection_pool(
    db_path: str,
    config: Optional[ConnectionConfig] = None
) -> ConnectionPool:
    """Erstellt einen neuen Connection Pool im globalen Manager."""
    return _connection_pool_manager.create_pool(db_path, config)

def get_connection_pool(db_path: str) -> Optional[ConnectionPool]:
    """Gibt einen Connection Pool aus dem globalen Manager zurück."""
    return _connection_pool_manager.get_pool(db_path)
