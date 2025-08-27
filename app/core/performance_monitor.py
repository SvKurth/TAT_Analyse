"""
Performance Monitor für das Trade Analyse Tool
Überwacht und misst die Performance von Funktionen und Services.
"""

import time
import functools
import threading
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta
from app.core.logging_service import get_logger


@dataclass
class PerformanceMetric:
    """Einzelne Performance-Metrik."""
    function_name: str
    execution_time: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class FunctionStats:
    """Statistiken für eine einzelne Funktion."""
    function_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    recent_execution_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def success_rate(self) -> float:
        """Gibt die Erfolgsrate zurück."""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    @property
    def failure_rate(self) -> float:
        """Gibt die Fehlerrate zurück."""
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls
    
    def add_metric(self, metric: PerformanceMetric) -> None:
        """Fügt eine neue Metrik hinzu."""
        self.total_calls += 1
        self.total_execution_time += metric.execution_time
        
        if metric.success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        
        # Aktualisiere Min/Max
        if metric.execution_time < self.min_execution_time:
            self.min_execution_time = metric.execution_time
        if metric.execution_time > self.max_execution_time:
            self.max_execution_time = metric.execution_time
        
        # Aktualisiere Durchschnitt
        self.avg_execution_time = self.total_execution_time / self.total_calls
        
        # Füge zur Liste der letzten Ausführungszeiten hinzu
        self.recent_execution_times.append(metric.execution_time)
    
    def get_recent_avg(self, count: int = 10) -> float:
        """Gibt den Durchschnitt der letzten N Ausführungen zurück."""
        if not self.recent_execution_times:
            return 0.0
        
        recent_times = list(self.recent_execution_times)[-count:]
        return sum(recent_times) / len(recent_times)


