"""
Trade_Analysis Source Package
Ein umfassendes Tool zur Analyse von Handelsdaten und Trading-Strategien.
"""

__version__ = "1.0.0"
__author__ = "Trade_Analysis Team"
__description__ = "Trading-Analyse und -Visualisierung"

from .data_loader import DataLoader
from .analysis import TradeAnalyzer
from .visualization import ChartGenerator
from .utils import setup_logging, load_config

__all__ = [
    "DataLoader",
    "TradeAnalyzer", 
    "ChartGenerator",
    "setup_logging",
    "load_config"
]
