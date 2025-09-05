#!/usr/bin/env python3
"""
Buscador Semântico Catmat v3.0 - Versão Modular
Autor: Eduardo Maia + IAs
Data: 2025

Pacote Python para busca semântica no Catálogo de Materiais (Catmat)
"""

from .buscador_catmat import BuscadorSemanticoCatmat
from .config_manager import ConfigManager
from .data_handler import DataHandler
from .embeddings_engine import EmbeddingsEngine
from .search_engine import SearchEngine
from .ai_recommender import AIRecommender
from .export_utils import ExportUtils
from .batch_processor import BatchProcessor

__version__ = "3.0.0"
__author__ = "Eduardo Maia + IAs"

__all__ = [
    'BuscadorSemanticoCatmat',
    'ConfigManager',
    'DataHandler', 
    'EmbeddingsEngine',
    'SearchEngine',
    'AIRecommender',
    'ExportUtils',
    'BatchProcessor'
]