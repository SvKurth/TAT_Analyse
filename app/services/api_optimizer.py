"""
API-Optimizer Service für intelligentes Prefetching und Batch-Processing
Optimiert API-Calls für bessere Performance im Navigator
"""

import asyncio
import concurrent.futures
import threading
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from queue import Queue, PriorityQueue
import logging
from datetime import datetime, timedelta

# Performance-Monitoring temporär deaktiviert
from app.core.smart_cache import get_cache_manager
from app.core.logging_service import get_logger

@dataclass
class APIRequest:
    """Repräsentiert eine API-Anfrage"""
    priority: int  # Höhere Zahl = höhere Priorität
    trade_id: str
    asset: str
    date: str
    option_type: str
    strike: int
    created_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        # Für PriorityQueue: Höhere Priorität zuerst
        return self.priority > other.priority

@dataclass
class APIResponse:
    """Repräsentiert eine API-Antwort"""
    trade_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_time: Optional[float] = None
    cache_hit: bool = False

class APIOptimizer:
    """Intelligenter API-Optimizer mit Prefetching und Batch-Processing"""
    
    def __init__(self, max_workers: int = 5, batch_size: int = 10):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.logger = get_logger(__name__)
        self.smart_cache = get_cache_manager().get_cache("api_optimizer")
        
        # Request-Queue mit Prioritäten
        self.request_queue = PriorityQueue()
        self.response_queue = Queue()
        
        # Worker-Threads
        self.workers = []
        self.running = False
        
        # Statistiken
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'average_response_time': 0.0,
            'total_response_time': 0.0
        }
        
        # Cache für API-Funktionen
        self.api_functions = {}
        
        # Starte Worker-Threads
        self._start_workers()
    
    def _start_workers(self):
        """Startet die Worker-Threads"""
        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
            worker.start()
            self.workers.append(worker)
            self.logger.info(f"API-Optimizer Worker {i} gestartet")
    
    def _worker_loop(self, worker_id: int):
        """Hauptschleife für Worker-Threads"""
        while self.running:
            try:
                # Hole Request aus der Queue (mit Timeout)
                try:
                    request = self.request_queue.get(timeout=1.0)
                except:
                    continue
                
                # Verarbeite Request
                self._process_request(request, worker_id)
                
                # Markiere als erledigt
                self.request_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Worker {worker_id} Fehler: {e}")
                continue
    
    def _process_request(self, request: APIRequest, worker_id: int):
        """Verarbeitet eine einzelne API-Anfrage"""
        start_time = time.time()
        
        try:
            # Prüfe Cache zuerst
            cache_key = f"{request.asset}_{request.date}_{request.option_type}_{request.strike}"
            cached_data = self.smart_cache.get(cache_key)
            
            if cached_data:
                # Cache-Hit
                response = APIResponse(
                    trade_id=request.trade_id,
                    success=True,
                    data=cached_data,
                    response_time=time.time() - start_time,
                    cache_hit=True
                )
                self.stats['cache_hits'] += 1
            else:
                # API-Call durchführen
                api_function = self.api_functions.get('get_option_price_data')
                if api_function:
                    try:
                        api_data = api_function(
                            request.asset, 
                            request.date, 
                            request.option_type, 
                            request.strike
                        )
                        
                        if api_data:
                            # In Cache speichern
                            self.smart_cache.set(cache_key, api_data, ttl=3600)  # 1 Stunde
                            
                            response = APIResponse(
                                trade_id=request.trade_id,
                                success=True,
                                data=api_data,
                                response_time=time.time() - start_time,
                                cache_hit=False
                            )
                        else:
                            response = APIResponse(
                                trade_id=request.trade_id,
                                success=False,
                                error="Keine API-Daten erhalten",
                                response_time=time.time() - start_time
                            )
                    except Exception as api_error:
                        response = APIResponse(
                            trade_id=request.trade_id,
                            success=False,
                            error=f"API-Fehler: {str(api_error)}",
                            response_time=time.time() - start_time
                        )
                else:
                    response = APIResponse(
                        trade_id=request.trade_id,
                        success=False,
                        error="API-Funktion nicht registriert",
                        response_time=time.time() - start_time
                    )
            
            # Statistiken aktualisieren
            self._update_stats(response)
            
            # Response in Queue legen
            self.response_queue.put(response)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Request-Verarbeitung: {e}")
            response = APIResponse(
                trade_id=request.trade_id,
                success=False,
                error=f"Verarbeitungsfehler: {str(e)}",
                response_time=time.time() - start_time
            )
            self.response_queue.put(response)
    
    def _update_stats(self, response: APIResponse):
        """Aktualisiert die Statistiken"""
        self.stats['total_requests'] += 1
        
        if response.success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        if response.response_time:
            self.stats['total_response_time'] += response.response_time
            self.stats['average_response_time'] = (
                self.stats['total_response_time'] / self.stats['total_requests']
            )
    
    def register_api_function(self, name: str, function: Callable):
        """Registriert eine API-Funktion"""
        self.api_functions[name] = function
        self.logger.info(f"API-Funktion '{name}' registriert")
    
    def submit_request(self, trade_id: str, asset: str, date: str, option_type: str,
                      strike: int, priority: int = 1) -> str:
        """Reicht eine API-Anfrage ein"""
        request = APIRequest(
            priority=priority,
            trade_id=trade_id,
            asset=asset,
            date=date,
            option_type=option_type,
            strike=strike,
            created_at=datetime.now()
        )
        
        self.request_queue.put(request)
        return trade_id
    
    def submit_batch_requests(self, requests: List[Tuple[str, str, str, str, int]],
                             priority: int = 1) -> List[str]:
        """Reicht mehrere API-Anfragen als Batch ein"""
        trade_ids = []
        
        for trade_id, asset, date, option_type, strike in requests:
            trade_ids.append(
                self.submit_request(trade_id, asset, date, option_type, strike, priority)
            )
        
        return trade_ids
    
    def get_response(self, timeout: float = 1.0) -> Optional[APIResponse]:
        """Holt eine Antwort aus der Response-Queue"""
        try:
            return self.response_queue.get(timeout=timeout)
        except:
            return None
    
    def get_all_responses(self, timeout: float = 5.0) -> List[APIResponse]:
        """Holt alle verfügbaren Antworten"""
        responses = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = self.get_response(timeout=0.1)
            if response:
                responses.append(response)
            else:
                break
        
        return responses
    
    def wait_for_completion(self, timeout: float = 30.0) -> bool:
        """Wartet auf die Fertigstellung aller Requests"""
        try:
            return self.request_queue.join()
        except:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt aktuelle Statistiken zurück"""
        return self.stats.copy()
    
    def clear_stats(self):
        """Setzt Statistiken zurück"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'average_response_time': 0.0,
            'total_response_time': 0.0
        }
    
    def shutdown(self):
        """Beendet den API-Optimizer"""
        self.running = False
        
        # Warte auf Worker-Threads
        for worker in self.workers:
            worker.join(timeout=5.0)
        
        self.logger.info("API-Optimizer heruntergefahren")

