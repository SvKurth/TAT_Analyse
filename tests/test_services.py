"""
Tests für Service-Layer des Trade Analyse Tools
"""

import unittest
import tempfile
import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Projektverzeichnis zum Python-Pfad hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.database_service import DatabaseService
from app.services.data_processing_service import DataProcessingService
from app.services.trade_data_service import TradeDataService


class TestDatabaseService(unittest.TestCase):
    """Tests für den DatabaseService."""
    
    def setUp(self):
        """Test-Setup."""
        self.config = {
            'database': {
                'file': 'test.db',
                'max_connections': 5
            }
        }
        self.db_service = DatabaseService(self.config)
        
        # Temporäre SQLite-Datenbank erstellen
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test.db')
        
        # Test-Datenbank mit Test-Tabelle erstellen
        self._create_test_database()
    
    def tearDown(self):
        """Test-Cleanup."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_database(self):
        """Erstellt eine Test-Datenbank mit Test-Tabelle."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Test-Tabelle erstellen
        cursor.execute('''
            CREATE TABLE Trade (
                TradeID INTEGER PRIMARY KEY,
                Symbol TEXT,
                DateOpened TEXT,
                Price REAL,
                Quantity INTEGER,
                Profit REAL
            )
        ''')
        
        # Test-Daten einfügen
        test_data = [
            (1, 'AAPL', '2023-01-01', 150.0, 100, 500.0),
            (2, 'GOOGL', '2023-01-02', 2800.0, 10, -200.0),
            (3, 'MSFT', '2023-01-03', 300.0, 50, 1000.0)
        ]
        
        cursor.executemany(
            'INSERT INTO Trade (TradeID, Symbol, DateOpened, Price, Quantity, Profit) VALUES (?, ?, ?, ?, ?, ?)',
            test_data
        )
        
        conn.commit()
        conn.close()
    
    def test_database_service_initialization(self):
        """Testet die Initialisierung des DatabaseService."""
        self.assertIsNotNone(self.db_service)
        self.assertEqual(self.db_service.config, self.config)
    
    def test_is_sqlite_file(self):
        """Testet die SQLite-Datei-Erkennung."""
        # Test mit echter SQLite-Datei
        self.assertTrue(self.db_service.is_sqlite_file(self.test_db_path))
        
        # Test mit nicht-SQLite-Datei
        temp_file = os.path.join(self.temp_dir, 'test.txt')
        with open(temp_file, 'w') as f:
            f.write('Keine SQLite-Datenbank')
        
        self.assertFalse(self.db_service.is_sqlite_file(temp_file))
    
    def test_get_table_info(self):
        """Testet das Abrufen von Tabelleninformationen."""
        db_info = self.db_service.get_table_info(self.test_db_path)
        
        self.assertIsInstance(db_info, dict)
        self.assertIn('tables', db_info)
        self.assertIn('Trade', db_info['tables'])
        self.assertEqual(db_info['total_tables'], 1)
        
        trade_table = db_info['tables']['Trade']
        self.assertIn('columns', trade_table)
        self.assertIn('row_count', trade_table)
        self.assertEqual(trade_table['row_count'], 3)
    
    def test_find_trade_table(self):
        """Testet das Finden der Trade-Tabelle."""
        trade_table = self.db_service.find_trade_table(self.test_db_path)
        self.assertEqual(trade_table, 'Trade')
    
    def test_load_table_data(self):
        """Testet das Laden von Tabellendaten."""
        data, primary_keys = self.db_service.load_table_data(self.test_db_path, 'Trade')
        
        self.assertIsInstance(data, pd.DataFrame)
        self.assertEqual(len(data), 3)
        self.assertEqual(len(primary_keys), 1)
        self.assertEqual(primary_keys[0], 'TradeID')
    
    def test_get_table_primary_keys(self):
        """Testet das Abrufen der Primärschlüssel."""
        primary_keys = self.db_service.get_table_primary_keys(self.test_db_path, 'Trade')
        self.assertEqual(primary_keys, ['TradeID'])
    
    def test_execute_query(self):
        """Testet die SQL-Abfrage-Ausführung."""
        query = "SELECT COUNT(*) as count FROM Trade WHERE Profit > 0"
        result = self.db_service.execute_query(self.test_db_path, query)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['count'], 2)


