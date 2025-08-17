"""
Tests für Core-Services des Trade Analyse Tools
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Projektverzeichnis zum Python-Pfad hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.logging_service import LoggingService, get_logging_service, get_logger
from app.core.error_handler import ErrorHandler, get_error_handler, safe_execute, retry_on_error
from app.core.config_service import ConfigService, get_config_service, get_config


class TestLoggingService(unittest.TestCase):
    """Tests für den LoggingService."""
    
    def setUp(self):
        """Test-Setup."""
        self.config = {
            'logging': {
                'level': 'INFO',
                'console': True,
                'file': None
            }
        }
        self.logging_service = LoggingService(self.config)
    
    def test_logging_service_initialization(self):
        """Testet die Initialisierung des LoggingService."""
        self.assertIsNotNone(self.logging_service)
        self.assertEqual(self.logging_service.config, self.config)
    
    def test_get_logger(self):
        """Testet die Logger-Erstellung."""
        logger = self.logging_service.get_logger(__name__)
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, __name__)
    
    def test_set_level(self):
        """Testet das Ändern des Log-Levels."""
        self.logging_service.set_level('DEBUG')
        # Prüfe, ob das Level geändert wurde
        self.logging_service.set_level('INFO')  # Zurück auf INFO
    
    def test_global_functions(self):
        """Testet die globalen Funktionen."""
        # Test get_logging_service
        global_service = get_logging_service(self.config)
        self.assertIsNotNone(global_service)
        
        # Test get_logger
        logger = get_logger(__name__)
        self.assertIsNotNone(logger)


class TestErrorHandler(unittest.TestCase):
    """Tests für den ErrorHandler."""
    
    def setUp(self):
        """Test-Setup."""
        self.error_handler = ErrorHandler()
    
    def test_error_handler_initialization(self):
        """Testet die Initialisierung des ErrorHandler."""
        self.assertIsNotNone(self.error_handler)
        self.assertIsNotNone(self.error_handler.logger)
    
    def test_handle_error(self):
        """Testet die Fehlerbehandlung."""
        test_error = ValueError("Test-Fehler")
        error_info = self.error_handler.handle_error(
            test_error, 
            "Test-Kontext", 
            "Test-Benutzernachricht"
        )
        
        self.assertIsNotNone(error_info)
        self.assertEqual(error_info['type'], 'ValueError')
        self.assertEqual(error_info['message'], 'Test-Fehler')
        self.assertEqual(error_info['context'], 'Test-Kontext')
        self.assertEqual(error_info['user_message'], 'Test-Benutzernachricht')
        self.assertTrue(error_info['handled'])
    
    def test_safe_execute_success(self):
        """Testet safe_execute bei erfolgreicher Ausführung."""
        def test_func(x, y):
            return x + y
        
        result = self.error_handler.safe_execute(
            test_func, 5, 3, 
            context="Test", 
            user_message="Test-Fehler"
        )
        
        self.assertEqual(result, 8)
    
    def test_safe_execute_failure(self):
        """Testet safe_execute bei Fehlern."""
        def test_func():
            raise ValueError("Test-Fehler")
        
        result = self.error_handler.safe_execute(
            test_func, 
            context="Test", 
            user_message="Test-Fehler",
            default_return="Fallback"
        )
        
        self.assertEqual(result, "Fallback")
    
    def test_retry_decorator(self):
        """Testet den Retry-Decorator."""
        attempt_count = 0
        
        @self.error_handler.retry_on_error(max_attempts=3, delay=0.1)
        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Temporärer Fehler")
            return "Erfolg"
        
        result = failing_function()
        self.assertEqual(result, "Erfolg")
        self.assertEqual(attempt_count, 3)
    
    def test_global_functions(self):
        """Testet die globalen Funktionen."""
        # Test get_error_handler
        global_handler = get_error_handler()
        self.assertIsNotNone(global_handler)
        
        # Test safe_execute
        def test_func():
            return "Test"
        
        result = safe_execute(test_func)
        self.assertEqual(result, "Test")


class TestConfigService(unittest.TestCase):
    """Tests für den ConfigService."""
    
    def setUp(self):
        """Test-Setup."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.yaml')
        
        # Test-Konfiguration erstellen
        test_config = {
            'database': {
                'file': 'test.db',
                'max_connections': 5
            },
            'logging': {
                'level': 'DEBUG',
                'console': True
            }
        }
        
        import yaml
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f)
    
    def tearDown(self):
        """Test-Cleanup."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_config_service_initialization(self):
        """Testet die Initialisierung des ConfigService."""
        config_service = ConfigService(self.config_path)
        self.assertIsNotNone(config_service)
        self.assertEqual(config_service.config_path, self.config_path)
    
    def test_config_loading(self):
        """Testet das Laden der Konfiguration."""
        config_service = ConfigService(self.config_path)
        
        # Prüfe geladene Werte
        self.assertEqual(config_service.get('database.file'), 'test.db')
        self.assertEqual(config_service.get('database.max_connections'), 5)
        self.assertEqual(config_service.get('logging.level'), 'DEBUG')
        self.assertTrue(config_service.get('logging.console'))
    
    def test_config_validation(self):
        """Testet die Konfigurationsvalidierung."""
        config_service = ConfigService(self.config_path)
        
        # Validiere Konfiguration
        try:
            config_service.config.validate()
            validation_successful = True
        except Exception:
            validation_successful = False
        
        self.assertTrue(validation_successful)
    
    def test_config_setting(self):
        """Testet das Setzen von Konfigurationswerten."""
        config_service = ConfigService(self.config_path)
        
        # Wert setzen
        config_service.set('database.file', 'new_test.db')
        self.assertEqual(config_service.get('database.file'), 'new_test.db')
    
    def test_config_summary(self):
        """Testet die Konfigurationszusammenfassung."""
        config_service = ConfigService(self.config_path)
        summary = config_service.get_config_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('database_file', summary)
        self.assertIn('log_level', summary)
    
    def test_global_functions(self):
        """Testet die globalen Funktionen."""
        # Test get_config_service
        global_config_service = get_config_service(self.config_path)
        self.assertIsNotNone(global_config_service)
        
        # Test get_config
        db_file = get_config('database.file', default='default.db')
        self.assertEqual(db_file, 'test.db')


class TestIntegration(unittest.TestCase):
    """Integrationstests für Core-Services."""
    
    def setUp(self):
        """Test-Setup."""
        self.config = {
            'logging': {
                'level': 'INFO',
                'console': True,
                'file': None
            },
            'database': {
                'file': 'test.db',
                'max_connections': 5
            }
        }
    
    def test_service_integration(self):
        """Testet die Integration aller Core-Services."""
        # Logging-Service initialisieren
        logging_service = get_logging_service(self.config)
        self.assertIsNotNone(logging_service)
        
        # Error-Handler initialisieren
        error_handler = get_error_handler()
        self.assertIsNotNone(error_handler)
        
        # Logger erstellen
        logger = get_logger(__name__)
        self.assertIsNotNone(logger)
        
        # Test-Log-Nachricht
        logger.info("Integrationstest erfolgreich")
        
        # Fehlerbehandlung testen
        def test_func():
            raise ValueError("Integrationstest-Fehler")
        
        result = safe_execute(
            test_func, 
            context="Integrationstest",
            user_message="Test-Fehler",
            default_return="Integrationstest-Erfolg"
        )
        
        self.assertEqual(result, "Integrationstest-Erfolg")


if __name__ == '__main__':
    # Test-Suite erstellen
    test_suite = unittest.TestSuite()
    
    # Tests hinzufügen
    test_suite.addTest(unittest.makeSuite(TestLoggingService))
    test_suite.addTest(unittest.makeSuite(TestErrorHandler))
    test_suite.addTest(unittest.makeSuite(TestConfigService))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Tests ausführen
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit-Code setzen
    sys.exit(not result.wasSuccessful())