class PrefetchManager:
    """Verwaltet das intelligente Prefetching von API-Daten"""
    
    def __init__(self, api_optimizer: APIOptimizer):
        self.api_optimizer = api_optimizer
        self.logger = get_logger(__name__)
        self.prefetch_queue = Queue()
        self.prefetch_thread = None
        self.running = False
        
        # Prefetch-Strategien
        self.prefetch_strategies = {
            'sequential': self._sequential_prefetch,
            'priority': self._priority_prefetch,
            'smart': self._smart_prefetch
        }
    
    def start_prefetching(self, strategy: str = 'smart'):
        """Startet das Prefetching mit der angegebenen Strategie"""
        if self.running:
            return
        
        self.running = True
        self.prefetch_thread = threading.Thread(
            target=self._prefetch_loop, 
            args=(strategy,), 
            daemon=True
        )
        self.prefetch_thread.start()
        self.logger.info(f"Prefetching mit Strategie '{strategy}' gestartet")
    
    def stop_prefetching(self):
        """Stoppt das Prefetching"""
        self.running = False
        if self.prefetch_thread:
            self.prefetch_thread.join(timeout=5.0)
        self.logger.info("Prefetching gestoppt")
    
    def _prefetch_loop(self, strategy: str):
        """Hauptschleife für das Prefetching"""
        while self.running:
            try:
                # Hole Prefetch-Request
                try:
                    prefetch_data = self.prefetch_queue.get(timeout=1.0)
                except:
                    continue
                
                # Führe Prefetching mit der gewählten Strategie durch
                prefetch_func = self.prefetch_strategies.get(strategy, self._smart_prefetch)
                prefetch_func(prefetch_data)
                
                # Markiere als erledigt
                self.prefetch_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Prefetching-Fehler: {e}")
                continue
    
    def _sequential_prefetch(self, prefetch_data: Dict[str, Any]):
        """Sequenzielle Prefetch-Strategie"""
        requests = prefetch_data.get('requests', [])
        
        for request in requests:
            if not self.running:
                break
            
            trade_id, asset, date, option_type, strike = request
            self.api_optimizer.submit_request(
                trade_id, asset, date, option_type, strike, priority=1
            )
            
            # Kurze Pause zwischen Requests
            time.sleep(0.1)
    
    def _priority_prefetch(self, prefetch_data: Dict[str, Any]):
        """Prioritätsbasierte Prefetch-Strategie"""
        requests = prefetch_data.get('requests', [])
        
        # Sortiere nach Priorität (z.B. nach Datum - neuere zuerst)
        sorted_requests = sorted(requests, key=lambda x: x[1], reverse=True)
        
        for request in sorted_requests:
            if not self.running:
                break
            
            trade_id, asset, date, option_type, strike = request
            priority = 2 if date >= datetime.now().strftime('%Y-%m-%d') else 1
            
            self.api_optimizer.submit_request(
                trade_id, asset, date, option_type, strike, priority=priority
            )
    
    def _smart_prefetch(self, prefetch_data: Dict[str, Any]):
        """Intelligente Prefetch-Strategie mit Batch-Processing"""
        requests = prefetch_data.get('requests', [])
        
        # Teile in Batches auf
        batch_size = 5
        for i in range(0, len(requests), batch_size):
            if not self.running:
                break
            
            batch = requests[i:i + batch_size]
            self.api_optimizer.submit_batch_requests(batch, priority=1)
            
            # Kurze Pause zwischen Batches
            time.sleep(0.05)
    
    def add_prefetch_request(self, requests: List[Tuple[str, str, str, str, int]]):
        """Fügt Prefetch-Requests hinzu"""
        prefetch_data = {'requests': requests}
        self.prefetch_queue.put(prefetch_data)

# Globale Instanzen
_api_optimizer = None
_prefetch_manager = None

def get_api_optimizer() -> APIOptimizer:
    """Gibt die globale API-Optimizer-Instanz zurück"""
    global _api_optimizer
    if _api_optimizer is None:
        _api_optimizer = APIOptimizer()
    return _api_optimizer

def get_prefetch_manager() -> PrefetchManager:
    """Gibt die globale Prefetch-Manager-Instanz zurück"""
    global _prefetch_manager
    if _prefetch_manager is None:
        _prefetch_manager = PrefetchManager(get_api_optimizer())
    return _prefetch_manager

def shutdown_api_services():
    """Beendet alle API-Services"""
    global _api_optimizer, _prefetch_manager
    
    if _prefetch_manager:
        _prefetch_manager.stop_prefetching()
        _prefetch_manager = None
    
    if _api_optimizer:
        _api_optimizer.shutdown()
        _api_optimizer = None