class TestDataProcessingService(unittest.TestCase):
    """Tests für den DataProcessingService."""
    
    def setUp(self):
        """Test-Setup."""
        self.config = {
            'analysis': {
                'default_currency': 'EUR',
                'decimal_places': 2
            }
        }
        self.processing_service = DataProcessingService(self.config)
        
        # Test-Daten erstellen
        self.test_data = pd.DataFrame({
            'TradeID': [1, 2, 3],
            'Symbol': ['AAPL', 'GOOGL', 'MSFT'],
            'DateOpened': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'Price': [150.0, 2800.0, 300.0],
            'Quantity': [100, 10, 50],
            'Profit': [500.0, -200.0, 1000.0]
        })
    
    def test_data_processing_service_initialization(self):
        """Testet die Initialisierung des DataProcessingService."""
        self.assertIsNotNone(self.processing_service)
        self.assertEqual(self.processing_service.config, self.config)
    
    def test_format_trade_data(self):
        """Testet die Formatierung von Trade-Daten."""
        primary_keys = ['TradeID']
        formatted_data = self.processing_service.format_trade_data(self.test_data, primary_keys)
        
        self.assertIsInstance(formatted_data, pd.DataFrame)
        self.assertEqual(len(formatted_data), 3)
        
        # Prüfe, ob Primärschlüssel als erste Spalte gesetzt wurde
        self.assertEqual(formatted_data.columns[0], 'TradeID')
    
    def test_get_data_info(self):
        """Testet das Abrufen von Dateninformationen."""
        info = self.processing_service.get_data_info(self.test_data)
        
        self.assertIsInstance(info, dict)
        self.assertIn('shape', info)
        self.assertIn('columns', info)
        self.assertIn('dtypes', info)
        self.assertEqual(info['shape'], (3, 6))
    
    def test_save_data_csv(self):
        """Testet das Speichern von Daten im CSV-Format."""
        temp_file = tempfile.mktemp(suffix='.csv')
        
        try:
            self.processing_service.save_data(self.test_data, temp_file, 'csv')
            self.assertTrue(os.path.exists(temp_file))
            
            # Prüfe, ob Datei gelesen werden kann
            loaded_data = pd.read_csv(temp_file)
            self.assertEqual(len(loaded_data), 3)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)


class TestTradeDataService(unittest.TestCase):
    """Tests für den TradeDataService."""
    
    def setUp(self):
        """Test-Setup."""
        self.config = {
            'database': {
                'file': 'test.db',
                'max_connections': 5
            },
            'analysis': {
                'default_currency': 'EUR',
                'decimal_places': 2
            }
        }
        self.trade_service = TradeDataService(self.config)
        
        # Temporäre SQLite-Datenbank erstellen
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test.db')
        
        # Test-Datenbank mit Test-Tabelle erstellen
        self._create_test_database()
    
    def tearDown(self):
        """Test-Cleanup."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_database(self):
        """Erstellt eine Test-Datenbank mit Test-Tabelle."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Test-Tabelle erstellen
        cursor.execute('''
            CREATE TABLE Trade (
                TradeID INTEGER PRIMARY KEY,
                Symbol TEXT,
                DateOpened TEXT,
                Price REAL,
                Quantity INTEGER,
                Profit REAL
            )
        ''')
        
        # Test-Daten einfügen
        test_data = [
            (1, 'AAPL', '2023-01-01', 150.0, 100, 500.0),
            (2, 'GOOGL', '2023-01-02', 2800.0, 10, -200.0),
            (3, 'MSFT', '2023-01-03', 300.0, 50, 1000.0)
        ]
        
        cursor.executemany(
            'INSERT INTO Trade (TradeID, Symbol, DateOpened, Price, Quantity, Profit) VALUES (?, ?, ?, ?, ?, ?)',
            test_data
        )
        
        conn.commit()
        conn.close()
    
    def test_trade_data_service_initialization(self):
        """Testet die Initialisierung des TradeDataService."""
        self.assertIsNotNone(self.trade_service)
        self.assertEqual(self.trade_service.config, self.config)
        self.assertIsNotNone(self.trade_service.database_service)
        self.assertIsNotNone(self.trade_service.data_processing_service)
    
    def test_is_sqlite_file(self):
        """Testet die SQLite-Datei-Erkennung."""
        self.assertTrue(self.trade_service.is_sqlite_file(self.test_db_path))
    
    def test_get_sqlite_table_info(self):
        """Testet das Abrufen von SQLite-Tabelleninformationen."""
        db_info = self.trade_service.get_sqlite_table_info(self.test_db_path)
        
        self.assertIsInstance(db_info, dict)
        self.assertIn('tables', db_info)
        self.assertIn('Trade', db_info['tables'])
    
    def test_load_trade_table(self):
        """Testet das Laden der Trade-Tabelle."""
        trade_data = self.trade_service.load_trade_table(self.test_db_path)
        
        self.assertIsInstance(trade_data, pd.DataFrame)
        self.assertEqual(len(trade_data), 3)
        self.assertIn('TradeID', trade_data.columns)
        self.assertIn('Symbol', trade_data.columns)
    
    def test_load_tradelog_sqlite(self):
        """Testet das Laden von Tradelog-Daten."""
        tradelog_data = self.trade_service.load_tradelog_sqlite(self.test_db_path)
        
        self.assertIsInstance(tradelog_data, pd.DataFrame)
        self.assertEqual(len(tradelog_data), 3)
    
    def test_load_csv_data(self):
        """Testet das Laden von CSV-Daten."""
        # Test-Daten erstellen
        test_data = pd.DataFrame({
            'TradeID': [1, 2, 3],
            'Symbol': ['AAPL', 'GOOGL', 'MSFT'],
            'DateOpened': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'Price': [150.0, 2800.0, 300.0],
            'Quantity': [100, 10, 50],
            'Profit': [500.0, -200.0, 1000.0]
        })
        
        # Test-CSV-Datei erstellen
        temp_csv = os.path.join(self.temp_dir, 'test.csv')
        test_data.to_csv(temp_csv, index=False)
        
        try:
            csv_data = self.trade_service.load_csv_data(temp_csv)
            self.assertIsInstance(csv_data, pd.DataFrame)
            self.assertEqual(len(csv_data), 3)
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)
    
    def test_get_data_info(self):
        """Testet das Abrufen von Dateninformationen."""
        # Test-Daten erstellen
        test_data = pd.DataFrame({
            'TradeID': [1, 2, 3],
            'Symbol': ['AAPL', 'GOOGL', 'MSFT'],
            'DateOpened': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'Price': [150.0, 2800.0, 300.0],
            'Quantity': [100, 10, 50],
            'Profit': [500.0, -200.0, 1000.0]
        })
        
        info = self.trade_service.get_data_info(test_data)
        
        self.assertIsInstance(info, dict)
        self.assertIn('shape', info)
        self.assertEqual(info['shape'], (3, 6))
    
    def test_get_table_primary_keys(self):
        """Testet das Abrufen der Tabellen-Primärschlüssel."""
        primary_keys = self.trade_service.get_table_primary_keys(self.test_db_path, 'Trade')
        self.assertEqual(primary_keys, ['TradeID'])