class PerformanceMonitor:
    """
    Zentrale Performance-Überwachung.
    
    Features:
    - Automatische Performance-Messung mit Decorators
    - Detaillierte Statistiken pro Funktion
    - Performance-Alerts bei Schwellenwerten
    - Export von Performance-Daten
    """
    
    def __init__(
        self,
        enable_alerts: bool = True,
        slow_function_threshold: float = 1.0,  # Sekunden
        max_metrics_per_function: int = 1000,
        enable_logging: bool = True
    ):
        """
        Initialisiert den Performance Monitor.
        
        Args:
            enable_alerts: Aktiviert Performance-Alerts
            slow_function_threshold: Schwellenwert für langsame Funktionen
            max_metrics_per_function: Maximale Anzahl Metriken pro Funktion
            enable_logging: Aktiviert Performance-Logging
        """
        self.enable_alerts = enable_alerts
        self.slow_function_threshold = slow_function_threshold
        self.max_metrics_per_function = max_metrics_per_function
        self.enable_logging = enable_logging
        
        self._stats: Dict[str, FunctionStats] = defaultdict(FunctionStats)
        self._metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self._lock = threading.RLock()
        self._logger = get_logger(__name__)
        
        # Performance-Alerts
        self._alert_callbacks: List[Callable] = []
    
    def monitor_function(
        self,
        slow_threshold: Optional[float] = None,
        context_provider: Optional[Callable] = None,
        log_slow_calls: bool = True
    ):
        """
        Decorator für Performance-Monitoring.
        
        Args:
            slow_threshold: Individueller Schwellenwert für diese Funktion
            context_provider: Funktion die zusätzlichen Kontext liefert
            log_slow_calls: Loggt langsame Aufrufe
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                success = False
                error_message = None
                context = None
                
                try:
                    # Sammle Kontext falls verfügbar
                    if context_provider:
                        try:
                            context = context_provider(*args, **kwargs)
                        except Exception as e:
                            self._logger.warning(f"Fehler beim Sammeln des Kontexts: {e}")
                    
                    # Führe Funktion aus
                    result = func(*args, **kwargs)
                    success = True
                    return result
                
                except Exception as e:
                    error_message = str(e)
                    raise
                
                finally:
                    # Messung beenden
                    execution_time = time.time() - start_time
                    
                    # Metrik erstellen
                    metric = PerformanceMetric(
                        function_name=func.__name__,
                        execution_time=execution_time,
                        timestamp=datetime.now(),
                        success=success,
                        error_message=error_message,
                        context=context
                    )
                    
                    # Metrik hinzufügen
                    self._add_metric(metric)
                    
                    # Performance-Alerts
                    threshold = slow_threshold or self.slow_function_threshold
                    if execution_time > threshold:
                        self._handle_slow_function(metric, threshold)
                        
                        if log_slow_calls:
                            self._logger.warning(
                                f"Langsame Funktion: {func.__name__} "
                                f"({execution_time:.4f}s > {threshold:.4f}s)"
                            )
            
            return wrapper
        return decorator
    
    def _add_metric(self, metric: PerformanceMetric) -> None:
        """Fügt eine neue Metrik hinzu."""
        with self._lock:
            function_name = metric.function_name
            
            # Aktualisiere Statistiken
            if function_name not in self._stats:
                self._stats[function_name] = FunctionStats(function_name=function_name)
            
            self._stats[function_name].add_metric(metric)
            
            # Füge Metrik hinzu
            self._metrics[function_name].append(metric)
            
            # Begrenze Anzahl der Metriken
            if len(self._metrics[function_name]) > self.max_metrics_per_function:
                self._metrics[function_name] = self._metrics[function_name][-self.max_metrics_per_function:]
    
    def _handle_slow_function(self, metric: PerformanceMetric, threshold: float) -> None:
        """Behandelt langsame Funktionen."""
        if not self.enable_alerts:
            return
        
        # Führe Alert-Callbacks aus
        for callback in self._alert_callbacks:
            try:
                callback(metric, threshold)
            except Exception as e:
                self._logger.error(f"Fehler in Alert-Callback: {e}")
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Fügt einen Alert-Callback hinzu."""
        self._alert_callbacks.append(callback)
    
    def get_function_stats(self, function_name: str) -> Optional[FunctionStats]:
        """Gibt Statistiken für eine Funktion zurück."""
        with self._lock:
            return self._stats.get(function_name)
    
    def get_all_stats(self) -> Dict[str, FunctionStats]:
        """Gibt alle Funktionsstatistiken zurück."""
        with self._lock:
            return dict(self._stats)
    
    def get_slow_functions(self, threshold: Optional[float] = None) -> List[FunctionStats]:
        """Gibt alle Funktionen zurück, die langsamer als der Schwellenwert sind."""
        threshold = threshold or self.slow_function_threshold
        
        with self._lock:
            slow_functions = [
                stats for stats in self._stats.values()
                if stats.avg_execution_time > threshold
            ]
            
            # Sortiere nach durchschnittlicher Ausführungszeit (langsamste zuerst)
            slow_functions.sort(key=lambda x: x.avg_execution_time, reverse=True)
            
            return slow_functions
    
    def get_top_functions(self, count: int = 10, by: str = "avg_time") -> List[FunctionStats]:
        """
        Gibt die Top-Funktionen zurück.
        
        Args:
            count: Anzahl der zurückzugebenden Funktionen
            by: Sortierung nach ('avg_time', 'total_calls', 'success_rate')
        """
        with self._lock:
            all_stats = list(self._stats.values())
            
            if by == "avg_time":
                all_stats.sort(key=lambda x: x.avg_execution_time, reverse=True)
            elif by == "total_calls":
                all_stats.sort(key=lambda x: x.total_calls, reverse=True)
            elif by == "success_rate":
                all_stats.sort(key=lambda x: x.success_rate, reverse=True)
            else:
                raise ValueError(f"Unbekannte Sortierung: {by}")
            
            return all_stats[:count]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung aller Performance-Daten zurück."""
        with self._lock:
            total_functions = len(self._stats)
            total_calls = sum(stats.total_calls for stats in self._stats.values())
            total_execution_time = sum(stats.total_execution_time for stats in self._stats.values())
            
            if total_calls > 0:
                overall_avg_time = total_execution_time / total_calls
            else:
                overall_avg_time = 0.0
            
            slow_functions = self.get_slow_functions()
            
            return {
                'total_functions': total_functions,
                'total_calls': total_calls,
                'overall_avg_execution_time': overall_avg_time,
                'slow_functions_count': len(slow_functions),
                'functions_with_errors': sum(1 for stats in self._stats.values() if stats.failed_calls > 0),
                'overall_success_rate': sum(stats.successful_calls for stats in self._stats.values()) / max(total_calls, 1)
            }
    
    def reset_stats(self, function_name: Optional[str] = None) -> None:
        """Setzt Statistiken zurück."""
        with self._lock:
            if function_name:
                if function_name in self._stats:
                    self._stats[function_name] = FunctionStats(function_name=function_name)
                if function_name in self._metrics:
                    self._metrics[function_name].clear()
                self._logger.info(f"Statistiken für Funktion '{function_name}' zurückgesetzt")
            else:
                self._stats.clear()
                self._metrics.clear()
                self._logger.info("Alle Performance-Statistiken zurückgesetzt")
    
    def export_metrics(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """Exportiert Metriken für Analyse."""
        with self._lock:
            if function_name:
                if function_name not in self._metrics:
                    return {}
                
                return {
                    'function_name': function_name,
                    'metrics': [
                        {
                            'timestamp': metric.timestamp.isoformat(),
                            'execution_time': metric.execution_time,
                            'success': metric.success,
                            'error_message': metric.error_message,
                            'context': metric.context
                        }
                        for metric in self._metrics[function_name]
                    ]
                }
            else:
                return {
                    'export_timestamp': datetime.now().isoformat(),
                    'functions': {
                        name: [
                            {
                                'timestamp': metric.timestamp.isoformat(),
                                'execution_time': metric.execution_time,
                                'success': metric.success,
                                'error_message': metric.error_message,
                                'context': metric.context
                            }
                            for metric in metrics
                        ]
                        for name, metrics in self._metrics.items()
                    }
                }


# Globale Performance Monitor Instanz
_performance_monitor = None
_performance_monitor_lock = threading.Lock()

def get_performance_monitor() -> PerformanceMonitor:
    """Gibt den globalen Performance Monitor zurück."""
    global _performance_monitor
    
    if _performance_monitor is None:
        with _performance_monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = PerformanceMonitor()
    
    return _performance_monitor

def monitor_function(
    slow_threshold: Optional[float] = None,
    context_provider: Optional[Callable] = None,
    log_slow_calls: bool = True
):
    """Globaler Decorator für Performance-Monitoring."""
    return get_performance_monitor().monitor_function(
        slow_threshold=slow_threshold,
        context_provider=context_provider,
        log_slow_calls=log_slow_calls
    )

def get_function_stats(function_name: str) -> Optional[FunctionStats]:
    """Gibt Statistiken für eine Funktion zurück."""
    return get_performance_monitor().get_function_stats(function_name)

def get_performance_summary() -> Dict[str, Any]:
    """Gibt eine Performance-Zusammenfassung zurück."""
    return get_performance_monitor().get_performance_summary()

def reset_performance_stats(function_name: Optional[str] = None) -> None:
    """Setzt Performance-Statistiken zurück."""
    get_performance_monitor().reset_stats(function_name)
