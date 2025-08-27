"""
Service Registry für das Trade Analyse Tool
Zentrale Verwaltung aller Services mit Dependency Injection und Lifecycle Management.
"""

import threading
from typing import Dict, Any, Optional, Type, Callable
from contextlib import contextmanager
from app.core.logging_service import get_logger


class ServiceRegistry:
    """
    Zentrale Service-Registry für Dependency Injection und Service-Management.
    
    Implementiert das Singleton-Pattern und bietet Thread-Sicherheit.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        if ServiceRegistry._instance is not None:
            raise Exception("ServiceRegistry ist ein Singleton")
        
        self._services: Dict[str, Any] = {}
        self._service_factories: Dict[str, Callable] = {}
        self._service_configs: Dict[str, Dict[str, Any]] = {}
        self._logger = get_logger(__name__)
        
        ServiceRegistry._instance = self
    
    @classmethod
    def get_instance(cls) -> 'ServiceRegistry':
        """Gibt die einzige Instanz der ServiceRegistry zurück."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def register_service(self, name: str, service: Any, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Registriert einen Service direkt.
        
        Args:
            name: Name des Services
            service: Service-Instanz
            config: Optionale Konfiguration für den Service
        """
        with self._lock:
            self._services[name] = service
            if config:
                self._service_configs[name] = config
            self._logger.info(f"Service '{name}' direkt registriert")
    
    def register_factory(self, name: str, factory: Callable, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Registriert eine Service-Factory für Lazy Loading.
        
        Args:
            name: Name des Services
            factory: Factory-Funktion, die den Service erstellt
            config: Optionale Konfiguration für den Service
        """
        with self._lock:
            self._service_factories[name] = factory
            if config:
                self._service_configs[name] = config
            self._logger.info(f"Service-Factory '{name}' registriert")
    
    def get_service(self, name: str) -> Any:
        """
        Gibt einen Service zurück, erstellt ihn bei Bedarf.
        
        Args:
            name: Name des Services
            
        Returns:
            Service-Instanz
            
        Raises:
            KeyError: Wenn der Service nicht gefunden werden kann
        """
        # Prüfe ob Service bereits existiert
        if name in self._services:
            return self._services[name]
        
        # Prüfe ob Factory existiert
        if name in self._service_factories:
            with self._lock:
                # Double-check nach dem Lock
                if name not in self._services:
                    try:
                        config = self._service_configs.get(name, {})
                        service = self._service_factories[name](config)
                        self._services[name] = service
                        self._logger.info(f"Service '{name}' über Factory erstellt")
                    except Exception as e:
                        self._logger.error(f"Fehler beim Erstellen des Services '{name}': {e}")
                        raise
                return self._services[name]
        
        raise KeyError(f"Service '{name}' nicht gefunden")
    
    def has_service(self, name: str) -> bool:
        """Prüft ob ein Service existiert."""
        return name in self._services or name in self._service_factories
    
    def remove_service(self, name: str) -> None:
        """Entfernt einen Service aus der Registry."""
        with self._lock:
            if name in self._services:
                del self._services[name]
                self._logger.info(f"Service '{name}' entfernt")
            if name in self._service_factories:
                del self._service_factories[name]
                self._logger.info(f"Service-Factory '{name}' entfernt")
            if name in self._service_configs:
                del self._service_configs[name]
    
    def clear(self) -> None:
        """Löscht alle Services und Factories."""
        with self._lock:
            self._services.clear()
            self._service_factories.clear()
            self._service_configs.clear()
            self._logger.info("Alle Services gelöscht")
    
    def list_services(self) -> Dict[str, str]:
        """Gibt eine Liste aller registrierten Services zurück."""
        services = {}
        services.update({name: "direct" for name in self._services.keys()})
        services.update({name: "factory" for name in self._service_factories.keys()})
        return services
    
    @contextmanager
    def temporary_service(self, name: str, service: Any):
        """
        Kontextmanager für temporäre Services.
        
        Args:
            name: Name des temporären Services
            service: Service-Instanz
        """
        original_service = None
        try:
            if name in self._services:
                original_service = self._services[name]
            self.register_service(name, service)
            yield
        finally:
            if original_service is not None:
                self.register_service(name, original_service)
            else:
                self.remove_service(name)


# Globale Funktionen für einfache Verwendung
def get_service_registry() -> ServiceRegistry:
    """Gibt die globale Service-Registry zurück."""
    return ServiceRegistry.get_instance()


def register_service(name: str, service: Any, config: Optional[Dict[str, Any]] = None) -> None:
    """Registriert einen Service in der globalen Registry."""
    get_service_registry().register_service(name, service, config)


def register_factory(name: str, factory: Callable, config: Optional[Dict[str, Any]] = None) -> None:
    """Registriert eine Service-Factory in der globalen Registry."""
    get_service_registry().register_factory(name, factory, config)


def get_service(name: str) -> Any:
    """Gibt einen Service aus der globalen Registry zurück."""
    return get_service_registry().get_service(name)


def has_service(name: str) -> bool:
    """Prüft ob ein Service in der globalen Registry existiert."""
    return get_service_registry().has_service(name)