class TestServiceIntegration(unittest.TestCase):
    """Integrationstests für alle Services."""
    
    def setUp(self):
        """Test-Setup."""
        self.config = {
            'database': {
                'file': 'test.db',
                'max_connections': 5
            },
            'analysis': {
                'default_currency': 'EUR',
                'decimal_places': 2
            }
        }
        
        # Alle Services initialisieren
        self.trade_service = TradeDataService(self.config)
        self.db_service = self.trade_service.database_service
        self.processing_service = self.trade_service.data_processing_service
        
        # Temporäre SQLite-Datenbank erstellen
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test.db')
        
        # Test-Datenbank mit Test-Tabelle erstellen
        self._create_test_database()
    
    def tearDown(self):
        """Test-Cleanup."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_database(self):
        """Erstellt eine Test-Datenbank mit Test-Tabelle."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Test-Tabelle erstellen
        cursor.execute('''
            CREATE TABLE Trade (
                TradeID INTEGER PRIMARY KEY,
                Symbol TEXT,
                DateOpened TEXT,
                Price REAL,
                Quantity INTEGER,
                Profit REAL
            )
        ''')
        
        # Test-Daten einfügen
        test_data = [
            (1, 'AAPL', '2023-01-01', 150.0, 100, 500.0),
            (2, 'GOOGL', '2023-01-02', 2800.0, 10, -200.0),
            (3, 'MSFT', '2023-01-03', 300.0, 50, 1000.0)
        ]
        
        cursor.executemany(
            'INSERT INTO Trade (TradeID, Symbol, DateOpened, Price, Quantity, Profit) VALUES (?, ?, ?, ?, ?, ?)',
            test_data
        )
        
        conn.commit()
        conn.close()
    
    def test_full_workflow(self):
        """Testet den vollständigen Workflow aller Services."""
        # 1. SQLite-Datei erkennen
        self.assertTrue(self.trade_service.is_sqlite_file(self.test_db_path))
        
        # 2. Datenbankinformationen abrufen
        db_info = self.trade_service.get_sqlite_table_info(self.test_db_path)
        self.assertIn('Trade', db_info['tables'])
        
        # 3. Trade-Tabelle laden
        trade_data = self.trade_service.load_trade_table(self.test_db_path)
        self.assertEqual(len(trade_data), 3)
        
        # 4. Dateninformationen abrufen
        info = self.trade_service.get_data_info(trade_data)
        self.assertEqual(info['shape'], (3, 6))
        
        # 5. Primärschlüssel abrufen
        primary_keys = self.trade_service.get_table_primary_keys(self.test_db_path, 'Trade')
        self.assertEqual(primary_keys, ['TradeID'])
    
    def test_error_handling(self):
        """Testet die Fehlerbehandlung in allen Services."""
        # Test mit nicht existierender Datenbank
        with self.assertRaises(Exception):
            self.trade_service.load_trade_table('nonexistent.db')
        
        # Test mit nicht existierender Tabelle
        with self.assertRaises(Exception):
            self.db_service.load_table_data(self.test_db_path, 'NonexistentTable')


if __name__ == '__main__':
    # Test-Suite erstellen
    test_suite = unittest.TestSuite()
    
    # Tests hinzufügen
    test_suite.addTest(unittest.makeSuite(TestDatabaseService))
    test_suite.addTest(unittest.makeSuite(TestDataProcessingService))
    test_suite.addTest(unittest.makeSuite(TestTradeDataService))
    test_suite.addTest(unittest.makeSuite(TestServiceIntegration))
    
    # Tests ausführen
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit-Code setzen
    sys.exit(not result.wasSuccessful())
