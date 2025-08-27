"""
Module Loader für das Trade Analyse Tool
Lazy Loading von Dashboard-Modulen für bessere Performance.
"""

import importlib
import importlib.util
import sys
import time
from typing import Dict, Any, Optional, Callable, Type, List
from pathlib import Path
from app.core.logging_service import get_logger
from app.core.performance_monitor import monitor_function
import threading


class ModuleInfo:
    """Informationen über ein geladenes Modul."""
    
    def __init__(self, name: str, module_path: str):
        self.name = name
        self.module_path = module_path
        self.module: Optional[Any] = None
        self.load_time: Optional[float] = None
        self.load_duration: Optional[float] = None
        self.error: Optional[str] = None
        self.last_accessed: Optional[float] = None
        self.access_count: int = 0
    
    def mark_accessed(self) -> None:
        """Markiert das Modul als zugegriffen."""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def is_loaded(self) -> bool:
        """Prüft ob das Modul geladen ist."""
        return self.module is not None and self.error is None


class ModuleLoader:
    """
    Lazy Loading System für Dashboard-Module.
    
    Features:
    - Automatisches Laden von Modulen bei Bedarf
    - Caching geladener Module
    - Performance-Monitoring
    - Fehlerbehandlung
    - Modul-Lifecycle-Management
    """
    
    def __init__(self, modules_directory: str = "modules"):
        """
        Initialisiert den Module Loader.
        
        Args:
            modules_directory: Verzeichnis mit den Modulen
        """
        self.modules_directory = Path(modules_directory)
        self.logger = get_logger(__name__)
        
        # Geladene Module
        self._modules: Dict[str, ModuleInfo] = {}
        self._module_functions: Dict[str, Dict[str, Callable]] = {}
        
        # Konfiguration
        self._auto_reload = False
        self._max_cached_modules = 20
        
        # Initialisiere verfügbare Module
        self._discover_modules()
    
    def _discover_modules(self) -> None:
        """Entdeckt verfügbare Module im Verzeichnis."""
        try:
            if not self.modules_directory.exists():
                self.logger.warning(f"Modul-Verzeichnis {self.modules_directory} existiert nicht")
                return
            
            # Suche nach Python-Dateien
            for py_file in self.modules_directory.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                
                module_name = py_file.stem
                module_path = str(py_file)
                
                # Erstelle ModuleInfo
                module_info = ModuleInfo(module_name, module_path)
                self._modules[module_name] = module_info
                
                self.logger.debug(f"Modul entdeckt: {module_name} -> {module_path}")
            
            self.logger.info(f"{len(self._modules)} Module entdeckt")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Entdecken der Module: {e}")
    
    @monitor_function(slow_threshold=0.5)
    def load_module(self, module_name: str, force_reload: bool = False) -> Optional[Any]:
        """
        Lädt ein Modul.
        
        Args:
            module_name: Name des zu ladenden Moduls
            force_reload: Erzwingt das Neuladen des Moduls
            
        Returns:
            Geladenes Modul oder None bei Fehler
        """
        if module_name not in self._modules:
            self.logger.error(f"Modul '{module_name}' nicht gefunden")
            return None
        
        module_info = self._modules[module_name]
        
        # Prüfe ob Modul bereits geladen ist
        if module_info.is_loaded() and not force_reload:
            module_info.mark_accessed()
            return module_info.module
        
        # Lade Modul
        start_time = time.time()
        
        try:
            # Erstelle Modul-Spec
            spec = importlib.util.spec_from_file_location(
                module_name, 
                module_info.module_path
            )
            
            if spec is None or spec.loader is None:
                raise ImportError(f"Konnte Spec für Modul '{module_name}' nicht erstellen")
            
            # Lade Modul
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Aktualisiere ModuleInfo
            module_info.module = module
            module_info.load_time = time.time()
            module_info.load_duration = time.time() - start_time
            module_info.error = None
            module_info.mark_accessed()
            
            # Cache Module-Funktionen
            self._cache_module_functions(module_name, module)
            
            self.logger.info(f"Modul '{module_name}' erfolgreich geladen ({module_info.load_duration:.4f}s)")
            
            # Cleanup bei zu vielen gecachten Modulen
            self._cleanup_cache()
            
            return module
            
        except Exception as e:
            error_msg = str(e)
            module_info.error = error_msg
            module_info.load_duration = time.time() - start_time
            
            self.logger.error(f"Fehler beim Laden des Moduls '{module_name}': {error_msg}")
            return None
    
    def _cache_module_functions(self, module_name: str, module: Any) -> None:
        """Cached verfügbare Funktionen eines Moduls."""
        functions = {}
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr) and not attr_name.startswith("_"):
                functions[attr_name] = attr
        
        self._module_functions[module_name] = functions
        
        self.logger.debug(f"Modul '{module_name}': {len(functions)} Funktionen gecacht")
    
    def _cleanup_cache(self) -> None:
        """Entfernt alte Module aus dem Cache."""
        if len(self._modules) <= self._max_cached_modules:
            return
        
        # Sortiere Module nach letztem Zugriff
        sorted_modules = sorted(
            self._modules.items(),
            key=lambda x: x[1].last_accessed or 0
        )
        
        # Entferne die ältesten Module
        modules_to_remove = len(self._modules) - self._max_cached_modules
        
        for i in range(modules_to_remove):
            module_name, module_info = sorted_modules[i]
            
            if module_info.is_loaded():
                # Entlade Modul
                module_info.module = None
                module_info.load_time = None
                module_info.load_duration = None
                
                # Entferne aus Function-Cache
                if module_name in self._module_functions:
                    del self._module_functions[module_name]
                
                self.logger.debug(f"Modul '{module_name}' aus Cache entfernt")
    
    def get_module_function(
        self,
        module_name: str,
        function_name: str,
        auto_load: bool = True
    ) -> Optional[Callable]:
        """
        Gibt eine Funktion aus einem Modul zurück.
        
        Args:
            module_name: Name des Moduls
            function_name: Name der Funktion
            auto_load: Lädt das Modul automatisch falls nötig
            
        Returns:
            Gefundene Funktion oder None
        """
        # Prüfe ob Modul geladen ist
        if module_name not in self._modules:
            if not auto_load:
                return None
            
            # Lade Modul automatisch
            if not self.load_module(module_name):
                return None
        
        # Prüfe ob Funktion verfügbar ist
        if module_name not in self._module_functions:
            return None
        
        functions = self._module_functions[module_name]
        return functions.get(function_name)
    
    def call_module_function(
        self,
        module_name: str,
        function_name: str,
        *args,
        auto_load: bool = True,
        **kwargs
    ) -> Any:
        """
        Ruft eine Funktion aus einem Modul auf.
        
        Args:
            module_name: Name des Moduls
            function_name: Name der Funktion
            auto_load: Lädt das Modul automatisch falls nötig
            *args: Funktionsargumente
            **kwargs: Funktionskeyword-Argumente
            
        Returns:
            Rückgabewert der Funktion
            
        Raises:
            ValueError: Wenn Modul oder Funktion nicht gefunden werden
        """
        function = self.get_module_function(module_name, function_name, auto_load)
        
        if function is None:
            raise ValueError(f"Funktion '{function_name}' in Modul '{module_name}' nicht gefunden")
        
        # Markiere Modul als zugegriffen
        if module_name in self._modules:
            self._modules[module_name].mark_accessed()
        
        # Rufe Funktion auf
        return function(*args, **kwargs)
    
    def list_available_modules(self) -> List[str]:
        """Gibt eine Liste aller verfügbaren Module zurück."""
        return list(self._modules.keys())
    
    def list_loaded_modules(self) -> List[str]:
        """Gibt eine Liste aller geladenen Module zurück."""
        return [
            name for name, info in self._modules.items()
            if info.is_loaded()
        ]
    
    def get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        """Gibt Informationen über ein Modul zurück."""
        return self._modules.get(module_name)
    
    def get_all_module_info(self) -> Dict[str, ModuleInfo]:
        """Gibt Informationen über alle Module zurück."""
        return dict(self._modules)
    
    def reload_module(self, module_name: str) -> bool:
        """Lädt ein Modul neu."""
        if module_name not in self._modules:
            return False
        
        # Entferne altes Modul
        module_info = self._modules[module_name]
        module_info.module = None
        module_info.load_time = None
        module_info.load_duration = None
        module_info.error = None
        
        # Entferne aus Function-Cache
        if module_name in self._module_functions:
            del self._module_functions[module_name]
        
        # Lade Modul neu
        return self.load_module(module_name, force_reload=True) is not None
    
    def reload_all_modules(self) -> Dict[str, bool]:
        """Lädt alle Module neu."""
        results = {}
        
        for module_name in self._modules:
            results[module_name] = self.reload_module(module_name)
        
        return results
    
    def unload_module(self, module_name: str) -> bool:
        """Entlädt ein Modul."""
        if module_name not in self._modules:
            return False
        
        module_info = self._modules[module_name]
        
        # Entlade Modul
        module_info.module = None
        module_info.load_time = None
        module_info.load_duration = None
        module_info.error = None
        
        # Entferne aus Function-Cache
        if module_name in self._module_functions:
            del self._module_functions[module_name]
        
        self.logger.info(f"Modul '{module_name}' entladen")
        return True
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Gibt Cache-Statistiken zurück."""
        loaded_count = len(self.list_loaded_modules())
        total_count = len(self._modules)
        
        return {
            'total_modules': total_count,
            'loaded_modules': loaded_count,
            'cached_modules': len(self._module_functions),
            'cache_usage': loaded_count / max(total_count, 1),
            'max_cached_modules': self._max_cached_modules
        }
    
    def set_auto_reload(self, enabled: bool) -> None:
        """Aktiviert/Deaktiviert automatisches Neuladen."""
        self._auto_reload = enabled
        self.logger.info(f"Auto-Reload: {'aktiviert' if enabled else 'deaktiviert'}")
    
    def set_max_cached_modules(self, max_modules: int) -> None:
        """Setzt die maximale Anzahl gecachter Module."""
        if max_modules < 1:
            raise ValueError("max_modules muss mindestens 1 sein")
        
        self._max_cached_modules = max_modules
        
        # Führe sofortigen Cleanup durch
        self._cleanup_cache()
        
        self.logger.info(f"Maximale Anzahl gecachter Module auf {max_modules} gesetzt")


# Globale Module Loader Instanz
_module_loader = None
_module_loader_lock = threading.Lock()

def get_module_loader(modules_directory: str = "modules") -> ModuleLoader:
    """Gibt den globalen Module Loader zurück."""
    global _module_loader
    
    if _module_loader is None:
        with _module_loader_lock:
            if _module_loader is None:
                _module_loader = ModuleLoader(modules_directory)
    
    return _module_loader

def load_module(module_name: str, force_reload: bool = False) -> Optional[Any]:
    """Lädt ein Modul über den globalen Loader."""
    return get_module_loader().load_module(module_name, force_reload)

def get_module_function(
    module_name: str,
    function_name: str,
    auto_load: bool = True
) -> Optional[Callable]:
    """Gibt eine Funktion aus einem Modul zurück."""
    return get_module_loader().get_module_function(module_name, function_name, auto_load)

def call_module_function(
    module_name: str,
    function_name: str,
    *args,
    auto_load: bool = True,
    **kwargs
) -> Any:
    """Ruft eine Funktion aus einem Modul auf."""
    return get_module_loader().call_module_function(
        module_name, function_name, *args, auto_load=auto_load, **kwargs
    )
