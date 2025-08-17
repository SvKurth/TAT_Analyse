"""
Error Handler für das Trade Analyse Tool
Zentrale Verwaltung und Behandlung von Fehlern.
"""

import traceback
import sys
from typing import Optional, Callable, Any, Dict
from functools import wraps
from .logging_service import get_logger


class ErrorHandler:
    """Zentraler Error-Handler für alle Anwendungskomponenten."""
    
    def __init__(self):
        """Initialisiert den ErrorHandler."""
        self.logger = get_logger(__name__)
        self.error_callbacks = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Richtet Standard-Fehlerbehandler ein."""
        # Unbehandelte Exceptions abfangen
        sys.excepthook = self._handle_uncaught_exception
        
        # KeyboardInterrupt abfangen
        def signal_handler(signum, frame):
            self.logger.info("🛑 Anwendung wird durch Benutzer beendet")
            sys.exit(0)
        
        try:
            import signal
            signal.signal(signal.SIGINT, signal_handler)
        except (ImportError, AttributeError):
            # Windows-Unterstützung
            pass
    
    def _handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """Behandelt unbehandelte Exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # KeyboardInterrupt normal beenden
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Fehler loggen
        self.logger.error("💥 Unbehandelte Exception aufgetreten:")
        self.logger.error(f"Typ: {exc_type.__name__}")
        self.logger.error(f"Wert: {exc_value}")
        self.logger.error("Traceback:")
        
        # Traceback formatieren und loggen
        for line in traceback.format_exception(exc_type, exc_value, exc_traceback):
            self.logger.error(line.rstrip())
        
        # Benutzer informieren
        print(f"\n❌ Ein unerwarteter Fehler ist aufgetreten: {exc_value}")
        print("📝 Bitte überprüfen Sie die Logs für weitere Details.")
    
    def handle_error(self, error: Exception, context: str = "", 
                    user_message: str = "", log_level: str = "ERROR") -> Dict[str, Any]:
        """
        Behandelt einen Fehler und gibt Informationen zurück.
        
        Args:
            error: Der aufgetretene Fehler
            context: Kontext, in dem der Fehler aufgetreten ist
            user_message: Benutzerfreundliche Nachricht
            log_level: Log-Level für den Fehler
            
        Returns:
            Dictionary mit Fehlerinformationen
        """
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'user_message': user_message or str(error),
            'traceback': traceback.format_exc(),
            'handled': True
        }
        
        # Fehler loggen
        log_method = getattr(self.logger, log_level.lower())
        log_method(f"❌ Fehler in {context}: {error}")
        
        if log_level.upper() == "DEBUG":
            log_method(f"Traceback: {error_info['traceback']}")
        
        # Benutzerfreundliche Nachricht
        if user_message:
            print(f"❌ {user_message}")
        
        return error_info
    
    def safe_execute(self, func: Callable, *args, 
                    context: str = "", 
                    user_message: str = "",
                    default_return: Any = None,
                    **kwargs) -> Any:
        """
        Führt eine Funktion sicher aus und fängt Fehler ab.
        
        Args:
            func: Zu ausführende Funktion
            *args: Funktionsargumente
            context: Kontext für Fehlerbehandlung
            user_message: Benutzerfreundliche Fehlermeldung
            default_return: Rückgabewert bei Fehlern
            **kwargs: Funktions-Kwargs
            
        Returns:
            Funktionsergebnis oder default_return bei Fehlern
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_error(e, context, user_message)
            return default_return
    
    def register_error_callback(self, error_type: type, callback: Callable):
        """
        Registriert einen Callback für einen bestimmten Fehlertyp.
        
        Args:
            error_type: Typ des Fehlers
            callback: Funktion, die bei diesem Fehler aufgerufen wird
        """
        self.error_callbacks[error_type] = callback
    
    def retry_on_error(self, max_attempts: int = 3, 
                      delay: float = 1.0,
                      backoff_factor: float = 2.0,
                      exceptions: tuple = (Exception,)):
        """
        Decorator für Wiederholungsversuche bei Fehlern.
        
        Args:
            max_attempts: Maximale Anzahl Versuche
            delay: Verzögerung zwischen Versuchen in Sekunden
            backoff_factor: Faktor für exponentielle Verzögerung
            exceptions: Zu behandelnde Exception-Typen
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay
                
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        attempt_num = attempt + 1
                        
                        if attempt_num < max_attempts:
                            self.logger.warning(
                                f"⚠️ Versuch {attempt_num}/{max_attempts} fehlgeschlagen: {e}. "
                                f"Wiederholung in {current_delay:.1f}s..."
                            )
                            
                            import time
                            time.sleep(current_delay)
                            current_delay *= backoff_factor
                        else:
                            self.logger.error(
                                f"💥 Alle {max_attempts} Versuche fehlgeschlagen. "
                                f"Letzter Fehler: {e}"
                            )
                
                # Alle Versuche fehlgeschlagen
                raise last_exception
            
            return wrapper
        return decorator


# Globale Instanz
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """
    Gibt die globale ErrorHandler-Instanz zurück.
    
    Returns:
        ErrorHandler-Instanz
    """
    global _error_handler
    
    if _error_handler is None:
        _error_handler = ErrorHandler()
    
    return _error_handler


def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """
    Kurzform für sicheres Ausführen von Funktionen.
    
    Args:
        func: Zu ausführende Funktion
        *args: Funktionsargumente
        **kwargs: Funktions-Kwargs
        
    Returns:
        Funktionsergebnis oder None bei Fehlern
    """
    return get_error_handler().safe_execute(func, *args, **kwargs)


def retry_on_error(max_attempts: int = 3, delay: float = 1.0):
    """
    Kurzform für Retry-Decorator.
    
    Args:
        max_attempts: Maximale Anzahl Versuche
        delay: Verzögerung zwischen Versuchen
        
    Returns:
        Decorator-Funktion
    """
    return get_error_handler().retry_on_error(max_attempts, delay)
