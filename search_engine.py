#!/usr/bin/env python3
"""
Módulo de Busca Semântica
Responsável por realizar buscas semânticas e preparar resultados
"""

import pandas as pd
import time
import logging
from datetime import datetime
from typing import Tuple
from embeddings_engine import EmbeddingsEngine

logger = logging.getLogger(__name__)


class SearchEngine:
    """Motor de busca semântica"""
    
    def __init__(self, embeddings_engine: EmbeddingsEngine):
        """
        Inicializa o motor de busca
        
        Args:
            embeddings_engine: Instância do motor de embeddings
        """
        self.embeddings_engine = embeddings_engine
    
    def search(self, query: str, df: pd.DataFrame, top_k: int = 15) -> pd.DataFrame:
        """
        Realiza busca semântica usando índice HNSW
        
        Args:
            query: Texto da consulta
            df: DataFrame com os dados
            top_k: Número de resultados a retornar
            
        Returns:
            DataFrame com os resultados mais relevantes
        """
        logger.info(f"🔍 Buscando: '{query}'")
        
        # Gera embedding da query
        query_embedding = self.embeddings_engine.generate_query_embedding(query)
        
        # Busca no índice HNSW
        start_time = time.time()
        scores, indices = self.embeddings_engine.search(query_embedding, top_k)
        search_time = time.time() - start_time
        
        # Prepara resultados
        results = df.iloc[indices[0]].copy()
        results['Score_Similaridade'] = scores[0]
        results['Timestamp_Busca'] = datetime.now().isoformat()
        results['Query_Original'] = query
        
        # Reordena colunas para melhor visualização
        important_columns = [
            'Score_Similaridade',
            'Código do Item',
            'Descrição do Item',
            'Nome da Classe',
            'Nome do Grupo',
            'Código NCM',
            'Query_Original',
            'Timestamp_Busca'
        ]
        
        # Só inclui colunas que existem
        existing_columns = [
            col for col in important_columns if col in results.columns]
        other_columns = [
            col for col in results.columns if col not in existing_columns]
        final_columns = existing_columns + other_columns
        
        results = results[final_columns]
        
        logger.info(f"⚡ Busca HNSW realizada em {search_time*1000:.1f}ms")
        logger.info(f"📊 {len(results)} resultados encontrados")
        
        return results